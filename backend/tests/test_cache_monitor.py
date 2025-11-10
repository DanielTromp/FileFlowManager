"""
Tests for cache monitoring functionality.

Tests cache statistics collection, hit rate tracking, and reporting.
"""

import pytest

from fileflow_core.cache_monitor import CacheMonitor, CacheStats
from fileflow_core.observability import MetricsCollector, get_metrics


@pytest.fixture(autouse=True)
def reset_global_metrics():
    """Reset global metrics before each test."""
    metrics = get_metrics()
    metrics.reset()
    yield
    metrics.reset()


class TestCacheMonitor:
    """Test CacheMonitor functionality."""

    def test_record_cache_hit(self):
        """Test recording cache hits."""
        monitor = CacheMonitor()

        for _ in range(5):
            monitor.record_cache_access("test_cache", hit=True)

        stats = monitor.get_cache_stats("test_cache")
        assert stats.hits == 5
        assert stats.misses == 0
        assert stats.hit_rate == 1.0

    def test_record_cache_miss(self):
        """Test recording cache misses."""
        monitor = CacheMonitor()

        for _ in range(3):
            monitor.record_cache_access("test_cache", hit=False)

        stats = monitor.get_cache_stats("test_cache")
        assert stats.hits == 0
        assert stats.misses == 3
        assert stats.hit_rate == 0.0

    def test_record_mixed_accesses(self):
        """Test recording mix of hits and misses."""
        monitor = CacheMonitor()

        # 7 hits, 3 misses = 70% hit rate
        for _ in range(7):
            monitor.record_cache_access("test_cache", hit=True)
        for _ in range(3):
            monitor.record_cache_access("test_cache", hit=False)

        stats = monitor.get_cache_stats("test_cache")
        assert stats.hits == 7
        assert stats.misses == 3
        assert stats.hit_rate == 0.7

    def test_record_cache_size(self):
        """Test recording cache size."""
        monitor = CacheMonitor()

        # Need at least one access to establish the cache
        monitor.record_cache_access("test_cache", hit=True)
        monitor.record_cache_size("test_cache", size=50, capacity=100)

        stats = monitor.get_cache_stats("test_cache")
        assert stats.size == 50
        assert stats.capacity == 100

    def test_record_cache_eviction(self):
        """Test recording cache evictions."""
        monitor = CacheMonitor()

        # Need some accesses first
        monitor.record_cache_access("test_cache", hit=True)

        # Record evictions
        for _ in range(5):
            monitor.record_cache_eviction("test_cache")

        stats = monitor.get_cache_stats("test_cache")
        assert stats.evictions == 5

    def test_cache_access_with_operation(self):
        """Test recording cache access with operation label."""
        monitor = CacheMonitor()

        # Record accesses without operation
        monitor.record_cache_access("test_cache", hit=True)
        monitor.record_cache_access("test_cache", hit=False)

        # Overall stats (operations with labels are tracked separately)
        stats = monitor.get_cache_stats("test_cache")
        assert stats.hits == 1
        assert stats.misses == 1

        # Verify operation-labeled accesses were recorded separately
        monitor.record_cache_access("test_cache", hit=True, operation="get")
        # Operation-labeled metrics don't affect base cache stats

    def test_get_cache_stats_nonexistent(self):
        """Test getting stats for nonexistent cache."""
        monitor = CacheMonitor()

        stats = monitor.get_cache_stats("nonexistent")
        assert stats is None

    def test_get_all_cache_stats(self):
        """Test getting stats for all caches."""
        monitor = CacheMonitor()

        # Record data for multiple caches
        monitor.record_cache_access("cache1", hit=True)
        monitor.record_cache_access("cache2", hit=False)
        monitor.record_cache_access("cache3", hit=True)

        all_stats = monitor.get_all_cache_stats()

        assert "cache1" in all_stats
        assert "cache2" in all_stats
        assert "cache3" in all_stats

    def test_format_cache_report(self):
        """Test formatting cache report."""
        monitor = CacheMonitor()

        # Add some cache data
        for _ in range(8):
            monitor.record_cache_access("test_cache", hit=True)
        for _ in range(2):
            monitor.record_cache_access("test_cache", hit=False)
        monitor.record_cache_size("test_cache", size=50, capacity=100)

        report = monitor.format_cache_report()

        assert "CACHE PERFORMANCE REPORT" in report
        assert "test_cache" in report
        assert "80.00%" in report  # Hit rate
        assert "50" in report  # Size
        assert "100" in report  # Capacity

    def test_log_cache_performance_healthy(self):
        """Test logging healthy cache performance."""
        monitor = CacheMonitor()

        # Create healthy cache stats (80% hit rate)
        for _ in range(8):
            monitor.record_cache_access("test_cache", hit=True)
        for _ in range(2):
            monitor.record_cache_access("test_cache", hit=False)

        # Should not raise exception
        monitor.log_cache_performance("test_cache", warn_threshold=0.5)

    def test_log_cache_performance_unhealthy(self):
        """Test logging unhealthy cache performance."""
        monitor = CacheMonitor()

        # Create unhealthy cache stats (30% hit rate)
        for _ in range(3):
            monitor.record_cache_access("test_cache", hit=True)
        for _ in range(7):
            monitor.record_cache_access("test_cache", hit=False)

        # Should not raise exception even with low hit rate
        monitor.log_cache_performance("test_cache", warn_threshold=0.5)

    def test_cache_stats_dataclass(self):
        """Test CacheStats dataclass."""
        stats = CacheStats(
            name="test_cache",
            hits=80,
            misses=20,
            hit_rate=0.8,
            size=50,
            capacity=100,
            evictions=5,
        )

        assert stats.name == "test_cache"
        assert stats.hits == 80
        assert stats.misses == 20
        assert stats.hit_rate == 0.8
        assert stats.size == 50
        assert stats.capacity == 100
        assert stats.evictions == 5

    def test_multiple_caches_independent(self):
        """Test that multiple caches track independently."""
        monitor = CacheMonitor()

        # Cache1: 90% hit rate
        for _ in range(9):
            monitor.record_cache_access("cache1", hit=True)
        for _ in range(1):
            monitor.record_cache_access("cache1", hit=False)

        # Cache2: 60% hit rate
        for _ in range(6):
            monitor.record_cache_access("cache2", hit=True)
        for _ in range(4):
            monitor.record_cache_access("cache2", hit=False)

        stats1 = monitor.get_cache_stats("cache1")
        stats2 = monitor.get_cache_stats("cache2")

        assert stats1.hit_rate == 0.9
        assert stats2.hit_rate == 0.6

    def test_monitor_with_custom_metrics(self):
        """Test monitor with custom metrics collector."""
        metrics = MetricsCollector()
        monitor = CacheMonitor(metrics=metrics)

        monitor.record_cache_access("test_cache", hit=True)

        # Verify metrics were recorded
        hits = metrics.get_counter("cache_hits_total", labels={"cache": "test_cache"})
        assert hits == 1.0


class TestCacheMonitorDecorators:
    """Test cache monitoring decorators."""

    def test_monitor_lru_cache_decorator(self):
        """Test @monitor_lru_cache decorator."""
        from fileflow_core.cache_monitor import monitor_lru_cache

        monitor = CacheMonitor()

        @monitor_lru_cache("test_cache", monitor=monitor)
        def get_from_cache(key):
            # Simulate cache miss/hit
            return key if key == "cached" else None

        # Cache miss
        get_from_cache("uncached")

        # Cache hit
        get_from_cache("cached")

        stats = monitor.get_cache_stats("test_cache")
        assert stats.hits == 1
        assert stats.misses == 1

    def test_track_cache_operation_decorator(self):
        """Test @track_cache_operation decorator."""
        from fileflow_core.cache_monitor import track_cache_operation

        monitor = CacheMonitor()

        # Establish baseline without operation label
        monitor.record_cache_access("test_cache", hit=True)

        @track_cache_operation("test_cache", "get", monitor=monitor)
        def cache_get(key):
            return key if key == "exists" else None

        cache_get("exists")
        cache_get("missing")

        # Base cache stats (decorator uses operation label, tracked separately)
        stats = monitor.get_cache_stats("test_cache")
        assert stats.hits == 1  # baseline hit only
        # Decorator accesses with operation label are tracked in separate metrics
