"""
Cancellable and retry-enabled directory scanner for robust scanning of large filesystems.
"""

import os
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass
import threading

from .scanner import FolderInfo, ScanResult, normalise_comments


@dataclass
class ScanProgress:
    """Progress information for directory scanning."""
    folders_processed: int = 0
    directories_scanned: int = 0
    total_files_found: int = 0
    current_path: Optional[Path] = None
    warnings_count: int = 0
    retry_count: int = 0


@dataclass
class ScanConfig:
    """Configuration for directory scanning."""
    max_depth: int = 3
    min_files: int = 3
    max_retries: int = 3
    retry_delay: float = 0.1  # seconds
    batch_size: int = 1000  # Process directories in batches


class ScanCancelledException(Exception):
    """Exception raised when a scan is cancelled."""
    pass


class CancellableDirectoryScanner:
    """
    Directory scanner with retry and cancellation support.

    Features:
    - Cancellation support via threading.Event
    - Retry logic for transient failures
    - Progress tracking
    - Memory-efficient batch processing
    """

    def __init__(self, config: Optional[ScanConfig] = None):
        self.config = config or ScanConfig()
        self._cancel_event = threading.Event()
        self._progress = ScanProgress()
        self._progress_callback: Optional[Callable[[ScanProgress], None]] = None

    def cancel(self):
        """Cancel the current scan operation."""
        self._cancel_event.set()

    def is_cancelled(self) -> bool:
        """Check if the scan has been cancelled."""
        return self._cancel_event.is_set()

    def set_progress_callback(self, callback: Callable[[ScanProgress], None]):
        """Set a callback function to receive progress updates."""
        self._progress_callback = callback

    def _check_cancelled(self):
        """Check if scan is cancelled and raise exception if so."""
        if self.is_cancelled():
            raise ScanCancelledException("Scan was cancelled by user")

    def _retry_operation(self, operation, *args, **kwargs):
        """Execute an operation with retry logic."""
        last_exception = None

        for attempt in range(self.config.max_retries + 1):
            try:
                self._check_cancelled()
                return operation(*args, **kwargs)
            except (OSError, PermissionError) as e:
                last_exception = e
                if attempt < self.config.max_retries:
                    self._progress.retry_count += 1
                    time.sleep(self.config.retry_delay * (2 ** attempt))  # Exponential backoff
                    continue
                else:
                    # Final attempt failed
                    raise e

        # This should never be reached, but just in case
        raise last_exception

    def _scan_directory_batch(self, directories: List[Tuple[Path, int]],
                            resolved_root: Path, comment_map: Dict[str, str],
                            folders: List[FolderInfo], warnings: List[str]) -> List[Tuple[Path, int]]:
        """Scan a batch of directories and return new directories to process."""
        new_directories: List[Tuple[Path, int]] = []

        for current_path, depth in directories:
            self._check_cancelled()
            self._progress.current_path = current_path

            try:
                # Retry directory access
                entries = self._retry_operation(list, os.scandir(current_path))
            except (OSError, PermissionError) as exc:
                warnings.append(f"Skipped {current_path}: {exc}")
                self._progress.warnings_count += 1
                continue

            self._progress.directories_scanned += 1

            # Count files in single pass
            file_count = 0
            child_directories: List[Path] = []

            for entry in entries:
                if entry.is_file(follow_symlinks=False):
                    file_count += 1
                elif entry.is_dir(follow_symlinks=False):
                    child_directories.append(Path(entry.path))

            self._progress.total_files_found += file_count

            # Include folder if it meets criteria
            if depth == 0 or file_count >= self.config.min_files:
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
                self._progress.folders_processed += 1

            # Add child directories if not exceeding max depth
            if depth < self.config.max_depth:
                # Sort for consistent ordering
                child_directories.sort(key=lambda p: str(p))
                for child_path in child_directories:
                    new_directories.append((child_path, depth + 1))

            # Update progress callback
            if self._progress_callback:
                self._progress_callback(self._progress)

        return new_directories

    def scan_directory(
        self,
        root: Path,
        comments: Optional[Dict[str, str]] = None,
    ) -> ScanResult:
        """
        Scan directory with retry and cancellation support.

        Args:
            root: Root directory to scan
            comments: Optional comment mapping

        Returns:
            ScanResult with folders and warnings

        Raises:
            ScanCancelledException: If scan is cancelled
        """
        if self.config.max_depth < 0:
            raise ValueError("max_depth must be zero or greater")
        if self.config.min_files < 0:
            raise ValueError("min_files must be zero or greater")

        # Reset state
        self._cancel_event.clear()
        self._progress = ScanProgress()

        resolved_root = root.resolve()
        comment_map = normalise_comments(comments or {}, resolved_root)

        folders: List[FolderInfo] = []
        warnings: List[str] = []

        # Start with root directory
        pending_directories: List[Tuple[Path, int]] = [(resolved_root, 0)]

        try:
            while pending_directories:
                self._check_cancelled()

                # Process directories in batches
                batch_size = min(self.config.batch_size, len(pending_directories))
                current_batch = pending_directories[:batch_size]
                pending_directories = pending_directories[batch_size:]

                # Scan current batch and get new directories
                new_directories = self._scan_directory_batch(
                    current_batch, resolved_root, comment_map, folders, warnings
                )

                # Add new directories to pending list
                pending_directories.extend(new_directories)

        except ScanCancelledException:
            # Clean up partial results
            folders.clear()
            warnings.append("Scan was cancelled - partial results discarded")
            raise

        # Sort final results
        def _sort_key(info: FolderInfo) -> str:
            normalised = str(info.relative_path).replace(os.sep, "/")
            return normalised or "."

        folders.sort(key=_sort_key)
        return ScanResult(folders=folders, warnings=warnings)

    def get_progress(self) -> ScanProgress:
        """Get current scan progress."""
        return self._progress.copy()


def scan_directory_with_retry(
    root: Path,
    max_depth: int = 3,
    min_files: int = 3,
    comments: Optional[Dict[str, str]] = None,
    max_retries: int = 3,
    progress_callback: Optional[Callable[[ScanProgress], None]] = None,
) -> ScanResult:
    """
    Convenience function for scanning with retry support.

    Args:
        root: Root directory to scan
        max_depth: Maximum directory depth to scan
        min_files: Minimum files required for folder inclusion
        comments: Optional comment mapping
        max_retries: Maximum retry attempts for failed operations
        progress_callback: Optional callback for progress updates

    Returns:
        ScanResult with folders and warnings
    """
    config = ScanConfig(
        max_depth=max_depth,
        min_files=min_files,
        max_retries=max_retries,
    )

    scanner = CancellableDirectoryScanner(config)
    if progress_callback:
        scanner.set_progress_callback(progress_callback)

    return scanner.scan_directory(root, comments)