# FileFlow Manager Performance & Reliability Guide

This guide explains the performance optimizations and reliability features built into FileFlow Manager.

## Table of Contents

1. [Error Handling](#error-handling)
2. [Progress Tracking & Cancellation](#progress-tracking--cancellation)
3. [Retry Logic](#retry-logic)
4. [Caching](#caching)
5. [Database Optimization](#database-optimization)
6. [Performance Best Practices](#performance-best-practices)
7. [Monitoring & Profiling](#monitoring--profiling)

---

## Error Handling

FileFlow Manager provides comprehensive error handling with user-friendly messages and actionable suggestions.

### Error Types

**FileFlowError** - Base exception with enhanced information:
```python
from fileflow_core.errors import FileOperationError

try:
    move_file(source, destination)
except FileOperationError as e:
    print(e.user_message)  # User-friendly message
    print(e.suggestion)    # Actionable suggestion
    print(e.severity.value)  # 'info', 'warning', 'error', 'critical'
    print(e.details)       # Additional context
```

**Available Exception Types:**
- `ConfigurationError` - Configuration file issues
- `FileOperationError` - File move/delete/copy errors
- `DatabaseError` - Database access errors
- `ValidationError` - Input validation errors
- `ScanError` - File scanning errors
- `DuplicateDetectionError` - Checksum calculation errors
- `RuleError` - Rule configuration/execution errors
- `OperationCancelledError` - User-cancelled operations
- `RetryableError` - Errors that should be retried

### Error Context

All errors include:
- **message**: Technical error for logs
- **user_message**: User-friendly description
- **suggestion**: Actionable fix
- **severity**: Error level (info/warning/error/critical)
- **details**: Additional context (file paths, rule IDs, etc.)
- **recoverable**: Whether operation can be retried

### Example Usage

```python
from fileflow_core.errors import format_error_for_user

try:
    scan_files(rules)
except Exception as e:
    error_info = format_error_for_user(e)

    print(f"Error: {error_info['user_message']}")
    print(f"Suggestion: {error_info['suggestion']}")

    # In GUI: show error dialog
    show_error_dialog(
        title=error_info['type'],
        message=error_info['user_message'],
        details=error_info['suggestion']
    )
```

### Permission Error Handling

Special handling for common macOS permission issues:

```python
try:
    scan_directory("/Users/username/Desktop")
except FileOperationError as e:
    if "permission" in str(e).lower():
        print("Grant Full Disk Access:")
        print("  System Settings → Privacy & Security → Full Disk Access")
```

---

## Progress Tracking & Cancellation

Track progress of long-running operations with real-time updates and user cancellation.

### Basic Usage

```python
from fileflow_core.progress import ProgressTracker

# Create tracker
tracker = ProgressTracker(
    operation_id="scan-files-001",
    total_items=1000,
    callback=lambda progress: print(f"{progress.percentage:.1f}% complete")
)

# Start operation
tracker.start()

try:
    for i, file in enumerate(files):
        # Check for cancellation
        tracker.update(
            completed=i+1,
            current_item=str(file)
        )

        # Process file
        process_file(file)

    tracker.complete()

except OperationCancelledError:
    print("Operation cancelled by user")
except Exception as e:
    tracker.fail(str(e))
```

### Progress Information

```python
progress = tracker.get_progress()

print(f"Status: {progress.status.value}")
print(f"Progress: {progress.completed_items}/{progress.total_items}")
print(f"Percentage: {progress.percentage:.1f}%")
print(f"Elapsed: {progress.elapsed_time:.1f}s")
print(f"Remaining: {progress.estimated_remaining:.1f}s")
print(f"Speed: {progress.items_per_second:.1f} items/sec")
print(f"Current: {progress.current_item}")
```

### Cancellation

```python
# User clicks cancel button
tracker.cancel()

# In operation loop
try:
    tracker.update(current_item="file.txt")
    # Raises OperationCancelledError if cancelled
except OperationCancelledError:
    cleanup()
    raise
```

### Pause/Resume

```python
# Pause operation
tracker.pause()

# Resume operation
tracker.resume()

# Check status
if tracker.is_paused():
    print("Operation is paused")
```

### Progress Manager

Manage multiple concurrent operations:

```python
from fileflow_core.progress import get_progress_manager

manager = get_progress_manager()

# Create multiple trackers
scan_tracker = manager.create_tracker("scan", total_items=1000)
delete_tracker = manager.create_tracker("delete", total_items=50)

# Get all progress
all_progress = manager.get_all_progress()
for p in all_progress:
    print(f"{p.operation_id}: {p.percentage:.1f}%")

# Cancel specific operation
manager.cancel_operation("scan")

# Cleanup completed operations
manager.cleanup_completed()
```

---

## Retry Logic

Automatic retry with exponential backoff for transient failures.

### Decorator Usage

```python
from fileflow_core.retry import with_retry, retry_file_operation

# Simple retry
@with_retry(max_attempts=5, initial_delay=1.0)
def unreliable_function():
    # May fail transiently
    pass

# Pre-configured for file operations
@retry_file_operation
def move_file(source, dest):
    # Will retry on OSError, PermissionError
    os.rename(source, dest)
```

### Custom Retry Configuration

```python
from fileflow_core.retry import RetryConfig, with_retry

config = RetryConfig(
    max_attempts=5,           # Try up to 5 times
    initial_delay=1.0,        # Start with 1 second delay
    max_delay=60.0,           # Cap at 60 seconds
    exponential_base=2.0,     # Double delay each attempt
    jitter=True,              # Add random variation
    retryable_exceptions=(OSError, TimeoutError)
)

@with_retry(config=config)
def network_operation():
    # Will retry with exponential backoff
    pass
```

### Exponential Backoff

Retry delays increase exponentially:
```
Attempt 1: Fails → Wait 1.0s
Attempt 2: Fails → Wait 2.0s
Attempt 3: Fails → Wait 4.0s
Attempt 4: Fails → Wait 8.0s
Attempt 5: Fails → Raise exception
```

With jitter (±25% randomness):
```
Attempt 1: Wait 0.75-1.25s
Attempt 2: Wait 1.5-2.5s
Attempt 3: Wait 3.0-5.0s
Attempt 4: Wait 6.0-10.0s
```

### Pre-configured Decorators

**File Operations** (short delays, more attempts):
```python
from fileflow_core.retry import retry_file_operation

@retry_file_operation
def file_op():
    # 5 attempts, 0.5s initial delay, max 10s
    pass
```

**Network Operations** (longer delays, fewer attempts):
```python
from fileflow_core.retry import retry_network_operation

@retry_network_operation
def network_op():
    # 3 attempts, 2.0s initial delay, max 30s
    pass
```

**Database Operations** (quick retries for locks):
```python
from fileflow_core.retry import retry_database_operation

@retry_database_operation
def db_op():
    # 5 attempts, 0.1s initial delay, max 5s
    pass
```

### Non-Decorator Usage

```python
from fileflow_core.retry import retry_on_failure

result = retry_on_failure(
    some_function,
    RetryConfig(max_attempts=3),
    arg1, arg2,
    kwarg1=value1
)
```

---

## Caching

Multi-level caching for performance optimization.

### LRU Cache

In-memory cache with automatic eviction:

```python
from fileflow_core.cache import LRUCache

# Create cache
cache = LRUCache(capacity=1000, ttl=300.0)  # 5 minute TTL

# Store value
cache.set("key", {"data": "value"})

# Retrieve value
value = cache.get("key")
if value:
    print("Cache hit!")
else:
    print("Cache miss")

# Invalidate entry
cache.invalidate("key")

# Clear all
cache.clear()

# Get statistics
stats = cache.get_stats()
print(f"Hit rate: {stats['hit_rate']}%")
print(f"Size: {stats['size']}/{stats['capacity']}")
```

### Function Result Caching

```python
from fileflow_core.cache import cached

# Cache with default settings
@cached(ttl=60.0)
def expensive_computation(arg1, arg2):
    # Result cached for 60 seconds
    return complex_calculation(arg1, arg2)

# Custom cache key
def custom_key(user_id, date):
    return f"{user_id}:{date.isoformat()}"

@cached(key_func=custom_key)
def user_data(user_id, date):
    return fetch_data(user_id, date)

# Manual cache management
expensive_computation.invalidate(arg1, arg2)  # Invalidate specific
expensive_computation.clear_cache()  # Clear all
```

### Query Cache

Cache database query results:

```python
from fileflow_core.cache import QueryCache

query_cache = QueryCache(capacity=500, ttl=300.0)

# Check cache
result = query_cache.get("SELECT * FROM rules WHERE enabled=?", (True,))
if result is None:
    # Execute query
    result = cursor.execute("SELECT * FROM rules WHERE enabled=?", (True,)).fetchall()
    # Cache result
    query_cache.set("SELECT * FROM rules WHERE enabled=?", (True,), result)

# Invalidate when table changes
query_cache.invalidate_table("rules")

# Statistics
stats = query_cache.get_stats()
print(f"Query cache hit rate: {stats['hit_rate']}%")
```

---

## Database Optimization

Connection pooling and query optimization.

### Connection Pool

Reuse database connections:

```python
from fileflow_core.cache import ConnectionPool

# Create pool
pool = ConnectionPool(
    db_path="/path/to/db.sqlite",
    pool_size=5,
    timeout=30.0
)

# Use connection
with pool.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM operations")
    results = cursor.fetchall()

# Automatic return to pool when context exits

# Get statistics
stats = pool.get_stats()
print(f"Available connections: {stats['available']}/{stats['pool_size']}")
```

### WAL Mode

Connection pool automatically enables Write-Ahead Logging:
```sql
PRAGMA journal_mode=WAL;  -- Better concurrency
PRAGMA synchronous=NORMAL; -- Balanced safety/performance
```

Benefits:
- Readers don't block writers
- Writers don't block readers
- Better concurrent performance

### Query Optimization

**Use Prepared Statements:**
```python
# Bad: SQL injection risk, no caching
cursor.execute(f"SELECT * FROM rules WHERE id='{rule_id}'")

# Good: Parameterized, cached by SQLite
cursor.execute("SELECT * FROM rules WHERE id=?", (rule_id,))
```

**Use Indexes:**
```sql
CREATE INDEX idx_operations_rule_id ON operations(rule_id);
CREATE INDEX idx_operations_timestamp ON operations(created_at);
```

**Batch Operations:**
```python
# Bad: Individual inserts
for op in operations:
    cursor.execute("INSERT INTO operations VALUES (?, ?)", op)
    conn.commit()

# Good: Batch with single transaction
cursor.executemany("INSERT INTO operations VALUES (?, ?)", operations)
conn.commit()
```

---

## Performance Best Practices

### File Scanning

**Limit Scope:**
```python
# Bad: Scan entire home directory
scan_directory(Path.home())

# Good: Scan specific directories
scan_directory(Path.home() / "Desktop")
scan_directory(Path.home() / "Downloads")
```

**Use Generators:**
```python
# Bad: Load all files into memory
files = list(path.rglob("*.txt"))

# Good: Process one at a time
for file in path.rglob("*.txt"):
    process_file(file)
```

**Filter Early:**
```python
# Bad: Load all, then filter
all_files = scan_all_files()
pdf_files = [f for f in all_files if f.suffix == ".pdf"]

# Good: Filter during scan
pdf_files = path.rglob("*.pdf")
```

### Checksum Calculation

**Use Cache:**
```python
from fileflow_storage.cache import ChecksumCache

cache = ChecksumCache(database)

# First scan: Calculates checksums
for file in files:
    checksum = cache.get_or_compute_checksum(file)

# Subsequent scans: Uses cache
for file in files:
    checksum = cache.get_or_compute_checksum(file)  # Fast!
```

**Clear When Needed:**
```python
# Clear if files changed significantly
cache.clear()
```

### Concurrent Processing

**Use Worker Pool:**
```python
from concurrent.futures import ThreadPoolExecutor
import os

# Limit to CPU count
max_workers = os.cpu_count()

with ThreadPoolExecutor(max_workers=max_workers) as executor:
    futures = [executor.submit(process_file, f) for f in files]
    results = [f.result() for f in futures]
```

**Don't Over-Parallelize:**
```python
# Bad: Too many threads for I/O
ThreadPoolExecutor(max_workers=100)

# Good: Match CPU count
ThreadPoolExecutor(max_workers=os.cpu_count())
```

---

## Monitoring & Profiling

### Cache Statistics

```python
# LRU Cache
stats = cache.get_stats()
print(f"Size: {stats['size']}/{stats['capacity']}")
print(f"Hits: {stats['hits']}, Misses: {stats['misses']}")
print(f"Hit Rate: {stats['hit_rate']}%")

# Connection Pool
stats = pool.get_stats()
print(f"Connections: {stats['in_use']}/{stats['pool_size']}")

# Query Cache
stats = query_cache.get_stats()
print(f"Query hit rate: {stats['hit_rate']}%")
```

### Progress Monitoring

```python
progress = tracker.get_progress()
print(f"Speed: {progress.items_per_second:.1f} items/sec")
print(f"ETA: {progress.estimated_remaining:.0f}s")
```

### Performance Profiling

**Profile Python code:**
```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Your code here
scan_files(rules)

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20 functions
```

**Profile with line profiler:**
```bash
# Install
pip install line_profiler

# Decorate function
@profile
def scan_files():
    pass

# Run
kernprof -l -v script.py
```

### Database Profiling

```python
import sqlite3

conn.set_trace_callback(print)  # Log all queries

# Or count queries
query_count = 0
def count_queries(statement):
    global query_count
    query_count += 1

conn.set_trace_callback(count_queries)
```

---

## Performance Targets

### Recommended Thresholds

| Operation | Target | Acceptable | Poor |
|-----------|--------|------------|------|
| Scan 1K files | <1s | 1-3s | >3s |
| Scan 10K files | <10s | 10-30s | >30s |
| Move file (same drive) | <50ms | 50-200ms | >200ms |
| Checksum (10MB file) | <100ms | 100-500ms | >500ms |
| Database query | <10ms | 10-50ms | >50ms |
| Cache hit rate | >80% | 60-80% | <60% |

### Optimization Checklist

- [ ] Enable connection pooling for database
- [ ] Use query cache for repeated queries
- [ ] Enable checksum caching
- [ ] Use retry logic for transient failures
- [ ] Implement progress tracking for long operations
- [ ] Add proper error handling with suggestions
- [ ] Profile slow operations
- [ ] Monitor cache hit rates
- [ ] Use batch operations where possible
- [ ] Limit concurrent workers to CPU count

---

## Summary

FileFlow Manager includes comprehensive performance and reliability features:

✅ **Error Handling**: User-friendly messages with actionable suggestions
✅ **Progress Tracking**: Real-time progress with cancellation support
✅ **Retry Logic**: Automatic retry with exponential backoff
✅ **Caching**: Multi-level caching (LRU, query, checksum)
✅ **Connection Pooling**: Efficient database access
✅ **Performance Monitoring**: Cache stats, progress metrics

These features work together to provide a fast, reliable, and user-friendly experience.
