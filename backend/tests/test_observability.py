"""
Tests for observability infrastructure.

Tests metrics collection, structured logging, and monitoring decorators.
"""

import time

import pytest

from fileflow_core.observability import (
    MetricsCollector,
    StructuredLogger,
    get_logger,
    get_metrics,
    monitored,
)


@pytest.fixture(autouse=True)
def reset_global_metrics():
    """Reset global metrics before each test."""
    metrics = get_metrics()
    metrics.reset()
    yield
    metrics.reset()


class TestMetricsCollector:
    """Test MetricsCollector functionality."""

    def test_counter_increment(self):
        """Test counter increments."""
        metrics = MetricsCollector()
        metrics.increment("test_counter")
        metrics.increment("test_counter", 2.0)

        assert metrics.get_counter("test_counter") == 3.0

    def test_counter_with_labels(self):
        """Test counters with labels."""
        metrics = MetricsCollector()
        metrics.increment("requests", labels={"method": "GET"})
        metrics.increment("requests", labels={"method": "POST"})
        metrics.increment("requests", labels={"method": "GET"})

        assert metrics.get_counter("requests", labels={"method": "GET"}) == 2.0
        assert metrics.get_counter("requests", labels={"method": "POST"}) == 1.0

    def test_gauge_set(self):
        """Test gauge values."""
        metrics = MetricsCollector()
        metrics.set_gauge("temperature", 25.5)
        assert metrics.get_gauge("temperature") == 25.5

        metrics.set_gauge("temperature", 30.0)
        assert metrics.get_gauge("temperature") == 30.0

    def test_histogram_observe(self):
        """Test histogram observations."""
        metrics = MetricsCollector()
        values = [1.0, 2.0, 3.0, 4.0, 5.0]

        for value in values:
            metrics.observe("response_time", value)

        stats = metrics.get_histogram_stats("response_time")
        assert stats.count == 5
        assert stats.min == 1.0
        assert stats.max == 5.0
        assert stats.mean == 3.0
        assert stats.p50 == 3.0

    def test_timer_record(self):
        """Test timer recording."""
        metrics = MetricsCollector()

        metrics.record_time("operation", 0.1)
        metrics.record_time("operation", 0.2)
        metrics.record_time("operation", 0.3)

        stats = metrics.get_timer_stats("operation")
        assert stats.count == 3
        assert stats.min == 0.1
        assert stats.max == 0.3
        assert abs(stats.mean - 0.2) < 0.01

    def test_timer_context_manager(self):
        """Test timer context manager."""
        metrics = MetricsCollector()

        with metrics.time("operation"):
            time.sleep(0.01)

        stats = metrics.get_timer_stats("operation")
        assert stats.count == 1
        assert stats.mean > 0.01
        assert stats.mean < 0.1

    def test_get_all_metrics(self):
        """Test getting all metrics."""
        metrics = MetricsCollector()
        metrics.increment("counter1", 5)
        metrics.set_gauge("gauge1", 10.0)
        metrics.observe("hist1", 1.0)
        metrics.record_time("timer1", 0.5)

        all_metrics = metrics.get_all_metrics()

        assert "counter1" in all_metrics["counters"]
        assert "gauge1" in all_metrics["gauges"]
        assert "hist1" in all_metrics["histograms"]
        assert "timer1" in all_metrics["timers"]

    def test_reset(self):
        """Test metrics reset."""
        metrics = MetricsCollector()
        metrics.increment("test", 10)
        metrics.set_gauge("test_gauge", 20)

        metrics.reset()

        assert metrics.get_counter("test") == 0.0
        assert metrics.get_gauge("test_gauge") is None

    def test_thread_safety(self):
        """Test thread-safe operations."""
        import threading

        metrics = MetricsCollector()

        def increment_counter():
            for _ in range(100):
                metrics.increment("thread_counter")

        threads = [threading.Thread(target=increment_counter) for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # All increments should be recorded
        assert metrics.get_counter("thread_counter") == 1000.0


class TestStructuredLogger:
    """Test StructuredLogger functionality."""

    def test_logger_creation(self):
        """Test logger creation."""
        logger = StructuredLogger("test_logger")
        assert logger.name == "test_logger"
        assert logger.logger.name == "test_logger"

    def test_logger_with_metrics(self):
        """Test logger with automatic metrics tracking."""
        metrics = MetricsCollector()
        logger = StructuredLogger("test_logger", metrics=metrics)

        # Log warning and error
        logger.warning("Test warning")
        logger.error("Test error")

        # Metrics should be tracked (warnings have exact match, errors include error_type)
        warnings = metrics.get_counter("log_warnings_total", labels={"logger": "test_logger"})
        assert warnings == 1.0

        # Errors are tracked with error_type label, so check all metrics
        all_metrics = metrics.get_all_metrics()
        error_metrics = [k for k in all_metrics["counters"].keys() if "log_errors_total" in k and "test_logger" in k]
        assert len(error_metrics) >= 1  # At least one error metric was recorded

    def test_logger_error_with_exception(self):
        """Test logging errors with exceptions."""
        metrics = MetricsCollector()
        logger = StructuredLogger("test_logger", metrics=metrics)

        try:
            raise ValueError("Test error")
        except ValueError as e:
            logger.error("Error occurred", error=e)

        # Error should be tracked with type
        error_count = metrics.get_counter(
            "log_errors_total",
            labels={"logger": "test_logger", "error_type": "ValueError"},
        )
        assert error_count == 1.0


class TestMonitoredDecorator:
    """Test @monitored decorator."""

    def test_monitored_success(self):
        """Test monitoring successful operations."""
        metrics = MetricsCollector()

        @monitored("test_op", metrics)
        def successful_operation():
            return "success"

        result = successful_operation()

        assert result == "success"
        assert metrics.get_counter("test_op_total") == 1.0
        assert metrics.get_counter("test_op_success") == 1.0

    def test_monitored_error(self):
        """Test monitoring failed operations."""
        metrics = MetricsCollector()

        @monitored("test_op", metrics)
        def failing_operation():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            failing_operation()

        assert metrics.get_counter("test_op_total") == 1.0
        assert metrics.get_counter("test_op_errors", labels={"error_type": "ValueError"}) == 1.0

    def test_monitored_duration(self):
        """Test monitoring operation duration."""
        metrics = MetricsCollector()

        @monitored("test_op", metrics, track_duration=True)
        def timed_operation():
            time.sleep(0.01)
            return "done"

        timed_operation()

        stats = metrics.get_timer_stats("test_op_duration")
        assert stats is not None
        assert stats.count == 1
        assert stats.mean > 0.01


class TestGlobalMetrics:
    """Test global metrics instance."""

    def test_get_metrics_singleton(self):
        """Test global metrics singleton."""
        metrics1 = get_metrics()
        metrics2 = get_metrics()

        assert metrics1 is metrics2

    def test_get_logger(self):
        """Test get_logger utility."""
        logger = get_logger("test_module")

        assert isinstance(logger, StructuredLogger)
        assert logger.name == "test_module"
        assert logger.metrics is not None
