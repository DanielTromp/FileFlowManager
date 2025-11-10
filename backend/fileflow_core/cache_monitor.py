"""
Cache monitoring and statistics for FileFlow Manager.

Provides monitoring for:
- LRU cache hit rates
- Query cache effectiveness
- Checksum cache performance
- Connection pool utilization
"""

from dataclasses import dataclass
from typing import Dict, Optional

from fileflow_core.observability import MetricsCollector, StructuredLogger, get_logger, get_metrics


@dataclass
class CacheStats:
    """Cache statistics snapshot."""

    name: str
    hits: int
    misses: int
    hit_rate: float
    size: int
    capacity: int
    evictions: int = 0


class CacheMonitor:
    """
    Monitor cache performance and effectiveness.

    Tracks metrics for all cache types:
    - LRU caches
    - Query caches
    - Checksum caches
    - Connection pools
    """

    def __init__(
        self,
        metrics: Optional[MetricsCollector] = None,
        logger: Optional[StructuredLogger] = None,
    ):
        """
        Initialize cache monitor.

        Args:
            metrics: Optional metrics collector
            logger: Optional structured logger
        """
        self.metrics = metrics or get_metrics()
        self.logger = logger or get_logger(__name__)

    def record_cache_access(
        self, cache_name: str, hit: bool, operation: Optional[str] = None
    ) -> None:
        """
        Record a cache access (hit or miss).

        Args:
            cache_name: Name of the cache
            hit: Whether it was a cache hit (True) or miss (False)
            operation: Optional operation name
        """
        labels = {"cache": cache_name}
        if operation:
            labels["operation"] = operation

        if hit:
            self.metrics.increment("cache_hits_total", labels=labels)
        else:
            self.metrics.increment("cache_misses_total", labels=labels)

        self.metrics.increment("cache_accesses_total", labels=labels)

    def record_cache_eviction(self, cache_name: str) -> None:
        """
        Record a cache eviction.

        Args:
            cache_name: Name of the cache
        """
        self.metrics.increment("cache_evictions_total", labels={"cache": cache_name})

    def record_cache_size(self, cache_name: str, size: int, capacity: int) -> None:
        """
        Record current cache size.

        Args:
            cache_name: Name of the cache
            size: Current cache size
            capacity: Cache capacity
        """
        self.metrics.set_gauge("cache_size", size, labels={"cache": cache_name})
        self.metrics.set_gauge("cache_capacity", capacity, labels={"cache": cache_name})
        self.metrics.set_gauge(
            "cache_utilization",
            size / capacity if capacity > 0 else 0,
            labels={"cache": cache_name},
        )

    def get_cache_stats(self, cache_name: str) -> Optional[CacheStats]:
        """
        Get statistics for a specific cache.

        Args:
            cache_name: Name of the cache

        Returns:
            CacheStats if available, None otherwise
        """
        labels = {"cache": cache_name}

        hits = self.metrics.get_counter("cache_hits_total", labels)
        misses = self.metrics.get_counter("cache_misses_total", labels)
        total = hits + misses

        if total == 0:
            return None

        hit_rate = hits / total
        size = int(self.metrics.get_gauge("cache_size", labels) or 0)
        capacity = int(self.metrics.get_gauge("cache_capacity", labels) or 0)
        evictions = int(self.metrics.get_counter("cache_evictions_total", labels) or 0)

        return CacheStats(
            name=cache_name,
            hits=int(hits),
            misses=int(misses),
            hit_rate=hit_rate,
            size=size,
            capacity=capacity,
            evictions=evictions,
        )

    def get_all_cache_stats(self) -> Dict[str, CacheStats]:
        """
        Get statistics for all monitored caches.

        Returns:
            Dictionary of cache stats by cache name
        """
        all_metrics = self.metrics.get_all_metrics()
        cache_names = set()

        # Extract cache names from counters
        for key in all_metrics["counters"].keys():
            if "cache=" in key:
                # Parse cache name from label
                start = key.find("cache=") + 6
                end = key.find(",", start) if "," in key[start:] else key.find("}", start)
                cache_name = key[start:end]
                cache_names.add(cache_name)

        stats = {}
        for cache_name in cache_names:
            cache_stats = self.get_cache_stats(cache_name)
            if cache_stats:
                stats[cache_name] = cache_stats

        return stats

    def log_cache_performance(self, cache_name: str, warn_threshold: float = 0.5) -> None:
        """
        Log cache performance statistics.

        Args:
            cache_name: Name of the cache
            warn_threshold: Warn if hit rate is below this threshold (default: 0.5)
        """
        stats = self.get_cache_stats(cache_name)
        if not stats:
            self.logger.debug(f"No statistics available for cache: {cache_name}")
            return

        if stats.hit_rate < warn_threshold:
            self.logger.warning(
                f"Low cache hit rate for {cache_name}",
                hit_rate=f"{stats.hit_rate:.2%}",
                hits=stats.hits,
                misses=stats.misses,
                size=stats.size,
                capacity=stats.capacity,
            )
        else:
            self.logger.info(
                f"Cache performance for {cache_name}",
                hit_rate=f"{stats.hit_rate:.2%}",
                hits=stats.hits,
                misses=stats.misses,
                size=stats.size,
                capacity=stats.capacity,
            )

    def format_cache_report(self, stats: Optional[Dict[str, CacheStats]] = None) -> str:
        """
        Format cache statistics as a readable report.

        Args:
            stats: Optional specific stats to report, otherwise all caches

        Returns:
            Formatted cache report string
        """
        if stats is None:
            stats = self.get_all_cache_stats()

        if not stats:
            return "No cache statistics available"

        lines = []
        lines.append("=" * 80)
        lines.append("CACHE PERFORMANCE REPORT")
        lines.append("=" * 80)
        lines.append("")

        for cache_name, cache_stats in sorted(stats.items()):
            lines.append(f"Cache: {cache_name}")
            lines.append(f"  Hit Rate:    {cache_stats.hit_rate:.2%}")
            lines.append(f"  Hits:        {cache_stats.hits:,}")
            lines.append(f"  Misses:      {cache_stats.misses:,}")
            lines.append(f"  Size:        {cache_stats.size:,} / {cache_stats.capacity:,}")
            lines.append(
                f"  Utilization: {cache_stats.size / cache_stats.capacity * 100:.1f}%"
                if cache_stats.capacity > 0
                else "  Utilization: N/A"
            )
            if cache_stats.evictions > 0:
                lines.append(f"  Evictions:   {cache_stats.evictions:,}")
            lines.append("")

        lines.append("=" * 80)
        return "\n".join(lines)


# Convenience functions for common cache types


def monitor_lru_cache(cache_name: str, monitor: Optional[CacheMonitor] = None):
    """
    Decorator to monitor LRU cache operations.

    Args:
        cache_name: Name to identify the cache
        monitor: Optional CacheMonitor instance

    Example:
        @monitor_lru_cache("destination_cache")
        def get_destination(key):
            return cache.get(key)
    """
    if monitor is None:
        monitor = CacheMonitor()

    def decorator(func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            # Assume None result means cache miss
            monitor.record_cache_access(cache_name, hit=(result is not None))
            return result

        return wrapper

    return decorator


def track_cache_operation(
    cache_name: str, operation: str, monitor: Optional[CacheMonitor] = None
):
    """
    Decorator to track cache operations with detailed context.

    Args:
        cache_name: Name to identify the cache
        operation: Operation name (e.g., "get", "set", "invalidate")
        monitor: Optional CacheMonitor instance

    Example:
        @track_cache_operation("query_cache", "get")
        def get_query(sql, params):
            return query_cache.get(sql, params)
    """
    if monitor is None:
        monitor = CacheMonitor()

    def decorator(func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            # Track access
            monitor.record_cache_access(cache_name, hit=(result is not None), operation=operation)
            return result

        return wrapper

    return decorator
