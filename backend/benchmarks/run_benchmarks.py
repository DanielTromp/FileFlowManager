"""
Comprehensive performance benchmarks for FileFlow Manager.

Benchmarks the performance improvements from infrastructure integration:
- Database operations with connection pooling
- Cache effectiveness (LRU cache, query cache)
- Rule engine with destination caching
- File operations with retry logic
"""

import json
import sqlite3
import tempfile
import time
from pathlib import Path

from benchmarks.framework import Benchmark, format_benchmark_report
from fileflow_core.cache import ConnectionPool, LRUCache, QueryCache
from fileflow_core.models import Rule
from fileflow_core.rule_engine import RuleEngine
from fileflow_storage.cache import ChecksumCache
from fileflow_storage.database import Database


def benchmark_database_operations():
    """Benchmark database operations with and without connection pooling."""
    print("\n" + "=" * 80)
    print("BENCHMARK: Database Operations")
    print("=" * 80)

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = Path(tmp.name)

    try:
        # Create schema
        conn = sqlite3.connect(str(db_path))
        conn.execute(
            "CREATE TABLE test_table (id INTEGER PRIMARY KEY, data TEXT, value INTEGER)"
        )
        conn.commit()
        conn.close()

        # Benchmark 1: Single connection vs connection pool
        bench = Benchmark("database-connection-overhead")

        def single_connection_inserts():
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            for i in range(100):
                cursor.execute(
                    "INSERT INTO test_table (data, value) VALUES (?, ?)",
                    (f"test{i}", i),
                )
            conn.commit()
            conn.close()
            # Clean up
            conn = sqlite3.connect(str(db_path))
            conn.execute("DELETE FROM test_table")
            conn.commit()
            conn.close()

        def pooled_connection_inserts():
            pool = ConnectionPool(db_path, pool_size=5)
            with pool.get_connection() as conn:
                cursor = conn.cursor()
                for i in range(100):
                    cursor.execute(
                        "INSERT INTO test_table (data, value) VALUES (?, ?)",
                        (f"test{i}", i),
                    )
                conn.commit()
            # Clean up
            with pool.get_connection() as conn:
                conn.execute("DELETE FROM test_table")
                conn.commit()
            pool.close_all()

        result = bench.compare(
            baseline_func=single_connection_inserts,
            optimized_func=pooled_connection_inserts,
            iterations=50,
            warmup=5,
            baseline_name="single-connection",
            optimized_name="connection-pool",
        )

        result["name"] = "Database Connection Overhead"
        print(format_benchmark_report(result))

        return result

    finally:
        db_path.unlink()


def benchmark_lru_cache():
    """Benchmark LRU cache performance."""
    print("\n" + "=" * 80)
    print("BENCHMARK: LRU Cache Performance")
    print("=" * 80)

    bench = Benchmark("lru-cache")

    # Prepare test data
    test_data = {f"key{i}": f"value{i}" for i in range(1000)}

    def without_cache():
        # Simulate repeated lookups in a dict
        lookup_count = 0
        for _ in range(100):
            for key in list(test_data.keys())[:50]:  # Access first 50 repeatedly
                _ = test_data.get(key)
                lookup_count += 1
        return lookup_count

    def with_cache():
        cache = LRUCache(capacity=100)
        # Pre-populate cache
        for key, value in list(test_data.items())[:50]:
            cache.set(key, value)

        lookup_count = 0
        hits = 0
        for _ in range(100):
            for key in list(test_data.keys())[:50]:
                result = cache.get(key)
                if result is not None:
                    hits += 1
                lookup_count += 1
        return lookup_count, hits

    # Run benchmarks
    baseline_result = bench.run(
        without_cache,
        iterations=100,
        warmup=10,
        name="without-cache",
        metadata={"approach": "direct dict access"},
    )

    optimized_result = bench.run(
        with_cache,
        iterations=100,
        warmup=10,
        name="with-lru-cache",
        metadata={"approach": "LRU cache", "capacity": 100},
    )

    # Calculate speedup
    speedup = baseline_result.mean_time / optimized_result.mean_time
    improvement_pct = ((speedup - 1.0) * 100) if speedup > 1.0 else 0.0

    # Get cache stats
    cache = LRUCache(capacity=100)
    for key, value in list(test_data.items())[:50]:
        cache.set(key, value)
    for _ in range(100):
        for key in list(test_data.keys())[:50]:
            cache.get(key)

    stats = cache.get_stats()

    result = {
        "name": "LRU Cache Performance",
        "baseline": baseline_result.to_dict(),
        "optimized": optimized_result.to_dict(),
        "speedup": round(speedup, 2),
        "improvement_percent": round(improvement_pct, 2),
        "cache_stats": stats,
    }

    print(format_benchmark_report(result))
    print(f"\nCache Statistics:")
    print(f"  Hit rate: {stats['hit_rate']}%")
    print(f"  Hits:     {stats['hits']}")
    print(f"  Misses:   {stats['misses']}")

    return result


def benchmark_query_cache():
    """Benchmark query result caching."""
    print("\n" + "=" * 80)
    print("BENCHMARK: Query Cache Performance")
    print("=" * 80)

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = Path(tmp.name)

    try:
        # Setup database
        pool = ConnectionPool(db_path, pool_size=3)

        with pool.get_connection() as conn:
            conn.execute(
                "CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT, price REAL)"
            )
            for i in range(1000):
                conn.execute(
                    "INSERT INTO products VALUES (?, ?, ?)",
                    (i, f"Product {i}", float(i * 10)),
                )
            conn.commit()

        bench = Benchmark("query-cache")
        cache = QueryCache()

        query = "SELECT * FROM products WHERE price > ? AND price < ?"
        params_list = [(100.0, 500.0), (200.0, 600.0), (300.0, 700.0)]

        def without_cache():
            count = 0
            for _ in range(50):
                for params in params_list:
                    with pool.get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute(query, params)
                        _ = cursor.fetchall()
                        count += 1
            return count

        def with_cache():
            count = 0
            for _ in range(50):
                for params in params_list:
                    # Check cache first
                    result = cache.get(query, params)
                    if result is None:
                        # Cache miss - execute query
                        with pool.get_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute(query, params)
                            result = cursor.fetchall()
                        cache.set(query, params, result)
                    count += 1
            return count

        result = bench.compare(
            baseline_func=without_cache,
            optimized_func=with_cache,
            iterations=20,
            warmup=5,
            baseline_name="without-query-cache",
            optimized_name="with-query-cache",
        )

        result["name"] = "Query Cache Performance"
        result["cache_stats"] = cache.get_stats()

        print(format_benchmark_report(result))
        print(f"\nQuery Cache Statistics:")
        print(f"  Hit rate: {cache.get_stats()['hit_rate']}%")

        pool.close_all()
        return result

    finally:
        db_path.unlink()


def benchmark_rule_engine_caching():
    """Benchmark rule engine with destination caching."""
    print("\n" + "=" * 80)
    print("BENCHMARK: Rule Engine Caching")
    print("=" * 80)

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = Path(tmp.name)

    try:
        db = Database(str(db_path))
        cache = ChecksumCache(str(db_path))

        # Create a simple rule
        rule = Rule(
            id="test-rule",
            name="Test Rule",
            description="Test rule for benchmarking",
            enabled=True,
            source_directories=["/tmp/test"],
            source_patterns=["*.txt"],
            file_types=["txt"],
            destination="/tmp/dest",
            organize_by_date=False,
            priority=1,
        )

        # Test with RuleEngine caching
        engine_with_cache = RuleEngine(
            database=db,
            cache=cache,
            expand_env_vars=lambda x: x,  # Simple passthrough
        )

        # Simulate repeated destination calculations
        bench = Benchmark("rule-engine-destination-cache")

        # Create dummy file metadata
        from fileflow_core.models import FileMetadata
        from datetime import datetime

        files = [
            FileMetadata(
                path=f"/tmp/test/file{i}.txt",
                filename=f"file{i}.txt",
                extension=".txt",
                size_bytes=1024,
                created_at=datetime.now(),
                modified_at=datetime.now(),
                checksum=None,
                matched_rules=[rule.id],
            )
            for i in range(100)
        ]

        def calculate_destinations_with_cache():
            count = 0
            for _ in range(10):  # Repeat 10 times
                for file in files:
                    _ = engine_with_cache._get_destination(file, rule)
                    count += 1
            return count

        # First run to populate cache
        calculate_destinations_with_cache()

        # Get cache stats before benchmark
        cache_stats_before = engine_with_cache._destination_cache.get_stats()

        # Benchmark with warm cache
        result = bench.run(
            calculate_destinations_with_cache,
            iterations=20,
            warmup=5,
            name="with-destination-cache",
            metadata={"files": len(files), "iterations_per_run": 10},
        )

        cache_stats_after = engine_with_cache._destination_cache.get_stats()

        print(format_benchmark_report(bench.get_summary()))
        print(f"\nDestination Cache Statistics:")
        print(f"  Capacity:  {cache_stats_after['capacity']}")
        print(f"  Size:      {cache_stats_after['size']}")
        print(f"  Hit rate:  {cache_stats_after['hit_rate']}%")
        print(f"  Hits:      {cache_stats_after['hits']}")
        print(f"  Misses:    {cache_stats_after['misses']}")

        db.close()

        return {
            "name": "Rule Engine Destination Caching",
            "result": result.to_dict(),
            "cache_stats": cache_stats_after,
        }

    finally:
        db_path.unlink()


def run_all_benchmarks():
    """Run all benchmarks and generate comprehensive report."""
    print("\n")
    print("=" * 80)
    print("FILEFLOW MANAGER - PERFORMANCE BENCHMARKS")
    print("=" * 80)
    print(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    results = {}

    # Run benchmarks
    results["database_operations"] = benchmark_database_operations()
    results["lru_cache"] = benchmark_lru_cache()
    results["query_cache"] = benchmark_query_cache()
    results["rule_engine_caching"] = benchmark_rule_engine_caching()

    # Generate summary
    print("\n")
    print("=" * 80)
    print("BENCHMARK SUMMARY")
    print("=" * 80)
    print("")
    print("Performance Improvements:")
    print(f"  Database Operations:  {results['database_operations']['speedup']}x faster")
    print(f"  LRU Cache:            {results['lru_cache']['speedup']}x faster")
    print(f"  Query Cache:          {results['query_cache']['speedup']}x faster")
    print("")
    print("Cache Effectiveness:")
    print(
        f"  LRU Cache Hit Rate:   {results['lru_cache']['cache_stats']['hit_rate']}%"
    )
    print(
        f"  Query Cache Hit Rate: {results['query_cache']['cache_stats']['hit_rate']}%"
    )
    print(
        f"  Rule Engine Cache:    {results['rule_engine_caching']['cache_stats']['hit_rate']}%"
    )
    print("=" * 80)

    # Save results to JSON
    output_file = Path("benchmark_results.json")
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nDetailed results saved to: {output_file}")

    return results


if __name__ == "__main__":
    run_all_benchmarks()
