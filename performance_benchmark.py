#!/usr/bin/env python3
"""
Performance benchmark for directory scanning with large file trees.
"""

import time
import tempfile
import os
from pathlib import Path
from typing import List, Tuple
import psutil
import tracemalloc

from share_and_tell.scanner import scan_directory


def get_memory_usage() -> float:
    """Get current memory usage in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024


def create_test_directory(base_path: Path, num_dirs: int, files_per_dir: int, depth: int = 3) -> Path:
    """Create a test directory structure with specified parameters."""
    test_root = base_path / f"test_{num_dirs}dirs_{files_per_dir}files_depth{depth}"
    test_root.mkdir(exist_ok=True)

    def create_recursive(current_path: Path, current_depth: int):
        if current_depth >= depth:
            return

        # Create files in current directory
        for i in range(files_per_dir):
            (current_path / f"file_{i}.txt").write_text(f"content {i}")

        # Create subdirectories
        dirs_to_create = min(num_dirs, 10) if current_depth > 0 else num_dirs
        for i in range(dirs_to_create):
            sub_dir = current_path / f"subdir_{i}"
            sub_dir.mkdir(exist_ok=True)
            create_recursive(sub_dir, current_depth + 1)

    create_recursive(test_root, 0)
    return test_root


def benchmark_scan(test_root: Path, max_depth: int = 3, min_files: int = 1) -> Tuple[float, int, float, float]:
    """Benchmark directory scanning performance."""
    print(f"Starting scan of {test_root}")
    print(f"Max depth: {max_depth}, Min files: {min_files}")

    # Start memory tracing
    tracemalloc.start()
    start_time = time.time()
    start_memory = get_memory_usage()

    try:
        result = scan_directory(test_root, max_depth=max_depth, min_files=min_files)

        end_time = time.time()
        end_memory = get_memory_usage()
        current, peak = tracemalloc.get_traced_memory()

        scan_time = end_time - start_time
        memory_used = end_memory - start_memory
        peak_memory = peak / 1024 / 1024  # Convert to MB

        print(".2f")
        print(f"Folders found: {len(result.folders)}")
        print(f"Warnings: {len(result.warnings)}")
        print(".2f")
        print(".2f")

        return scan_time, len(result.folders), memory_used, peak_memory

    finally:
        tracemalloc.stop()


def run_performance_tests():
    """Run comprehensive performance tests."""
    print("=== Directory Scanning Performance Benchmark ===\n")

    with tempfile.TemporaryDirectory() as temp_dir:
        base_path = Path(temp_dir)

        # Test scenarios
        test_cases = [
            # (num_dirs, files_per_dir, depth, max_depth, description)
            (10, 100, 2, 3, "Small tree: 10 dirs, 100 files each, depth 2"),
            (50, 50, 3, 3, "Medium tree: 50 dirs, 50 files each, depth 3"),
            (100, 20, 3, 3, "Large tree: 100 dirs, 20 files each, depth 3"),
            (10, 1000, 2, 3, "High file count: 10 dirs, 1000 files each"),
        ]

        results = []

        for num_dirs, files_per_dir, depth, max_depth, description in test_cases:
            print(f"\n--- {description} ---")

            # Create test directory
            test_root = create_test_directory(base_path, num_dirs, files_per_dir, depth)

            # Count total files/directories created
            total_files = sum(1 for _ in test_root.rglob("*") if _.is_file())
            total_dirs = sum(1 for _ in test_root.rglob("*") if _.is_dir())

            print(f"Created {total_files} files in {total_dirs} directories")

            # Run benchmark
            scan_time, folders_found, memory_used, peak_memory = benchmark_scan(
                test_root, max_depth=max_depth, min_files=1
            )

            results.append({
                'description': description,
                'total_files': total_files,
                'total_dirs': total_dirs,
                'scan_time': scan_time,
                'folders_found': folders_found,
                'memory_used': memory_used,
                'peak_memory': peak_memory,
                'files_per_second': total_files / scan_time if scan_time > 0 else 0,
                'dirs_per_second': total_dirs / scan_time if scan_time > 0 else 0,
            })

        # Print summary
        print("\n=== PERFORMANCE SUMMARY ===")
        print("<60")
        print("-" * 60)

        for result in results:
            print("<60")


def analyze_bottlenecks():
    """Analyze potential performance bottlenecks in the scanner."""
    print("\n=== BOTTLENECK ANALYSIS ===")

    issues = [
        {
            'component': 'Directory listing',
            'issue': 'list(os.scandir()) loads all entries into memory',
            'impact': 'High memory usage for directories with millions of files',
            'solution': 'Process entries incrementally instead of loading all at once'
        },
        {
            'component': 'File counting',
            'issue': 'Separate iteration to count files after listing',
            'impact': 'Double iteration through directory entries',
            'solution': 'Count files during the initial listing pass'
        },
        {
            'component': 'Stack-based DFS',
            'issue': 'Stack can grow very large for deep/wide directory trees',
            'impact': 'Memory usage scales with directory depth and breadth',
            'solution': 'Consider iterative approach with size limits'
        },
        {
            'component': 'Final sorting',
            'issue': 'Sorts all folders at the end using string operations',
            'impact': 'O(n log n) complexity for millions of folders',
            'solution': 'Maintain sorted order during insertion or use more efficient sorting'
        },
        {
            'component': 'Path operations',
            'issue': 'Frequent Path.relative_to() and string operations',
            'impact': 'CPU overhead for path manipulation',
            'solution': 'Cache path components and minimize string operations'
        }
    ]

    for issue in issues:
        print(f"\n{issue['component']}:")
        print(f"  Issue: {issue['issue']}")
        print(f"  Impact: {issue['impact']}")
        print(f"  Solution: {issue['solution']}")


if __name__ == "__main__":
    run_performance_tests()
    analyze_bottlenecks()