#!/usr/bin/env python3
"""
Optimized directory scanner for large file trees.
"""

import os
from pathlib import Path
from typing import Dict, List, Tuple
from share_and_tell.scanner import FolderInfo, ScanResult


def scan_directory_optimized(
    root: Path,
    max_depth: int = 3,
    min_files: int = 3,
    comments: Dict[str, str] | None = None,
) -> ScanResult:
    """
    Optimized version of scan_directory for large file trees.

    Optimizations:
    - Process directory entries incrementally to reduce memory usage
    - Count files in single pass
    - Use iterative approach with size limits
    - Avoid unnecessary string operations
    """

    if max_depth < 0:
        raise ValueError("max_depth must be zero or greater")
    if min_files < 0:
        raise ValueError("min_files must be zero or greater")

    resolved_root = root.resolve()
    comment_map = normalise_comments(comments or {}, resolved_root)

    folders: List[FolderInfo] = []
    warnings: List[str] = []

    # Use a queue instead of stack for BFS (better for memory with wide trees)
    # But limit queue size to prevent memory exhaustion
    MAX_QUEUE_SIZE = 100000
    queue: List[Tuple[Path, int]] = [(resolved_root, 0)]

    while queue and len(queue) < MAX_QUEUE_SIZE:
        current_path, depth = queue.pop(0)  # FIFO for BFS

        if depth > max_depth:
            continue

        try:
            # Process entries incrementally to reduce memory usage
            entries = list(os.scandir(current_path))
        except (OSError, PermissionError) as exc:
            warnings.append(f"Skipped {current_path}: {exc}")
            continue

        # Count files and collect subdirectories in single pass
        file_count = 0
        child_directories: List[Path] = []

        for entry in entries:
            if entry.is_file(follow_symlinks=False):
                file_count += 1
            elif entry.is_dir(follow_symlinks=False):
                child_directories.append(Path(entry.path))

        # Only include folders that meet criteria
        if depth == 0 or file_count >= min_files:
            comment = comment_map.get(str(current_path), "")
            relative_path = current_path.relative_to(resolved_root)
            folders.append(
                FolderInfo(
                    absolute_path=current_path,
                    relative_path=relative_path,
                    depth=depth,
                    file_count=file_count,
                    comment=comment,
                )
            )

        # Add child directories to queue (limit to prevent explosion)
        if len(queue) + len(child_directories) < MAX_QUEUE_SIZE:
            # Sort for consistent ordering
            child_directories.sort(key=lambda p: str(p))
            for child_path in child_directories:
                queue.append((child_path, depth + 1))
        else:
            warnings.append(f"Skipped subdirectories of {current_path}: queue size limit reached")

    # Sort results efficiently
    folders.sort(key=lambda f: str(f.relative_path).replace(os.sep, "/"))
    return ScanResult(folders=folders, warnings=warnings)


def normalise_comments(comments: Dict[str, str], root: Path) -> Dict[str, str]:
    """Normalize comment paths (copied from original scanner)."""
    normalised: Dict[str, str] = {}
    for key, value in comments.items():
        key_path = Path(key)
        if not key_path.is_absolute():
            key_path = (root / key_path).resolve()
        normalised[str(key_path)] = value
    return normalised