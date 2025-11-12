"""
Integration tests for infrastructure components.

Tests the interaction between error handling, retry logic, progress tracking,
and caching in realistic scenarios.
"""

import tempfile
import threading
import time
from pathlib import Path

import pytest

from fileflow_core.cache import ConnectionPool, LRUCache, QueryCache
from fileflow_core.errors import (
    OperationCancelledError,
    RetryableError,
)
from fileflow_core.progress import ProgressManager, ProgressTracker
from fileflow_core.retry import retry_database_operation, with_retry


class TestRetryWithProgress:
    """Test retry logic integrated with progress tracking."""

    def test_retryable_operation_with_progress(self):
        """Test retry with progress tracking."""
        tracker = ProgressTracker("retry-test", total_items=3)
        tracker.start()

        attempt_count = [0]

        @with_retry(max_attempts=3, initial_delay=0.01)
        def flaky_operation(item_id):
            attempt_count[0] += 1
            tracker.update(completed=attempt_count[0])

            if attempt_count[0] < 3:
                raise RetryableError(f"Temporary failure on attempt {attempt_count[0]}")

            return f"success-{item_id}"

        result = flaky_operation(1)

        assert result == "success-1"
        assert attempt_count[0] == 3
        assert tracker.get_progress().completed_items == 3

    def test_cancelled_operation_stops_retry(self):
        """Test cancellation stops retry attempts."""
        tracker = ProgressTracker("cancel-test", total_items=10)
        tracker.start()

        attempt_count = [0]

        @with_retry(max_attempts=5, initial_delay=0.01)
        def operation_with_cancel_check():
            attempt_count[0] += 1

            # Cancel after first attempt
            if attempt_count[0] == 1:
                tracker.cancel()

            # Check for cancellation
            if tracker.is_cancelled():
                raise OperationCancelledError()

            raise RetryableError("Keep trying")

        # Should raise OperationCancelledError on first retry
        with pytest.raises(OperationCancelledError):
            operation_with_cancel_check()

        # Should have tried at most twice (initial + one retry before cancel check)
        assert attempt_count[0] <= 2


class TestProgressWithCancellation:
    """Test progress tracking with cancellation."""

    def test_multi_step_operation_with_cancellation(self):
        """Test cancelling a multi-step operation."""
        manager = ProgressManager()
        tracker = manager.create_tracker("multi-step", total_items=100)
        tracker.start()

        processed_items = []

        def process_items():
            try:
                for i in range(100):
                    tracker.update(completed=i, current_item=f"item-{i}")
                    processed_items.append(i)
                    time.sleep(0.001)  # Simulate work
                tracker.complete()
            except OperationCancelledError:
                pass

        # Start processing in thread
        worker = threading.Thread(target=process_items)
        worker.start()

        # Let it process some items
        time.sleep(0.05)

        # Cancel the operation
        manager.cancel_operation("multi-step")

        # Wait for completion
        worker.join(timeout=1.0)

        # Should have processed some but not all items
        assert len(processed_items) < 100
        assert tracker.get_progress().status.value == "cancelled"


class TestDatabaseWithRetryAndCache:
    """Test database operations with retry, caching, and error handling."""

    def test_database_operation_with_retry(self):
        """Test database operations with automatic retry on lock."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = Path(tmp.name)

        try:
            pool = ConnectionPool(db_path, pool_size=2)

            # Create table
            with pool.get_connection() as conn:
                conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
                conn.commit()

            # Simulate database locked scenario with retry
            @retry_database_operation
            def insert_user(user_id, name):
                with pool.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO users VALUES (?, ?)", (user_id, name))
                    conn.commit()

            # Should succeed with retry
            insert_user(1, "Alice")
            insert_user(2, "Bob")

            # Verify
            with pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM users")
                count = cursor.fetchone()[0]
                assert count == 2

            pool.close_all()
        finally:
            db_path.unlink()

    def test_database_with_query_cache(self):
        """Test database with query caching."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = Path(tmp.name)

        try:
            pool = ConnectionPool(db_path, pool_size=2)
            cache = QueryCache()

            # Create and populate table
            with pool.get_connection() as conn:
                conn.execute("CREATE TABLE products (id INTEGER, name TEXT, price REAL)")
                conn.execute("INSERT INTO products VALUES (1, 'Widget', 9.99)")
                conn.execute("INSERT INTO products VALUES (2, 'Gadget', 19.99)")
                conn.commit()

            query = "SELECT * FROM products WHERE id = ?"
            params = (1,)

            # First query - not cached
            with pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                result1 = cursor.fetchall()
                cache.cache_query(query, params, result1)

            # Second query - from cache
            cached_result = cache.get(query, params)
            assert cached_result == result1

            # Modify table - invalidate cache
            with pool.get_connection() as conn:
                conn.execute("UPDATE products SET price = 12.99 WHERE id = 1")
                conn.commit()

            cache.invalidate_table("products")

            # Cache should be cleared
            cached_result = cache.get(query, params)
            assert cached_result is None

            pool.close_all()
        finally:
            db_path.unlink()


class TestErrorHandlingIntegration:
    """Test error handling across components."""

    def test_error_with_retry_and_progress(self):
        """Test error handling with retry and progress tracking."""
        tracker = ProgressTracker("error-test", total_items=5)
        tracker.start()

        attempt_log = []

        @with_retry(max_attempts=3, initial_delay=0.01)
        def operation_with_errors(item_id):
            attempt_log.append(("attempt", item_id))

            if len(attempt_log) < 3:
                # First two attempts fail
                raise RetryableError("Temporary error")

            # Third attempt succeeds
            tracker.update(completed=item_id)
            return f"success-{item_id}"

        result = operation_with_errors(5)

        assert result == "success-5"
        assert len(attempt_log) == 3
        assert tracker.get_progress().completed_items == 5

    def test_non_retryable_error_stops_operation(self):
        """Test non-retryable error stops operation immediately."""
        tracker = ProgressTracker("non-retry-test", total_items=10)
        tracker.start()

        @with_retry(max_attempts=5, initial_delay=0.01)
        def operation_with_fatal_error():
            tracker.update(increment=1)
            raise ValueError("Fatal error")  # Non-retryable

        with pytest.raises(ValueError):
            operation_with_fatal_error()

        # Should have failed immediately
        assert tracker.get_progress().completed_items == 1


class TestConcurrentOperations:
    """Test concurrent operations with all infrastructure components."""

    def test_concurrent_database_operations(self):
        """Test concurrent database operations with connection pooling."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = Path(tmp.name)

        try:
            pool = ConnectionPool(db_path, pool_size=5)
            manager = ProgressManager()
            errors = []

            # Create table
            with pool.get_connection() as conn:
                conn.execute("CREATE TABLE logs (thread_id INTEGER, item_id INTEGER)")
                conn.commit()

            def worker(thread_id):
                try:
                    tracker = manager.create_tracker(
                        f"worker-{thread_id}", total_items=10
                    )
                    tracker.start()

                    @retry_database_operation
                    def insert_log(item_id):
                        with pool.get_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute(
                                "INSERT INTO logs VALUES (?, ?)", (thread_id, item_id)
                            )
                            conn.commit()
                        tracker.update(increment=1)

                    for i in range(10):
                        insert_log(i)

                    tracker.complete()
                except Exception as e:
                    errors.append(e)

            # Start workers
            threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            # Verify
            assert len(errors) == 0

            # Check all operations completed
            all_progress = manager.get_all_progress()
            assert len(all_progress) == 5
            assert all(p.status.value == "completed" for p in all_progress)

            # Check all records inserted
            with pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM logs")
                count = cursor.fetchone()[0]
                assert count == 50  # 5 workers × 10 items

            pool.close_all()
        finally:
            db_path.unlink()


class TestCachingWithRetry:
    """Test caching integrated with retry logic."""

    def test_cached_operation_with_retry(self):
        """Test cached operations with retry on failure."""
        cache = LRUCache(capacity=10)
        call_count = [0]

        @with_retry(max_attempts=3, initial_delay=0.01)
        def expensive_operation(key):
            # Check cache first
            cached = cache.get(key)
            if cached is not None:
                return cached

            # Simulate expensive computation
            call_count[0] += 1

            if call_count[0] < 2:
                raise RetryableError("Computation failed")

            result = f"computed-{key}"
            cache.set(key, result)
            return result

        # First call - will fail then succeed on retry
        result1 = expensive_operation("key1")
        assert result1 == "computed-key1"
        assert call_count[0] == 2

        # Second call - from cache, no retry needed
        call_count[0] = 0
        result2 = expensive_operation("key1")
        assert result2 == "computed-key1"
        assert call_count[0] == 0  # Not called, used cache


class TestProgressCallbacks:
    """Test progress tracking with callbacks."""

    def test_progress_callback_with_retry(self):
        """Test progress callbacks during retry operations."""
        progress_updates = []

        def progress_callback(progress_info):
            progress_updates.append(
                {
                    "completed": progress_info.completed_items,
                    "status": progress_info.status.value,
                }
            )

        tracker = ProgressTracker(
            "callback-test", total_items=10, callback=progress_callback, callback_interval=0.01
        )

        attempt_count = [0]

        @with_retry(max_attempts=3, initial_delay=0.01)
        def operation_with_progress():
            attempt_count[0] += 1

            tracker.start()

            for i in range(10):
                tracker.update(completed=i + 1)
                time.sleep(0.001)

            if attempt_count[0] < 2:
                tracker.fail("Temporary failure")
                raise RetryableError("Try again")

            tracker.complete()

        operation_with_progress()

        # Should have received multiple progress updates
        assert len(progress_updates) > 0

        # Final update should show completion
        assert progress_updates[-1]["status"] == "completed"
        assert progress_updates[-1]["completed"] == 10


class TestRealWorldScenario:
    """Test realistic end-to-end scenarios."""

    def test_file_processing_simulation(self):
        """Simulate file processing with all infrastructure components."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = Path(tmp.name)

        try:
            # Setup
            pool = ConnectionPool(db_path, pool_size=3)
            cache = LRUCache(capacity=100)
            manager = ProgressManager()

            # Create database
            with pool.get_connection() as conn:
                conn.execute(
                    "CREATE TABLE file_metadata (path TEXT PRIMARY KEY, size INTEGER, processed BOOLEAN)"
                )
                conn.commit()

            # Simulate processing files
            tracker = manager.create_tracker("process-files", total_items=20)
            tracker.start()

            processed_files = []
            errors = []

            @retry_database_operation
            def save_metadata(file_path, size):
                with pool.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT OR REPLACE INTO file_metadata VALUES (?, ?, 1)",
                        (file_path, size),
                    )
                    conn.commit()

            def process_file(file_id):
                try:
                    file_path = f"/path/to/file{file_id}.txt"

                    # Check cache for file size
                    size = cache.get(file_path)
                    if size is None:
                        size = file_id * 1024  # Simulated size
                        cache.set(file_path, size)

                    # Save to database with retry
                    save_metadata(file_path, size)

                    processed_files.append(file_id)
                    tracker.update(increment=1, current_item=file_path)

                except Exception as e:
                    errors.append(e)
                    tracker.fail(str(e))

            # Process files
            for i in range(20):
                process_file(i)

            tracker.complete()

            # Verify
            assert len(errors) == 0
            assert len(processed_files) == 20

            progress = tracker.get_progress()
            assert progress.status.value == "completed"
            assert progress.completed_items == 20
            assert progress.percentage == 100.0

            # Verify database
            with pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM file_metadata WHERE processed = 1")
                count = cursor.fetchone()[0]
                assert count == 20

            # Verify cache
            assert cache.get("/path/to/file5.txt") == 5 * 1024

            pool.close_all()
        finally:
            db_path.unlink()
