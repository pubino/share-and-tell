#!/usr/bin/env python3
"""
Focused performance test for large directory trees.
"""

import time
import tempfile
import os
from pathlib import Path
from typing import Callable
import psutil

from share_and_tell.scanner import scan_directory
from share_and_tell.scanner_optimized import scan_directory_optimized


def get_memory_usage() -> float:
    """Get current memory usage in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024


def create_large_test_directory(base_path: Path, target_files: int) -> Path:
    """Create a test directory with approximately target_files total files."""
    test_root = base_path / f"large_test_{target_files}_files"
    test_root.mkdir(exist_ok=True)

    files_created = 0
    dirs_created = 1  # root directory

    def create_recursive(current_path: Path, remaining_files: int, depth: int = 0):
        nonlocal files_created, dirs_created

        if remaining_files <= 0 or depth > 4:  # Limit depth
            return

        # Create some files in current directory
        files_in_dir = min(remaining_files, max(1, remaining_files // 20))
        for i in range(files_in_dir):
            (current_path / f"file_{files_created}.txt").write_text(f"content {files_created}")
            files_created += 1
            remaining_files -= 1

        # Create subdirectories
        if remaining_files > 0 and depth < 4:
            subdirs = min(5, max(1, remaining_files // 1000))  # Balance breadth vs depth
            for i in range(subdirs):
                if remaining_files <= 0:
                    break
                sub_dir = current_path / f"dir_{dirs_created}"
                sub_dir.mkdir(exist_ok=True)
                dirs_created += 1
                create_recursive(sub_dir, remaining_files // subdirs, depth + 1)

    create_recursive(test_root, target_files)
    return test_root


def benchmark_scanner(
    scanner_func: Callable,
    test_root: Path,
    name: str,
    max_depth: int = 3,
    min_files: int = 1
) -> dict:
    """Benchmark a scanner function."""
    print(f"\n--- Testing {name} ---")

    start_time = time.time()
    start_memory = get_memory_usage()

    try:
        result = scanner_func(test_root, max_depth=max_depth, min_files=min_files)

        end_time = time.time()
        end_memory = get_memory_usage()

        scan_time = end_time - start_time
        memory_used = end_memory - start_memory

        print(".2f")
        print(f"Folders found: {len(result.folders)}")
        print(f"Warnings: {len(result.warnings)}")
        print(".2f")

        return {
            'name': name,
            'scan_time': scan_time,
            'folders_found': len(result.folders),
            'warnings': len(result.warnings),
            'memory_used': memory_used,
            'success': True
        }

    except Exception as e:
        end_time = time.time()
        scan_time = end_time - start_time
        print(f"FAILED after {scan_time:.2f}s: {e}")

        return {
            'name': name,
            'scan_time': scan_time,
            'folders_found': 0,
            'warnings': 0,
            'memory_used': 0,
            'success': False,
            'error': str(e)
        }


def run_large_scale_tests():
    """Run performance tests on large directory structures."""
    print("=== Large-Scale Directory Scanning Performance Test ===\n")

    with tempfile.TemporaryDirectory() as temp_dir:
        base_path = Path(temp_dir)

        # Test with increasingly large directory structures
        test_sizes = [10000, 50000, 100000]  # Target file counts

        scanners = [
            (scan_directory, "Original Scanner"),
            (scan_directory_optimized, "Optimized Scanner"),
        ]

        all_results = []

        for target_files in test_sizes:
            print(f"\n{'='*60}")
            print(f"TESTING WITH ~{target_files} FILES")
            print(f"{'='*60}")

            # Create test directory
            test_root = create_large_test_directory(base_path, target_files)

            # Count actual files created
            actual_files = sum(1 for _ in test_root.rglob("*") if _.is_file())
            actual_dirs = sum(1 for _ in test_root.rglob("*") if _.is_dir())

            print(f"Created {actual_files} files in {actual_dirs} directories")

            test_results = []

            # Test each scanner
            for scanner_func, name in scanners:
                result = benchmark_scanner(scanner_func, test_root, name)
                result['target_files'] = target_files
                result['actual_files'] = actual_files
                result['actual_dirs'] = actual_dirs
                test_results.append(result)

            all_results.extend(test_results)

            # Compare results
            if len(test_results) == 2:
                orig = test_results[0]
                opt = test_results[1]

                if orig['success'] and opt['success']:
                    time_ratio = orig['scan_time'] / opt['scan_time'] if opt['scan_time'] > 0 else float('inf')
                    print(".2f")
                    print(f"  Same results: {orig['folders_found'] == opt['folders_found']}")

        # Summary
        print(f"\n{'='*60}")
        print("PERFORMANCE SUMMARY")
        print(f"{'='*60}")

        print("<8")
        print("-" * 60)

        for result in all_results:
            status = "✓" if result['success'] else "✗"
            print("<8")


if __name__ == "__main__":
    run_large_scale_tests()