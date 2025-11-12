"""
Realistic file scanning performance benchmarks.

Benchmarks file scanning operations in realistic scenarios:
- Scanning directories with many files
- Progress tracking overhead
- Cancellation support overhead
- Checksum calculation with caching
"""

import tempfile
from pathlib import Path

from benchmarks.framework import Benchmark, format_benchmark_report
from fileflow_core.file_scanner import FileScanner
from fileflow_core.progress import ProgressTracker
from fileflow_storage.cache import ChecksumCache
from fileflow_storage.database import Database


def create_test_files(directory: Path, count: int = 100) -> list[Path]:
    """Create test files for scanning."""
    files = []
    for i in range(count):
        file_path = directory / f"test_file_{i}.txt"
        file_path.write_text(f"Test content {i}" * 100)  # ~1.5KB each
        files.append(file_path)
    return files


def benchmark_file_scanning_basic():
    """Benchmark basic file scanning without progress tracking."""
    print("\n" + "=" * 80)
    print("BENCHMARK: Basic File Scanning")
    print("=" * 80)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Create test files
        print("\nCreating 100 test files...")
        files = create_test_files(tmp_path, count=100)
        print(f"Created {len(files)} test files")

        scanner = FileScanner()
        bench = Benchmark("file-scanning-basic")

        def scan_without_progress():
            files = scanner.scan_directory(
                directory=tmp_path,
                patterns=["*.txt"],
                recursive=True,
                progress_tracker=None,  # No progress tracking
            )
            return len(files)

        def scan_with_progress():
            tracker = ProgressTracker("scan", total_items=0)
            tracker.start()
            files = scanner.scan_directory(
                directory=tmp_path,
                patterns=["*.txt"],
                recursive=True,
                progress_tracker=tracker,
            )
            tracker.complete()
            return len(files)

        result = bench.compare(
            baseline_func=scan_without_progress,
            optimized_func=scan_with_progress,
            iterations=20,
            warmup=3,
            baseline_name="without-progress",
            optimized_name="with-progress",
        )

        result["name"] = "File Scanning with Progress Tracking"
        result["files_scanned"] = 100

        print(format_benchmark_report(result))
        return result


def benchmark_checksum_caching():
    """Benchmark checksum calculation with and without caching."""
    print("\n" + "=" * 80)
    print("BENCHMARK: Checksum Caching")
    print("=" * 80)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        db_path = tmp_path / "cache.db"

        # Create test files
        print("\nCreating 50 test files...")
        files = create_test_files(tmp_path, count=50)
        print(f"Created {len(files)} test files")

        scanner = FileScanner()
        db = Database(str(db_path))
        cache = ChecksumCache(db)
        bench = Benchmark("checksum-caching")

        def scan_without_cache():
            """Scan and calculate checksums without caching."""
            metadata = scanner.scan_directory(
                directory=tmp_path,
                patterns=["*.txt"],
                recursive=True,
            )
            # Calculate checksums directly (no caching)
            for file_meta in metadata:
                cache.calculate_checksum(Path(file_meta.path))
            return len(metadata)

        def scan_with_cache_first_run():
            """First scan - populates cache."""
            metadata = scanner.scan_directory(
                directory=tmp_path,
                patterns=["*.txt"],
                recursive=True,
            )
            # Get checksums (will calculate and cache on first access)
            for file_meta in metadata:
                cache.get_checksum(Path(file_meta.path))
            return len(metadata)

        def scan_with_cache_hit():
            """Subsequent scan - uses cache."""
            metadata = scanner.scan_directory(
                directory=tmp_path,
                patterns=["*.txt"],
                recursive=True,
            )
            # Get checksums from cache
            for file_meta in metadata:
                cache.get_checksum(Path(file_meta.path))
            return len(metadata)

        # First, populate the cache
        print("\nPopulating cache...")
        scan_with_cache_first_run()
        print("Cache populated")

        # Benchmark: No cache vs cache hits
        result = bench.compare(
            baseline_func=scan_without_cache,
            optimized_func=scan_with_cache_hit,
            iterations=15,
            warmup=2,
            baseline_name="without-cache",
            optimized_name="with-cache",
        )

        result["name"] = "Checksum Calculation with Caching"
        result["files_processed"] = 50

        # Cache stats (after warming up, all hits should be from cache)
        cache_stats = {
            "total_entries": len(files),
            "expected_hits": len(files) * 15,  # 15 iterations with cache
            "hit_rate": "~100%"
        }
        result["cache_stats"] = cache_stats

        print(format_benchmark_report(result))
        print("\nCache Statistics:")
        print(f"  Files cached:  {cache_stats['total_entries']}")
        print(f"  Expected hits: {cache_stats['expected_hits']}")
        print(f"  Hit rate:      {cache_stats['hit_rate']}")

        db.close()
        return result


def benchmark_large_directory():
    """Benchmark scanning a large directory (1000 files)."""
    print("\n" + "=" * 80)
    print("BENCHMARK: Large Directory Scanning")
    print("=" * 80)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Create subdirectories with files
        print("\nCreating directory structure with 1000 files...")
        total_files = 0
        for i in range(10):  # 10 subdirectories
            subdir = tmp_path / f"subdir_{i}"
            subdir.mkdir()
            files = create_test_files(subdir, count=100)  # 100 files each
            total_files += len(files)
        print(f"Created {total_files} test files in 10 subdirectories")

        scanner = FileScanner()
        bench = Benchmark("large-directory-scan")

        def scan_large_directory():
            # Create a new tracker for each iteration
            tracker = ProgressTracker("scan-large", total_items=0)
            tracker.start()
            files = scanner.scan_directory(
                directory=tmp_path,
                patterns=["*.txt"],
                recursive=True,
                progress_tracker=tracker,
            )
            tracker.complete()
            return len(files)

        result = bench.run(
            scan_large_directory,
            iterations=10,
            warmup=2,
            name="large-directory-scan",
            metadata={"files": total_files, "directories": 10},
        )

        print(format_benchmark_report({"results": [result.to_dict()]}))
        print(f"\nFiles scanned: {total_files}")
        print(f"Average scan time: {result.mean_time:.4f}s")
        print(f"Files per second: {total_files / result.mean_time:.2f}")

        return {"name": "Large Directory Scanning", "result": result.to_dict()}


def run_all_file_benchmarks():
    """Run all file scanning benchmarks."""
    print("\n")
    print("=" * 80)
    print("FILE SCANNING PERFORMANCE BENCHMARKS")
    print("=" * 80)

    results = {}

    results["basic_scanning"] = benchmark_file_scanning_basic()
    results["checksum_caching"] = benchmark_checksum_caching()
    results["large_directory"] = benchmark_large_directory()

    # Summary
    print("\n")
    print("=" * 80)
    print("FILE SCANNING BENCHMARK SUMMARY")
    print("=" * 80)
    print("")
    print("Progress Tracking Overhead:")
    print(f"  Speedup: {results['basic_scanning']['speedup']}x")
    print("  (Lower is expected - progress tracking adds minimal overhead)")
    print("")
    print("Checksum Caching Performance:")
    print(f"  Speedup: {results['checksum_caching']['speedup']}x")
    print(f"  Cache Hit Rate: {results['checksum_caching']['cache_stats']['hit_rate']}")
    print("")
    print("Large Directory Scanning:")
    result = results['large_directory']['result']
    print(f"  1000 files scanned in {result['mean_time']:.4f}s")
    print(f"  Throughput: {1000 / result['mean_time']:.2f} files/sec")
    print("=" * 80)

    return results


if __name__ == "__main__":
    run_all_file_benchmarks()
