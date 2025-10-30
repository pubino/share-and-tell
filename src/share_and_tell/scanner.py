from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


@dataclass
class FolderInfo:
    """Lightweight record for a discovered folder."""

    absolute_path: Path
    relative_path: Path
    depth: int
    file_count: int
    comment: str = ""

    def as_dict(self) -> Dict[str, str]:
        """Convert this record into a JSON-serialisable mapping."""
        return {
            "folder": str(self.relative_path).replace(os.sep, "/") or ".",
            "absolute_path": str(self.absolute_path),
            "depth": self.depth,
            "file_count": self.file_count,
            "comment": self.comment,
        }


@dataclass
class ScanResult:
    """Outcome of walking the file tree."""

    folders: List[FolderInfo]
    warnings: List[str]


def normalise_comments(comments: Dict[str, str], root: Path) -> Dict[str, str]:
    normalised: Dict[str, str] = {}
    for key, value in comments.items():
        key_path = Path(key)
        if not key_path.is_absolute():
            key_path = (root / key_path).resolve()
        normalised[str(key_path)] = value
    return normalised


def scan_directory(
    root: Path,
    max_depth: int = 3,
    min_files: int = 3,
    comments: Dict[str, str] | None = None,
) -> ScanResult:
    """Traverse *root* and return folders meeting the importance threshold."""

    if max_depth < 0:
        raise ValueError("max_depth must be zero or greater")
    if min_files < 0:
        raise ValueError("min_files must be zero or greater")

    resolved_root = root.resolve()
    comment_map = normalise_comments(comments or {}, resolved_root)

    folders: List[FolderInfo] = []
    warnings: List[str] = []

    stack: List[Tuple[Path, int]] = [(resolved_root, 0)]

    while stack:
        current_path, depth = stack.pop()
        if depth > max_depth:
            continue

        try:
            entries = list(os.scandir(current_path))
        except (OSError, PermissionError) as exc:
            warnings.append(f"Skipped {current_path}: {exc}")
            continue

        file_count = sum(1 for entry in entries if entry.is_file(follow_symlinks=False))
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

        child_directories: List[Path] = [
            Path(entry.path)
            for entry in entries
            if entry.is_dir(follow_symlinks=False)
        ]

        for child_path in reversed(sorted(child_directories, key=lambda item: str(item))):
            stack.append((child_path, depth + 1))

    folders.sort(key=lambda item: (item.depth, str(item.relative_path)))
    return ScanResult(folders=folders, warnings=warnings)
