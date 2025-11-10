"""
Observability and monitoring infrastructure for FileFlow Manager.

Provides structured logging, metrics collection, and performance monitoring
to track the effectiveness of infrastructure optimizations.
"""

import logging
import time
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from threading import Lock
from typing import Any, Callable, Dict, List, Optional


class MetricType(Enum):
    """Types of metrics that can be collected."""

    COUNTER = "counter"  # Monotonically increasing value
    GAUGE = "gauge"  # Point-in-time value
    HISTOGRAM = "histogram"  # Distribution of values
    TIMER = "timer"  # Duration measurements


@dataclass
class MetricValue:
    """A single metric value with metadata."""

    name: str
    value: float
    metric_type: MetricType
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    unit: Optional[str] = None


@dataclass
class HistogramStats:
    """Statistics for histogram metrics."""

    count: int
    sum: float
    min: float
    max: float
    mean: float
    p50: float
    p95: float
    p99: float


class MetricsCollector:
    """
    Collect and aggregate metrics for monitoring.

    Thread-safe metrics collection with support for:
    - Counters (monotonically increasing)
    - Gauges (point-in-time values)
    - Histograms (value distributions)
    - Timers (duration measurements)
    """

    def __init__(self):
        """Initialize metrics collector."""
        self._lock = Lock()
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._timers: Dict[str, List[float]] = defaultdict(list)
        self._labels: Dict[str, Dict[str, str]] = {}

    def increment(
        self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Increment a counter metric.

        Args:
            name: Metric name
            value: Amount to increment by (default: 1.0)
            labels: Optional labels for the metric
        """
        with self._lock:
            key = self._make_key(name, labels)
            self._counters[key] += value
            if labels:
                self._labels[key] = labels

    def set_gauge(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Set a gauge metric to a specific value.

        Args:
            name: Metric name
            value: Value to set
            labels: Optional labels for the metric
        """
        with self._lock:
            key = self._make_key(name, labels)
            self._gauges[key] = value
            if labels:
                self._labels[key] = labels

    def observe(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Record a histogram observation.

        Args:
            name: Metric name
            value: Value to observe
            labels: Optional labels for the metric
        """
        with self._lock:
            key = self._make_key(name, labels)
            self._histograms[key].append(value)
            if labels:
                self._labels[key] = labels

    def record_time(
        self, name: str, duration: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Record a timer duration.

        Args:
            name: Metric name
            duration: Duration in seconds
            labels: Optional labels for the metric
        """
        with self._lock:
            key = self._make_key(name, labels)
            self._timers[key].append(duration)
            if labels:
                self._labels[key] = labels

    @contextmanager
    def time(self, name: str, labels: Optional[Dict[str, str]] = None):
        """
        Context manager to time a code block.

        Args:
            name: Metric name
            labels: Optional labels for the metric

        Example:
            with metrics.time("operation_duration"):
                do_work()
        """
        start = time.perf_counter()
        try:
            yield
        finally:
            duration = time.perf_counter() - start
            self.record_time(name, duration, labels)

    def get_counter(self, name: str, labels: Optional[Dict[str, str]] = None) -> float:
        """Get current counter value."""
        with self._lock:
            key = self._make_key(name, labels)
            return self._counters.get(key, 0.0)

    def get_gauge(self, name: str, labels: Optional[Dict[str, str]] = None) -> Optional[float]:
        """Get current gauge value."""
        with self._lock:
            key = self._make_key(name, labels)
            return self._gauges.get(key)

    def get_histogram_stats(
        self, name: str, labels: Optional[Dict[str, str]] = None
    ) -> Optional[HistogramStats]:
        """Get histogram statistics."""
        with self._lock:
            key = self._make_key(name, labels)
            values = self._histograms.get(key, [])
            if not values:
                return None

            sorted_values = sorted(values)
            count = len(sorted_values)
            total = sum(sorted_values)

            return HistogramStats(
                count=count,
                sum=total,
                min=sorted_values[0],
                max=sorted_values[-1],
                mean=total / count,
                p50=self._percentile(sorted_values, 0.5),
                p95=self._percentile(sorted_values, 0.95),
                p99=self._percentile(sorted_values, 0.99),
            )

    def get_timer_stats(
        self, name: str, labels: Optional[Dict[str, str]] = None
    ) -> Optional[HistogramStats]:
        """Get timer statistics."""
        with self._lock:
            key = self._make_key(name, labels)
            values = self._timers.get(key, [])
            if not values:
                return None

            sorted_values = sorted(values)
            count = len(sorted_values)
            total = sum(sorted_values)

            return HistogramStats(
                count=count,
                sum=total,
                min=sorted_values[0],
                max=sorted_values[-1],
                mean=total / count,
                p50=self._percentile(sorted_values, 0.5),
                p95=self._percentile(sorted_values, 0.95),
                p99=self._percentile(sorted_values, 0.99),
            )

    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics."""
        with self._lock:
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": {
                    name: self._histogram_to_dict(values)
                    for name, values in self._histograms.items()
                },
                "timers": {
                    name: self._histogram_to_dict(values)
                    for name, values in self._timers.items()
                },
            }

    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            self._timers.clear()
            self._labels.clear()

    @staticmethod
    def _make_key(name: str, labels: Optional[Dict[str, str]]) -> str:
        """Create a unique key from name and labels."""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    @staticmethod
    def _percentile(sorted_values: List[float], p: float) -> float:
        """Calculate percentile from sorted values."""
        if not sorted_values:
            return 0.0
        k = (len(sorted_values) - 1) * p
        f = int(k)
        c = f + 1
        if c >= len(sorted_values):
            return sorted_values[-1]
        d0 = sorted_values[f] * (c - k)
        d1 = sorted_values[c] * (k - f)
        return d0 + d1

    @staticmethod
    def _histogram_to_dict(values: List[float]) -> Dict[str, Any]:
        """Convert histogram values to statistics dict."""
        if not values:
            return {"count": 0}

        sorted_values = sorted(values)
        count = len(sorted_values)
        total = sum(sorted_values)

        return {
            "count": count,
            "sum": total,
            "min": sorted_values[0],
            "max": sorted_values[-1],
            "mean": total / count,
            "p50": MetricsCollector._percentile(sorted_values, 0.5),
            "p95": MetricsCollector._percentile(sorted_values, 0.95),
            "p99": MetricsCollector._percentile(sorted_values, 0.99),
        }


class StructuredLogger:
    """
    Structured logging with context and labels.

    Provides JSON-compatible structured logging with:
    - Contextual information
    - Custom labels
    - Performance tracking
    - Error tracking
    """

    def __init__(self, name: str, metrics: Optional[MetricsCollector] = None):
        """
        Initialize structured logger.

        Args:
            name: Logger name (usually module name)
            metrics: Optional metrics collector for automatic metric tracking
        """
        self.logger = logging.getLogger(name)
        self.name = name
        self.metrics = metrics

    def debug(self, message: str, **context) -> None:
        """Log debug message with context."""
        self._log(logging.DEBUG, message, context)

    def info(self, message: str, **context) -> None:
        """Log info message with context."""
        self._log(logging.INFO, message, context)

    def warning(self, message: str, **context) -> None:
        """Log warning message with context."""
        self._log(logging.WARNING, message, context)
        if self.metrics:
            self.metrics.increment("log_warnings_total", labels={"logger": self.name})

    def error(self, message: str, error: Optional[Exception] = None, **context) -> None:
        """Log error message with context and optional exception."""
        if error:
            context["error_type"] = type(error).__name__
            context["error_message"] = str(error)
        self._log(logging.ERROR, message, context)
        if self.metrics:
            self.metrics.increment(
                "log_errors_total",
                labels={"logger": self.name, "error_type": context.get("error_type", "unknown")},
            )

    def _log(self, level: int, message: str, context: Dict[str, Any]) -> None:
        """Internal logging with structured context."""
        # Add timestamp
        context["timestamp"] = datetime.now().isoformat()
        context["logger"] = self.name

        # Format message with context
        if context:
            context_str = " ".join(f"{k}={v}" for k, v in context.items())
            full_message = f"{message} {context_str}"
        else:
            full_message = message

        self.logger.log(level, full_message, extra=context)


def monitored(
    operation: str,
    metrics: MetricsCollector,
    track_errors: bool = True,
    track_duration: bool = True,
) -> Callable:
    """
    Decorator to monitor function execution.

    Args:
        operation: Operation name for metrics
        metrics: Metrics collector
        track_errors: Track error count (default: True)
        track_duration: Track execution duration (default: True)

    Example:
        @monitored("database_query", metrics)
        def query_database():
            return db.execute(query)
    """

    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # Track call count
            metrics.increment(f"{operation}_total")

            # Track duration
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                # Track success
                metrics.increment(f"{operation}_success")
                return result
            except Exception as e:
                # Track error
                if track_errors:
                    metrics.increment(
                        f"{operation}_errors",
                        labels={"error_type": type(e).__name__},
                    )
                raise
            finally:
                if track_duration:
                    duration = time.perf_counter() - start
                    metrics.record_time(f"{operation}_duration", duration)

        return wrapper

    return decorator


# Global metrics collector instance
_global_metrics = MetricsCollector()


def get_metrics() -> MetricsCollector:
    """Get the global metrics collector instance."""
    return _global_metrics


def get_logger(name: str) -> StructuredLogger:
    """
    Get a structured logger with automatic metrics tracking.

    Args:
        name: Logger name (usually __name__)

    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(name, metrics=_global_metrics)
