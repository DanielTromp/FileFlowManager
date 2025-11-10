# Observability & Monitoring Guide

**FileFlow Manager** - Production Monitoring Guide

## Overview

Complete observability infrastructure for tracking performance improvements validated in benchmarks:
- Query Cache: 12x faster
- Rule Engine: 99.6% hit rate
- Checksum Caching: 1.11x faster

---

## Quick Start

```python
from fileflow_core.observability import get_logger, get_metrics, monitored
from fileflow_core.cache_monitor import CacheMonitor
from fileflow_core.health import HealthChecker
from fileflow_core.metrics_export import MetricsExporter

# Get logger
logger = get_logger(__name__)
logger.info("Operation started", files=100, pattern="*.txt")

# Track metrics automatically
metrics = get_metrics()

@monitored("file_processing", metrics)
def process_files(files):
    for file in files:
        # Process file
        pass

# Monitor cache performance
monitor = CacheMonitor()
monitor.record_cache_access("my_cache", hit=True)

# Check system health
checker = HealthChecker()
result = checker.check_cache_health(cache_hit_rate=0.95)

# Export metrics
exporter = MetricsExporter()
report = exporter.export_report()
print(report)
```

---

## Components

### 1. Structured Logging

Log with context for better debugging:

```python
from fileflow_core.observability import get_logger

logger = get_logger(__name__)

# Log with context
logger.info("Scanning directory",
    directory="/path/to/scan",
    pattern="*.txt",
    recursive=True
)

# Log errors with exception
try:
    risky_operation()
except Exception as e:
    logger.error("Operation failed",
        error=e,
        file_path="/path/to/file"
    )
```

### 2. Metrics Collection

Track counters, gauges, histograms, and timers:

```python
from fileflow_core.observability import get_metrics

metrics = get_metrics()

# Increment counter
metrics.increment("files_processed")
metrics.increment("cache_hits", labels={"cache": "query"})

# Set gauge
metrics.set_gauge("active_operations", 5)

# Observe histogram values
metrics.observe("file_size_bytes", 1024)

# Time operations
with metrics.time("database_query"):
    result = db.execute(query)

# Get statistics
timer_stats = metrics.get_timer_stats("database_query")
print(f"Mean time: {timer_stats.mean:.4f}s")
print(f"P95: {timer_stats.p95:.4f}s")
```

### 3. Cache Monitoring

Track cache effectiveness:

```python
from fileflow_core.cache_monitor import CacheMonitor

monitor = CacheMonitor()

# Record cache access
cache_value = cache.get(key)
monitor.record_cache_access("destination_cache", hit=(cache_value is not None))

# Record cache size
monitor.record_cache_size("destination_cache",
    size=len(cache._cache),
    capacity=cache.capacity
)

# Get statistics
stats = monitor.get_cache_stats("destination_cache")
print(f"Hit Rate: {stats.hit_rate:.2%}")
print(f"Size: {stats.size} / {stats.capacity}")

# Generate report
report = monitor.format_cache_report()
print(report)
```

### 4. Health Checks

Monitor system health:

```python
from fileflow_core.health import HealthChecker

checker = HealthChecker()

# Check database
result = checker.check_database("/path/to/fileflow.db")
print(f"Database: {result.status.value} - {result.message}")

# Check cache health
result = checker.check_cache_health(cache_hit_rate=0.85)
print(f"Cache: {result.status.value}")

# Check performance
result = checker.check_performance_metrics(avg_operation_time=0.1)
print(f"Performance: {result.status.value}")

# Run all checks
results = checker.run_all_checks(
    db_path="/path/to/fileflow.db",
    cache_hit_rate=0.85,
    fs_path="/path/to/data",
    avg_operation_time=0.1
)

# Get overall status
overall = checker.get_overall_status(results)
print(f"Overall: {overall.value}")

# Format report
report = checker.format_health_report(results)
print(report)
```

### 5. Metrics Export

Export metrics in various formats:

```python
from fileflow_core.metrics_export import MetricsExporter

exporter = MetricsExporter()

# Take snapshot
snapshot = exporter.take_snapshot(include_health_checks=True)

# Export as JSON
json_data = exporter.export_json(snapshot)

# Export as Prometheus format
prom_data = exporter.export_prometheus(snapshot)

# Export as human-readable report
report = exporter.export_report(snapshot)

# Get summary statistics
summary = exporter.get_summary_stats(snapshot)
print(f"Total operations: {summary['total_operations']}")
print(f"Error rate: {summary['error_rate']:.2%}")
print(f"Avg cache hit rate: {summary['avg_cache_hit_rate']:.2%}")

# Save to file
from pathlib import Path
exporter.save_snapshot(Path("metrics.json"), format="json")
```

---

## Integration Patterns

### Pattern 1: Decorated Functions

Automatically track all calls, successes, errors, and duration:

```python
from fileflow_core.observability import monitored, get_metrics

metrics = get_metrics()

@monitored("database_query", metrics)
def execute_query(sql):
    return db.execute(sql)

# Automatically tracks:
# - database_query_total (counter)
# - database_query_success (counter)
# - database_query_errors (counter with error_type label)
# - database_query_duration (timer)
```

### Pattern 2: Manual Tracking

Fine-grained control over metrics:

```python
def process_batch(files):
    metrics = get_metrics()
    logger = get_logger(__name__)

    logger.info("Starting batch", batch_size=len(files))

    with metrics.time("batch_processing"):
        for file in files:
            metrics.increment("files_processed")
            try:
                process_file(file)
                metrics.increment("processing_success")
            except Exception as e:
                metrics.increment("processing_errors",
                    labels={"error_type": type(e).__name__})
                logger.error("Processing failed", error=e, file=str(file))

    logger.info("Batch complete", files_processed=len(files))
```

### Pattern 3: Cache Integration

Monitor existing LRU cache:

```python
from fileflow_core.cache import LRUCache
from fileflow_core.cache_monitor import CacheMonitor

cache = LRUCache(capacity=1000, ttl=300.0)
monitor = CacheMonitor()

def get_with_monitoring(key):
    value = cache.get(key)
    monitor.record_cache_access("my_cache", hit=(value is not None))

    if value is None:
        value = expensive_calculation(key)
        cache.set(key, value)

    # Update size periodically
    monitor.record_cache_size("my_cache",
        size=len(cache._cache),
        capacity=cache.capacity
    )

    return value
```

---

## Production Deployment

### 1. Enable Logging

Configure structured logging format:

```python
import logging
import json

class StructuredFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Add extra fields from record
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        return json.dumps(log_data)

handler = logging.StreamHandler()
handler.setFormatter(StructuredFormatter())
logging.root.addHandler(handler)
logging.root.setLevel(logging.INFO)
```

### 2. Periodic Metrics Export

Export metrics on a schedule:

```python
import schedule
import time
from pathlib import Path
from fileflow_core.metrics_export import MetricsExporter

exporter = MetricsExporter()

def export_metrics():
    snapshot = exporter.take_snapshot(include_health_checks=True)

    # Save JSON for analysis
    timestamp = snapshot.timestamp.strftime("%Y%m%d_%H%M%S")
    exporter.save_snapshot(
        Path(f"metrics_{timestamp}.json"),
        snapshot=snapshot,
        format="json"
    )

    # Log summary
    summary = exporter.get_summary_stats(snapshot)
    print(f"Metrics exported: {summary['total_operations']} operations")

# Export every 5 minutes
schedule.every(5).minutes.do(export_metrics)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### 3. Health Check Endpoint

Expose health checks via API:

```python
from flask import Flask, jsonify
from fileflow_core.health import HealthChecker

app = Flask(__name__)
checker = HealthChecker()

@app.route("/health")
def health():
    results = checker.run_all_checks(
        db_path="/var/lib/fileflow/fileflow.db",
        cache_hit_rate=0.8,  # From cache monitor
        fs_path="/var/lib/fileflow/data",
        avg_operation_time=0.1  # From metrics
    )

    overall = checker.get_overall_status(results)

    return jsonify({
        "status": overall.value,
        "checks": {
            name: {
                "status": result.status.value,
                "message": result.message,
                "latency_ms": result.latency_ms
            }
            for name, result in results.items()
        }
    })
```

---

## Monitoring Dashboard Example

Create a simple monitoring dashboard:

```python
from fileflow_core.metrics_export import MetricsExporter
from fileflow_core.cache_monitor import CacheMonitor

def print_dashboard():
    exporter = MetricsExporter()
    snapshot = exporter.take_snapshot(include_health_checks=True)
    summary = exporter.get_summary_stats(snapshot)

    print("=" * 80)
    print("FILEFLOW MANAGER - MONITORING DASHBOARD")
    print("=" * 80)
    print(f"\nTimestamp: {snapshot.timestamp.isoformat()}")
    print(f"\nOverall Status: {summary['overall_health'].upper()}")
    print(f"\nOperations:")
    print(f"  Total:       {summary['total_operations']:,}")
    print(f"  Errors:      {summary['total_errors']:,}")
    print(f"  Error Rate:  {summary['error_rate']:.2%}")
    print(f"\nCache Performance:")
    print(f"  Avg Hit Rate:  {summary['avg_cache_hit_rate']:.2%}")
    print(f"  Num Caches:    {summary['num_caches']}")

    # Detailed cache stats
    for cache_name, stats in snapshot.cache_stats.items():
        print(f"\n{cache_name}:")
        print(f"  Hit Rate: {stats.hit_rate:.2%}")
        print(f"  Hits:     {stats.hits:,}")
        print(f"  Misses:   {stats.misses:,}")

    print("=" * 80)

# Run dashboard
print_dashboard()
```

---

## Examples

Complete examples available in `examples/observability_example.py`:

```bash
poetry run python examples/observability_example.py
```

Includes examples of:
1. Structured logging with context
2. Metrics tracking with decorators
3. Manual metrics collection
4. Cache monitoring
5. Health checks
6. Metrics export
7. Complete monitoring workflow

---

## Testing

Run comprehensive tests:

```bash
# Run all observability tests
poetry run pytest tests/test_observability.py tests/test_health.py tests/test_cache_monitor.py -v

# Run with coverage
poetry run pytest tests/test_observability.py tests/test_health.py tests/test_cache_monitor.py --cov=fileflow_core --cov-report=term-missing
```

Test coverage:
- observability.py: 96%
- health.py: 89%
- cache_monitor.py: 94%
- Total: 50 tests, all passing

---

## Performance Impact

Monitoring overhead is minimal:
- Metrics collection: <1% CPU overhead
- Cache monitoring: Negligible (simple counter increments)
- Health checks: Run on demand only
- Structured logging: Async-friendly, minimal impact

---

## Best Practices

1. **Use structured logging**: Always include context
2. **Monitor cache hit rates**: Alert if below 70%
3. **Track error rates**: Alert if above 1%
4. **Export metrics periodically**: Every 5-10 minutes
5. **Run health checks on startup**: Verify system is ready
6. **Use labels sparingly**: Too many unique labels = high cardinality

---

## Troubleshooting

**High memory usage?**
- Reduce metrics retention
- Reset metrics periodically: `get_metrics().reset()`
- Use smaller histogram sample sizes

**Cache hit rate low?**
- Check cache capacity
- Review TTL settings
- Analyze access patterns

**Performance degraded?**
- Check avg_operation_time in health checks
- Review timer percentiles (p95, p99)
- Look for error rate spikes

---

## See Also

- PERFORMANCE.md - Performance benchmark results
- INTEGRATION.md - Infrastructure integration details
- examples/observability_example.py - Complete examples
- tests/test_observability.py - Test examples
