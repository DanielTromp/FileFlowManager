"""
Example of integrating observability into FileFlow Manager.

Demonstrates how to:
- Add structured logging
- Track metrics
- Monitor cache performance
- Export metrics and reports
"""

import time

from fileflow_core.cache import LRUCache
from fileflow_core.cache_monitor import CacheMonitor
from fileflow_core.health import HealthChecker
from fileflow_core.metrics_export import MetricsExporter
from fileflow_core.observability import (
    get_logger,
    get_metrics,
    monitored,
)


# Example 1: Basic structured logging
def example_structured_logging():
    """Example of using structured logging."""
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Structured Logging")
    print("=" * 80 + "\n")

    logger = get_logger(__name__)

    # Log with context
    logger.info("Starting file scan", directory="/path/to/scan", pattern="*.txt")

    # Log with error
    try:
        raise ValueError("Invalid configuration")
    except ValueError as e:
        logger.error("Configuration error occurred", error=e, config_file="settings.json")

    # Log warning
    logger.warning("Cache hit rate is low", hit_rate=0.45, threshold=0.5)

    print("✓ Logged messages with structured context\n")


# Example 2: Tracking metrics with decorators
def example_metrics_tracking():
    """Example of tracking metrics with decorators."""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Metrics Tracking")
    print("=" * 80 + "\n")

    metrics = get_metrics()

    @monitored("file_processing", metrics)
    def process_file(filename: str) -> bool:
        """Simulated file processing."""
        time.sleep(0.01)  # Simulate work
        if "error" in filename:
            raise ValueError("Simulated error")
        return True

    # Process some files
    for i in range(10):
        try:
            process_file(f"file_{i}.txt")
        except ValueError:
            pass

    # Check metrics
    total = metrics.get_counter("file_processing_total")
    success = metrics.get_counter("file_processing_success")
    errors = metrics.get_counter("file_processing_errors")

    print(f"Total operations:   {total}")
    print(f"Successful:         {success}")
    print(f"Errors:             {errors}")
    print(f"Success rate:       {success / total * 100:.1f}%\n")


# Example 3: Manual metrics collection
def example_manual_metrics():
    """Example of manual metrics collection."""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Manual Metrics Collection")
    print("=" * 80 + "\n")

    metrics = get_metrics()

    # Increment counter
    for _ in range(5):
        metrics.increment("files_scanned")

    # Set gauge
    metrics.set_gauge("active_operations", 3)
    metrics.set_gauge("queue_size", 127)

    # Observe histogram values
    for duration in [0.1, 0.2, 0.15, 0.3, 0.12]:
        metrics.observe("operation_duration", duration)

    # Time operations
    with metrics.time("database_query"):
        time.sleep(0.05)  # Simulate query

    # Get statistics
    print(f"Files scanned:      {metrics.get_counter('files_scanned')}")
    print(f"Active operations:  {metrics.get_gauge('active_operations')}")
    print(f"Queue size:         {metrics.get_gauge('queue_size')}\n")


# Example 4: Cache monitoring
def example_cache_monitoring():
    """Example of monitoring cache performance."""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Cache Monitoring")
    print("=" * 80 + "\n")

    # Create cache and monitor
    cache = LRUCache(capacity=100, ttl=60.0)
    monitor = CacheMonitor()

    # Simulate cache operations
    for i in range(50):
        key = f"key_{i % 10}"  # Some keys will repeat (cache hits)
        value = cache.get(key)

        if value is None:
            # Cache miss
            cache.set(key, f"value_{i}")
            monitor.record_cache_access("destination_cache", hit=False)
        else:
            # Cache hit
            monitor.record_cache_access("destination_cache", hit=True)

        # Update cache size
        monitor.record_cache_size("destination_cache", len(cache._cache), cache.capacity)

    # Get cache statistics
    stats = monitor.get_cache_stats("destination_cache")
    if stats:
        print(f"Cache: {stats.name}")
        print(f"  Hit Rate:    {stats.hit_rate:.2%}")
        print(f"  Hits:        {stats.hits}")
        print(f"  Misses:      {stats.misses}")
        print(f"  Size:        {stats.size} / {stats.capacity}")
        print(f"  Utilization: {stats.size / stats.capacity * 100:.1f}%\n")


# Example 5: Health checks
def example_health_checks():
    """Example of running health checks."""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Health Checks")
    print("=" * 80 + "\n")

    checker = HealthChecker()

    # Check cache health (excellent)
    result = checker.check_cache_health(cache_hit_rate=0.95)
    print(f"✓ Cache Health: {result.status.value} - {result.message}")

    # Check performance (healthy)
    result = checker.check_performance_metrics(avg_operation_time=0.05)
    print(f"✓ Performance: {result.status.value} - {result.message}")

    # Check cache health (degraded)
    result = checker.check_cache_health(cache_hit_rate=0.65)
    print(f"⚠ Cache Health: {result.status.value} - {result.message}")

    # Check performance (unhealthy)
    result = checker.check_performance_metrics(avg_operation_time=2.0)
    print(f"✗ Performance: {result.status.value} - {result.message}\n")


# Example 6: Metrics export
def example_metrics_export():
    """Example of exporting metrics."""
    print("\n" + "=" * 80)
    print("EXAMPLE 6: Metrics Export")
    print("=" * 80 + "\n")

    exporter = MetricsExporter()

    # Generate some metrics
    metrics = get_metrics()
    metrics.increment("operations_total", 100)
    metrics.increment("operations_success", 95)
    metrics.increment("operations_errors", 5)
    metrics.set_gauge("active_connections", 5)

    # Take a snapshot
    snapshot = exporter.take_snapshot()

    # Export as JSON
    json_export = exporter.export_json(snapshot)
    print("JSON Export (first 300 chars):")
    print(json_export[:300] + "...\n")

    # Export summary statistics
    summary = exporter.get_summary_stats(snapshot)
    print("Summary Statistics:")
    for key, value in summary.items():
        print(f"  {key:25} {value}")
    print()


# Example 7: Complete monitoring workflow
def example_complete_workflow():
    """Example of complete monitoring workflow."""
    print("\n" + "=" * 80)
    print("EXAMPLE 7: Complete Monitoring Workflow")
    print("=" * 80 + "\n")

    # Initialize components
    metrics = get_metrics()
    logger = get_logger(__name__)
    monitor = CacheMonitor()
    MetricsExporter()

    # Simulated operation
    logger.info("Starting batch file processing", batch_size=50)

    with metrics.time("batch_processing"):
        for i in range(50):
            # Track operation
            metrics.increment("files_processed")

            # Simulate cache access
            cache_hit = i % 3 == 0  # 33% hit rate
            monitor.record_cache_access("file_metadata_cache", hit=cache_hit)

            # Simulate some errors
            if i % 10 == 0:
                metrics.increment("processing_errors")
                logger.warning("File processing error", file_index=i, error="Permission denied")

    logger.info("Batch processing complete", files_processed=50)

    # Generate report
    print("\nPerformance Report:")
    print("-" * 80)

    # Get metrics
    total = metrics.get_counter("files_processed")
    errors = metrics.get_counter("processing_errors")
    timer_stats = metrics.get_timer_stats("batch_processing")

    print(f"Files Processed:    {total}")
    print(f"Errors:             {errors}")
    print(f"Success Rate:       {(total - errors) / total * 100:.1f}%")
    if timer_stats:
        print(f"Processing Time:    {timer_stats.mean:.3f}s")

    # Cache statistics
    cache_stats = monitor.get_cache_stats("file_metadata_cache")
    if cache_stats:
        print("\nCache Performance:")
        print(f"  Hit Rate:         {cache_stats.hit_rate:.2%}")
        print(f"  Hits/Misses:      {cache_stats.hits} / {cache_stats.misses}")

    print()


def run_all_examples():
    """Run all observability examples."""
    print("\n")
    print("=" * 80)
    print("FILEFLOW MANAGER - OBSERVABILITY EXAMPLES")
    print("=" * 80)

    example_structured_logging()
    example_metrics_tracking()
    example_manual_metrics()
    example_cache_monitoring()
    example_health_checks()
    example_metrics_export()
    example_complete_workflow()

    print("\n")
    print("=" * 80)
    print("ALL EXAMPLES COMPLETE")
    print("=" * 80)
    print("\nKey Takeaways:")
    print("  1. Use get_logger(__name__) for structured logging with context")
    print("  2. Use @monitored decorator for automatic metrics tracking")
    print("  3. Use CacheMonitor to track cache hit rates and effectiveness")
    print("  4. Use HealthChecker to monitor system health")
    print("  5. Use MetricsExporter to export metrics in various formats")
    print("  6. All components are thread-safe and production-ready")
    print()


if __name__ == "__main__":
    run_all_examples()
