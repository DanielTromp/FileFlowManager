"""
Metrics export and reporting for FileFlow Manager.

Provides export functionality for:
- Prometheus format metrics
- JSON metrics export
- Human-readable reports
- Performance dashboards
"""

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fileflow_core.cache_monitor import CacheMonitor, CacheStats
from fileflow_core.health import HealthChecker, HealthCheckResult, HealthStatus
from fileflow_core.observability import MetricsCollector, get_metrics


@dataclass
class MetricsSnapshot:
    """Complete metrics snapshot at a point in time."""

    timestamp: datetime
    counters: Dict[str, float]
    gauges: Dict[str, float]
    histograms: Dict[str, Dict[str, Any]]
    timers: Dict[str, Dict[str, Any]]
    cache_stats: Dict[str, CacheStats]
    health_checks: Optional[Dict[str, HealthCheckResult]] = None


class MetricsExporter:
    """
    Export metrics in various formats.

    Supports:
    - JSON export for API/storage
    - Prometheus format for monitoring systems
    - Human-readable reports
    """

    def __init__(
        self,
        metrics: Optional[MetricsCollector] = None,
        cache_monitor: Optional[CacheMonitor] = None,
        health_checker: Optional[HealthChecker] = None,
    ):
        """
        Initialize metrics exporter.

        Args:
            metrics: Metrics collector instance
            cache_monitor: Cache monitor instance
            health_checker: Health checker instance
        """
        self.metrics = metrics or get_metrics()
        self.cache_monitor = cache_monitor or CacheMonitor(metrics=self.metrics)
        self.health_checker = health_checker or HealthChecker(metrics=self.metrics)

    def take_snapshot(
        self, include_health_checks: bool = False, **health_check_params
    ) -> MetricsSnapshot:
        """
        Take a complete metrics snapshot.

        Args:
            include_health_checks: Whether to run health checks
            **health_check_params: Parameters to pass to health checks

        Returns:
            MetricsSnapshot with all current metrics
        """
        all_metrics = self.metrics.get_all_metrics()
        cache_stats = self.cache_monitor.get_all_cache_stats()

        health_checks = None
        if include_health_checks:
            health_checks = self.health_checker.run_all_checks(**health_check_params)

        return MetricsSnapshot(
            timestamp=datetime.now(),
            counters=all_metrics["counters"],
            gauges=all_metrics["gauges"],
            histograms=all_metrics["histograms"],
            timers=all_metrics["timers"],
            cache_stats=cache_stats,
            health_checks=health_checks,
        )

    def export_json(
        self, snapshot: Optional[MetricsSnapshot] = None, pretty: bool = True
    ) -> str:
        """
        Export metrics as JSON.

        Args:
            snapshot: Optional snapshot to export, otherwise takes new one
            pretty: Whether to format JSON with indentation

        Returns:
            JSON string
        """
        if snapshot is None:
            snapshot = self.take_snapshot()

        data = {
            "timestamp": snapshot.timestamp.isoformat(),
            "counters": snapshot.counters,
            "gauges": snapshot.gauges,
            "histograms": snapshot.histograms,
            "timers": snapshot.timers,
            "cache_stats": {
                name: asdict(stats) for name, stats in snapshot.cache_stats.items()
            },
        }

        if snapshot.health_checks:
            data["health_checks"] = {
                name: {
                    "status": result.status.value,
                    "message": result.message,
                    "details": result.details,
                    "latency_ms": result.latency_ms,
                }
                for name, result in snapshot.health_checks.items()
            }

        if pretty:
            return json.dumps(data, indent=2, default=str)
        return json.dumps(data, default=str)

    def export_prometheus(self, snapshot: Optional[MetricsSnapshot] = None) -> str:
        """
        Export metrics in Prometheus text format.

        Args:
            snapshot: Optional snapshot to export, otherwise takes new one

        Returns:
            Prometheus format string
        """
        if snapshot is None:
            snapshot = self.take_snapshot()

        lines = []
        lines.append(f"# FileFlow Manager Metrics - {snapshot.timestamp.isoformat()}")
        lines.append("")

        # Export counters
        lines.append("# HELP fileflow_counter Monotonically increasing counter")
        lines.append("# TYPE fileflow_counter counter")
        for name, value in snapshot.counters.items():
            # Parse labels if present
            if "{" in name:
                metric_name = name[: name.index("{")]
                labels = name[name.index("{") : name.index("}") + 1]
                lines.append(f"fileflow_{metric_name}{labels} {value}")
            else:
                lines.append(f"fileflow_{name} {value}")

        lines.append("")

        # Export gauges
        lines.append("# HELP fileflow_gauge Current gauge value")
        lines.append("# TYPE fileflow_gauge gauge")
        for name, value in snapshot.gauges.items():
            if "{" in name:
                metric_name = name[: name.index("{")]
                labels = name[name.index("{") : name.index("}") + 1]
                lines.append(f"fileflow_{metric_name}{labels} {value}")
            else:
                lines.append(f"fileflow_{name} {value}")

        lines.append("")

        # Export histogram summaries
        lines.append("# HELP fileflow_histogram Histogram summary statistics")
        lines.append("# TYPE fileflow_histogram summary")
        for name, stats in snapshot.histograms.items():
            if stats.get("count", 0) > 0:
                base_name = f"fileflow_{name}"
                lines.append(f'{base_name}_count {stats["count"]}')
                lines.append(f'{base_name}_sum {stats["sum"]}')
                lines.append(f'{base_name}{{quantile="0.5"}} {stats["p50"]}')
                lines.append(f'{base_name}{{quantile="0.95"}} {stats["p95"]}')
                lines.append(f'{base_name}{{quantile="0.99"}} {stats["p99"]}')

        lines.append("")

        # Export timers
        lines.append("# HELP fileflow_timer Timer duration statistics")
        lines.append("# TYPE fileflow_timer summary")
        for name, stats in snapshot.timers.items():
            if stats.get("count", 0) > 0:
                base_name = f"fileflow_{name}"
                lines.append(f'{base_name}_count {stats["count"]}')
                lines.append(f'{base_name}_sum {stats["sum"]}')
                lines.append(f'{base_name}{{quantile="0.5"}} {stats["p50"]}')
                lines.append(f'{base_name}{{quantile="0.95"}} {stats["p95"]}')
                lines.append(f'{base_name}{{quantile="0.99"}} {stats["p99"]}')

        return "\n".join(lines)

    def export_report(self, snapshot: Optional[MetricsSnapshot] = None) -> str:
        """
        Export metrics as human-readable report.

        Args:
            snapshot: Optional snapshot to export, otherwise takes new one

        Returns:
            Formatted report string
        """
        if snapshot is None:
            snapshot = self.take_snapshot(include_health_checks=True)

        lines = []
        lines.append("=" * 80)
        lines.append("FILEFLOW MANAGER - METRICS REPORT")
        lines.append("=" * 80)
        lines.append(f"Timestamp: {snapshot.timestamp.isoformat()}")
        lines.append("")

        # Health checks
        if snapshot.health_checks:
            lines.append("SYSTEM HEALTH")
            lines.append("-" * 80)
            overall_status = self.health_checker.get_overall_status(snapshot.health_checks)
            lines.append(f"Overall Status: {overall_status.value.upper()}")
            lines.append("")
            for name, result in snapshot.health_checks.items():
                status_symbol = {
                    HealthStatus.HEALTHY: "✓",
                    HealthStatus.DEGRADED: "⚠",
                    HealthStatus.UNHEALTHY: "✗",
                }[result.status]
                lines.append(f"  {status_symbol} {name}: {result.message}")
            lines.append("")

        # Cache performance
        if snapshot.cache_stats:
            lines.append("CACHE PERFORMANCE")
            lines.append("-" * 80)
            for cache_name, stats in sorted(snapshot.cache_stats.items()):
                lines.append(f"Cache: {cache_name}")
                lines.append(f"  Hit Rate:    {stats.hit_rate:.2%}")
                lines.append(f"  Hits/Misses: {stats.hits:,} / {stats.misses:,}")
                lines.append(
                    f"  Size:        {stats.size:,} / {stats.capacity:,} "
                    f"({stats.size / stats.capacity * 100:.1f}% full)"
                )
                if stats.evictions > 0:
                    lines.append(f"  Evictions:   {stats.evictions:,}")
                lines.append("")

        # Top counters
        if snapshot.counters:
            lines.append("TOP METRICS (Counters)")
            lines.append("-" * 80)
            top_counters = sorted(
                snapshot.counters.items(), key=lambda x: x[1], reverse=True
            )[:10]
            for name, value in top_counters:
                lines.append(f"  {name:50} {value:>15,.0f}")
            lines.append("")

        # Performance timers
        if snapshot.timers:
            lines.append("PERFORMANCE TIMERS")
            lines.append("-" * 80)
            for name, stats in sorted(snapshot.timers.items()):
                if stats.get("count", 0) > 0:
                    lines.append(f"Timer: {name}")
                    lines.append(f"  Count:   {stats['count']:,}")
                    lines.append(f"  Mean:    {stats['mean']:.4f}s")
                    lines.append(f"  P50:     {stats['p50']:.4f}s")
                    lines.append(f"  P95:     {stats['p95']:.4f}s")
                    lines.append(f"  P99:     {stats['p99']:.4f}s")
                    lines.append("")

        lines.append("=" * 80)
        return "\n".join(lines)

    def save_snapshot(
        self, path: Path, snapshot: Optional[MetricsSnapshot] = None, format: str = "json"
    ) -> None:
        """
        Save metrics snapshot to file.

        Args:
            path: File path to save to
            snapshot: Optional snapshot to save, otherwise takes new one
            format: Export format ("json", "prometheus", "report")
        """
        if snapshot is None:
            snapshot = self.take_snapshot(include_health_checks=True)

        if format == "json":
            content = self.export_json(snapshot)
        elif format == "prometheus":
            content = self.export_prometheus(snapshot)
        elif format == "report":
            content = self.export_report(snapshot)
        else:
            raise ValueError(f"Unknown format: {format}")

        path.write_text(content)

    def get_summary_stats(self, snapshot: Optional[MetricsSnapshot] = None) -> Dict[str, Any]:
        """
        Get summary statistics.

        Args:
            snapshot: Optional snapshot to summarize, otherwise takes new one

        Returns:
            Dictionary with summary statistics
        """
        if snapshot is None:
            snapshot = self.take_snapshot(include_health_checks=True)

        # Calculate totals
        total_operations = sum(
            v for k, v in snapshot.counters.items() if k.endswith("_total")
        )
        total_errors = sum(v for k, v in snapshot.counters.items() if "error" in k.lower())

        # Average cache hit rate
        avg_hit_rate = (
            sum(stats.hit_rate for stats in snapshot.cache_stats.values())
            / len(snapshot.cache_stats)
            if snapshot.cache_stats
            else 0.0
        )

        # Overall health status
        overall_health = (
            self.health_checker.get_overall_status(snapshot.health_checks).value
            if snapshot.health_checks
            else "unknown"
        )

        return {
            "timestamp": snapshot.timestamp.isoformat(),
            "total_operations": int(total_operations),
            "total_errors": int(total_errors),
            "error_rate": total_errors / total_operations if total_operations > 0 else 0.0,
            "avg_cache_hit_rate": avg_hit_rate,
            "num_caches": len(snapshot.cache_stats),
            "num_counters": len(snapshot.counters),
            "num_gauges": len(snapshot.gauges),
            "num_timers": len(snapshot.timers),
            "overall_health": overall_health,
        }
