"""
Unit tests for caching and connection pooling.

Tests the caching infrastructure including LRUCache, ConnectionPool,
cached decorator, and QueryCache.
"""

import sqlite3
import tempfile
import threading
import time
from pathlib import Path

from fileflow_core.cache import (
    ConnectionPool,
    LRUCache,
    QueryCache,
    cached,
)


class TestLRUCache:
    """Test LRUCache class."""

    def test_basic_cache_operations(self):
        """Test basic cache get and set."""
        cache = LRUCache(capacity=10)

        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        cache.set("key2", "value2")
        assert cache.get("key2") == "value2"

    def test_cache_miss(self):
        """Test cache miss returns None."""
        cache = LRUCache()
        assert cache.get("nonexistent") is None

    def test_cache_capacity_eviction(self):
        """Test LRU eviction when capacity is reached."""
        cache = LRUCache(capacity=3)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        cache.set("key4", "value4")  # Should evict key1

        assert cache.get("key1") is None  # Evicted
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"

    def test_lru_ordering(self):
        """Test that least recently used items are evicted first."""
        cache = LRUCache(capacity=3)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # Access key1 to make it more recently used
        _ = cache.get("key1")

        # Add key4, should evict key2 (least recently used)
        cache.set("key4", "value4")

        assert cache.get("key1") == "value1"  # Still there
        assert cache.get("key2") is None  # Evicted
        assert cache.get("key3") == "value3"  # Still there
        assert cache.get("key4") == "value4"  # New item

    def test_cache_ttl(self):
        """Test time-to-live expiration."""
        cache = LRUCache(capacity=10, ttl=0.1)  # 100ms TTL

        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        time.sleep(0.15)  # Wait for expiration

        assert cache.get("key1") is None  # Expired

    def test_cache_update_existing(self):
        """Test updating existing cache entry."""
        cache = LRUCache(capacity=10)

        cache.set("key1", "value1")
        cache.set("key1", "value2")  # Update

        assert cache.get("key1") == "value2"

    def test_cache_invalidate(self):
        """Test cache invalidation."""
        cache = LRUCache(capacity=10)

        cache.set("key1", "value1")
        assert cache.invalidate("key1") is True
        assert cache.get("key1") is None

        assert cache.invalidate("nonexistent") is False

    def test_cache_clear(self):
        """Test clearing all cache entries."""
        cache = LRUCache(capacity=10)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        cache.clear()

        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert cache.get("key3") is None

    def test_cache_stats(self):
        """Test cache statistics."""
        cache = LRUCache(capacity=10)

        # Initial stats
        stats = cache.get_stats()
        assert stats["size"] == 0
        assert stats["capacity"] == 10
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["hit_rate"] == 0

        # Add items
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        # Hit
        _ = cache.get("key1")

        # Miss
        _ = cache.get("key3")

        stats = cache.get_stats()
        assert stats["size"] == 2
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 50.0

    def test_cache_thread_safety(self):
        """Test cache is thread-safe."""
        cache = LRUCache(capacity=100)
        errors = []

        def worker(thread_id):
            try:
                for i in range(100):
                    cache.set(f"key{thread_id}_{i}", f"value{thread_id}_{i}")
                    _ = cache.get(f"key{thread_id}_{i}")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0


class TestConnectionPool:
    """Test ConnectionPool class."""

    def test_create_pool(self):
        """Test creating a connection pool."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = Path(tmp.name)

        try:
            pool = ConnectionPool(db_path, pool_size=3)

            # Should be able to get connection
            with pool.get_connection() as conn:
                assert isinstance(conn, sqlite3.Connection)

            pool.close_all()
        finally:
            db_path.unlink()

    def test_connection_pool_reuse(self):
        """Test that connections are reused."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = Path(tmp.name)

        try:
            pool = ConnectionPool(db_path, pool_size=2)

            # Get and release connections
            with pool.get_connection() as conn1:
                conn1_id = id(conn1)

            with pool.get_connection() as conn2:
                conn2_id = id(conn2)

            # Should get the same connection object back
            assert conn1_id == conn2_id

            pool.close_all()
        finally:
            db_path.unlink()

    def test_pool_max_connections(self):
        """Test pool respects max connection limit."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = Path(tmp.name)

        try:
            pool = ConnectionPool(db_path, pool_size=2)

            # Acquire all connections
            conn1 = pool._acquire()
            conn2 = pool._acquire()

            # Pool should be exhausted
            stats = pool.get_stats()
            assert stats["total_connections"] == 2
            assert stats["in_use"] == 2
            assert stats["available"] == 0

            pool._release(conn1)
            pool._release(conn2)
            pool.close_all()
        finally:
            db_path.unlink()

    def test_connection_pool_concurrent_access(self):
        """Test concurrent access to connection pool."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = Path(tmp.name)

        try:
            pool = ConnectionPool(db_path, pool_size=5)
            errors = []

            def worker():
                try:
                    with pool.get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("CREATE TABLE IF NOT EXISTS test (id INTEGER)")
                        cursor.execute("INSERT INTO test VALUES (1)")
                        conn.commit()
                except Exception as e:
                    errors.append(e)

            threads = [threading.Thread(target=worker) for _ in range(10)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            assert len(errors) == 0
            pool.close_all()
        finally:
            db_path.unlink()

    def test_pool_stats(self):
        """Test connection pool statistics."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = Path(tmp.name)

        try:
            pool = ConnectionPool(db_path, pool_size=3)

            # Initial stats
            stats = pool.get_stats()
            assert stats["pool_size"] == 3
            assert stats["total_connections"] == 0
            assert stats["available"] == 0
            assert stats["in_use"] == 0

            # Get a connection
            with pool.get_connection():
                stats = pool.get_stats()
                assert stats["total_connections"] == 1
                assert stats["in_use"] == 1
                assert stats["available"] == 0

            # After release
            stats = pool.get_stats()
            assert stats["total_connections"] == 1
            assert stats["in_use"] == 0
            assert stats["available"] == 1

            pool.close_all()
        finally:
            db_path.unlink()


class TestCachedDecorator:
    """Test cached decorator."""

    def test_decorator_caches_result(self):
        """Test decorator caches function results."""
        call_count = [0]

        @cached()
        def expensive_func(x):
            call_count[0] += 1
            return x * 2

        # First call
        result1 = expensive_func(5)
        assert result1 == 10
        assert call_count[0] == 1

        # Second call with same arg - should use cache
        result2 = expensive_func(5)
        assert result2 == 10
        assert call_count[0] == 1  # Not called again

        # Call with different arg
        result3 = expensive_func(10)
        assert result3 == 20
        assert call_count[0] == 2

    def test_decorator_with_kwargs(self):
        """Test decorator works with keyword arguments."""
        call_count = [0]

        @cached()
        def func_with_kwargs(a, b, c=10):
            call_count[0] += 1
            return a + b + c

        result1 = func_with_kwargs(1, 2, c=3)
        assert result1 == 6
        assert call_count[0] == 1

        result2 = func_with_kwargs(1, 2, c=3)
        assert result2 == 6
        assert call_count[0] == 1  # Cached

        result3 = func_with_kwargs(1, 2, c=4)
        assert result3 == 7
        assert call_count[0] == 2  # Different args

    def test_decorator_ttl(self):
        """Test decorator respects TTL."""
        call_count = [0]

        @cached(ttl=0.1)
        def func(x):
            call_count[0] += 1
            return x * 2

        result1 = func(5)
        assert result1 == 10
        assert call_count[0] == 1

        time.sleep(0.15)  # Wait for expiration

        result2 = func(5)
        assert result2 == 10
        assert call_count[0] == 2  # Called again after expiration

    def test_decorator_invalidate(self):
        """Test manual cache invalidation."""
        call_count = [0]

        @cached()
        def func(x):
            call_count[0] += 1
            return x * 2

        func(5)
        assert call_count[0] == 1

        # Invalidate
        func.invalidate(5)

        func(5)
        assert call_count[0] == 2  # Called again

    def test_decorator_clear_cache(self):
        """Test clearing entire cache."""
        call_count = [0]

        @cached()
        def func(x):
            call_count[0] += 1
            return x * 2

        func(5)
        func(10)
        assert call_count[0] == 2

        # Clear cache
        func.clear_cache()

        func(5)
        func(10)
        assert call_count[0] == 4  # Both called again


class TestQueryCache:
    """Test QueryCache class."""

    def test_basic_query_caching(self):
        """Test basic query caching."""
        cache = QueryCache()

        query = "SELECT * FROM users WHERE id = ?"
        params = (1,)
        result = [{"id": 1, "name": "Alice"}]

        # Set and get
        cache.set(query, params, result)
        cached_result = cache.get(query, params)

        assert cached_result == result

    def test_query_cache_miss(self):
        """Test cache miss returns None."""
        cache = QueryCache()

        result = cache.get("SELECT * FROM users", ())
        assert result is None

    def test_query_cache_different_params(self):
        """Test different params create different cache entries."""
        cache = QueryCache()

        query = "SELECT * FROM users WHERE id = ?"
        result1 = [{"id": 1, "name": "Alice"}]
        result2 = [{"id": 2, "name": "Bob"}]

        cache.set(query, (1,), result1)
        cache.set(query, (2,), result2)

        assert cache.get(query, (1,)) == result1
        assert cache.get(query, (2,)) == result2

    def test_invalidate_table(self):
        """Test table invalidation clears cache."""
        cache = QueryCache()

        query1 = "SELECT * FROM users WHERE id = ?"
        query2 = "SELECT * FROM posts WHERE user_id = ?"

        cache.set(query1, (1,), [{"id": 1}])
        cache.set(query2, (1,), [{"id": 1}])

        # Invalidate users table
        cache.invalidate_table("users")

        # Both should be cleared (simplified implementation clears all)
        assert cache.get(query1, (1,)) is None
        assert cache.get(query2, (1,)) is None

    def test_extract_tables_from_query(self):
        """Test table name extraction from SQL queries."""
        cache = QueryCache()

        # FROM clause
        tables = cache._extract_tables("SELECT * FROM users WHERE id = 1")
        assert "users" in tables

        # JOIN clause
        tables = cache._extract_tables("SELECT * FROM users JOIN posts ON users.id = posts.user_id")
        assert "users" in tables
        assert "posts" in tables

        # INSERT
        tables = cache._extract_tables("INSERT INTO users VALUES (1, 'Alice')")
        assert "users" in tables

        # UPDATE
        tables = cache._extract_tables("UPDATE users SET name = 'Bob' WHERE id = 1")
        assert "users" in tables

        # DELETE
        tables = cache._extract_tables("DELETE FROM users WHERE id = 1")
        assert "users" in tables

    def test_query_cache_stats(self):
        """Test query cache statistics."""
        cache = QueryCache()

        stats = cache.get_stats()
        assert "size" in stats
        assert "capacity" in stats
        assert "hits" in stats
        assert "misses" in stats

    def test_query_cache_ttl(self):
        """Test query cache respects TTL."""
        cache = QueryCache(ttl=0.1)

        query = "SELECT * FROM users WHERE id = ?"
        params = (1,)
        result = [{"id": 1}]

        cache.set(query, params, result)
        assert cache.get(query, params) == result

        time.sleep(0.15)  # Wait for expiration

        assert cache.get(query, params) is None


class TestCacheIntegration:
    """Integration tests for caching."""

    def test_cache_with_database_pool(self):
        """Test using cache with database connection pool."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = Path(tmp.name)

        try:
            pool = ConnectionPool(db_path, pool_size=2)
            query_cache = QueryCache()

            # Create table
            with pool.get_connection() as conn:
                conn.execute("CREATE TABLE users (id INTEGER, name TEXT)")
                conn.execute("INSERT INTO users VALUES (1, 'Alice')")
                conn.execute("INSERT INTO users VALUES (2, 'Bob')")
                conn.commit()

            # Query with caching
            query = "SELECT * FROM users WHERE id = ?"
            params = (1,)

            # First query - not cached
            cached_result = query_cache.get(query, params)
            assert cached_result is None

            # Execute query
            with pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                result = cursor.fetchall()
                query_cache.set(query, params, result)

            # Second query - cached
            cached_result = query_cache.get(query, params)
            assert cached_result == result

            pool.close_all()
        finally:
            db_path.unlink()

    def test_multiple_decorators_share_cache(self):
        """Test multiple decorated functions can share a cache."""
        shared_cache = LRUCache(capacity=100)
        call_counts = {"func1": 0, "func2": 0}

        @cached(cache=shared_cache)
        def func1(x):
            call_counts["func1"] += 1
            return x * 2

        @cached(cache=shared_cache)
        def func2(x):
            call_counts["func2"] += 1
            return x * 3

        func1(5)
        func1(5)  # Cached
        func2(5)
        func2(5)  # Cached

        assert call_counts["func1"] == 1
        assert call_counts["func2"] == 1

        # Both use same cache
        stats = shared_cache.get_stats()
        assert stats["size"] == 2  # Two different functions
