"""
Caching utilities for performance optimization.

Provides in-memory caching, connection pooling, and cache invalidation
strategies for frequently accessed data.
"""

import functools
import hashlib
import logging
import sqlite3
import threading
import time
from collections import OrderedDict
from collections.abc import Callable, Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Set, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class LRUCache:
    """
    Thread-safe Least Recently Used (LRU) cache.

    Automatically evicts least recently used items when capacity is reached.
    """

    def __init__(self, capacity: int = 1000, ttl: float | None = None):
        """
        Initialize LRU cache.

        Args:
            capacity: Maximum number of items to cache
            ttl: Time-to-live in seconds (None for no expiration)
        """
        self.capacity = capacity
        self.ttl = ttl
        self._cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Any | None:
        """
        Get item from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None

            value, timestamp = self._cache[key]

            # Check TTL
            if self.ttl and (time.time() - timestamp) > self.ttl:
                del self._cache[key]
                self._misses += 1
                return None

            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self._hits += 1
            return value

    def set(self, key: str, value: Any) -> None:
        """
        Set item in cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        with self._lock:
            # Update existing or add new
            if key in self._cache:
                self._cache.move_to_end(key)

            self._cache[key] = (value, time.time())

            # Evict if over capacity
            if len(self._cache) > self.capacity:
                self._cache.popitem(last=False)  # Remove oldest

    def invalidate(self, key: str) -> bool:
        """
        Invalidate a cache entry.

        Args:
            key: Cache key to invalidate

        Returns:
            True if key was in cache, False otherwise
        """
        with self._lock:
            return self._cache.pop(key, None) is not None

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total > 0 else 0

            return {
                "size": len(self._cache),
                "capacity": self.capacity,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(hit_rate, 2),
            }


class ConnectionPool:
    """
    Database connection pool for SQLite.

    Maintains a pool of reusable database connections to avoid
    the overhead of opening/closing connections repeatedly.
    """

    def __init__(self, db_path: Path | str, pool_size: int = 5, timeout: float = 30.0):
        """
        Initialize connection pool.

        Args:
            db_path: Path to SQLite database
            pool_size: Maximum number of connections in pool
            timeout: Timeout in seconds for acquiring connection
        """
        self.db_path = Path(db_path)
        self.pool_size = pool_size
        self.timeout = timeout
        self._connections: list[sqlite3.Connection] = []
        self._available: list[sqlite3.Connection] = []
        self._in_use: set[sqlite3.Connection] = set()
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)

    def _create_connection(self) -> sqlite3.Connection:
        """Create a new database connection."""
        conn = sqlite3.connect(
            str(self.db_path), check_same_thread=False, timeout=self.timeout
        )
        # Enable WAL mode for better concurrency
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Get a connection from the pool (context manager).

        Yields:
            Database connection

        Example:
            with pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM table")
        """
        conn = self._acquire()
        try:
            yield conn
        finally:
            self._release(conn)

    def _acquire(self) -> sqlite3.Connection:
        """Acquire a connection from the pool."""
        with self._condition:
            # Wait for available connection
            deadline = time.time() + self.timeout
            while not self._available and len(self._connections) >= self.pool_size:
                timeout_remaining = deadline - time.time()
                if timeout_remaining <= 0:
                    raise TimeoutError("Timeout waiting for database connection")
                self._condition.wait(timeout=timeout_remaining)

            # Reuse available connection
            if self._available:
                conn = self._available.pop()
            # Or create new connection
            elif len(self._connections) < self.pool_size:
                conn = self._create_connection()
                self._connections.append(conn)
            else:
                raise RuntimeError("Connection pool exhausted")

            self._in_use.add(conn)
            return conn

    def _release(self, conn: sqlite3.Connection) -> None:
        """Release a connection back to the pool."""
        with self._condition:
            if conn not in self._in_use:
                logger.warning("Releasing connection not in use")
                return

            self._in_use.remove(conn)
            self._available.append(conn)
            self._condition.notify()

    def close_all(self) -> None:
        """Close all connections in the pool."""
        with self._lock:
            for conn in self._connections:
                try:
                    conn.close()
                except Exception as e:
                    logger.error(f"Error closing connection: {e}")

            self._connections.clear()
            self._available.clear()
            self._in_use.clear()

    def get_stats(self) -> dict[str, Any]:
        """Get pool statistics."""
        with self._lock:
            return {
                "pool_size": self.pool_size,
                "total_connections": len(self._connections),
                "available": len(self._available),
                "in_use": len(self._in_use),
            }


def cached(
    cache: LRUCache | None = None,
    ttl: float | None = None,
    key_func: Callable[..., str] | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to cache function results.

    Args:
        cache: LRU cache instance (creates new one if None)
        ttl: Time-to-live for cache entries (overrides cache TTL)
        key_func: Custom function to generate cache key from arguments

    Returns:
        Decorated function

    Example:
        @cached(ttl=60.0)
        def expensive_operation(arg1, arg2):
            # Expensive computation
            return result
    """
    if cache is None:
        cache = LRUCache(capacity=1000, ttl=ttl)

    def default_key_func(*args: Any, **kwargs: Any) -> str:
        """Generate cache key from function arguments."""
        key_parts = [str(arg) for arg in args]
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        key_str = ":".join(key_parts)
        return hashlib.md5(key_str.encode()).hexdigest()

    actual_key_func = key_func or default_key_func

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Generate cache key
            cache_key = f"{func.__module__}.{func.__name__}:{actual_key_func(*args, **kwargs)}"

            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result

            # Compute result
            logger.debug(f"Cache miss for {func.__name__}")
            result = func(*args, **kwargs)

            # Store in cache
            cache.set(cache_key, result)

            return result

        # Add cache management methods to wrapper
        wrapper.cache = cache  # type: ignore
        wrapper.invalidate = lambda *args, **kwargs: cache.invalidate(  # type: ignore
            f"{func.__module__}.{func.__name__}:{actual_key_func(*args, **kwargs)}"
        )
        wrapper.clear_cache = cache.clear  # type: ignore

        return wrapper

    return decorator


class QueryCache:
    """
    Cache for database query results.

    Automatically invalidates cache based on table modifications.
    """

    def __init__(self, capacity: int = 500, ttl: float = 300.0):
        """
        Initialize query cache.

        Args:
            capacity: Maximum number of cached queries
            ttl: Time-to-live in seconds (default: 5 minutes)
        """
        self._cache = LRUCache(capacity=capacity, ttl=ttl)
        self._table_versions: dict[str, int] = {}
        self._lock = threading.Lock()

    def get(self, query: str, params: tuple[Any, ...] = ()) -> Any | None:
        """
        Get cached query result.

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            Cached result or None
        """
        cache_key = self._make_key(query, params)
        return self._cache.get(cache_key)

    def set(self, query: str, params: tuple[Any, ...], result: Any) -> None:
        """
        Cache query result.

        Args:
            query: SQL query
            params: Query parameters
            result: Query result to cache
        """
        cache_key = self._make_key(query, params)
        self._cache.set(cache_key, result)

    def invalidate_table(self, table_name: str) -> None:
        """
        Invalidate all queries for a table.

        Args:
            table_name: Table that was modified
        """
        with self._lock:
            # Increment table version
            self._table_versions[table_name] = (
                self._table_versions.get(table_name, 0) + 1
            )

        # Clear entire cache (could be more sophisticated)
        self._cache.clear()
        logger.debug(f"Invalidated cache for table: {table_name}")

    def _make_key(self, query: str, params: tuple[Any, ...]) -> str:
        """Generate cache key from query and parameters."""
        # Extract table names from query (simple approach)
        tables = self._extract_tables(query)

        # Include table versions in key
        table_versions = [
            (table, self._table_versions.get(table, 0)) for table in tables  # type: ignore[attr-defined]
        ]

        # Generate key
        key_data = f"{query}:{params}:{table_versions}"
        return hashlib.md5(key_data.encode()).hexdigest()

    @staticmethod
    def _extract_tables(query: str) -> Set[str]:
        """Extract table names from SQL query (simplified)."""
        import re

        query_lower = query.lower()
        tables: Set[str] = set()

        # Find FROM clauses
        from_pattern = r"from\s+([a-z_][a-z0-9_]*)"
        tables.update(re.findall(from_pattern, query_lower))

        # Find JOIN clauses
        join_pattern = r"join\s+([a-z_][a-z0-9_]*)"
        tables.update(re.findall(join_pattern, query_lower))

        # Find INSERT/UPDATE/DELETE
        insert_pattern = r"insert\s+into\s+([a-z_][a-z0-9_]*)"
        update_pattern = r"update\s+([a-z_][a-z0-9_]*)"
        delete_pattern = r"delete\s+from\s+([a-z_][a-z0-9_]*)"

        tables.update(re.findall(insert_pattern, query_lower))
        tables.update(re.findall(update_pattern, query_lower))
        tables.update(re.findall(delete_pattern, query_lower))

        return tables

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        return {
            **self._cache.get_stats(),
            "tracked_tables": len(self._table_versions),
        }
