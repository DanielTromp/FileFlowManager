"""
Health check and system monitoring for FileFlow Manager.

Provides health checks for:
- Database connectivity
- Cache effectiveness
- System resources
- Performance metrics
"""

import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from fileflow_core.observability import MetricsCollector, get_metrics


class HealthStatus(Enum):
    """Health check status levels."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheckResult:
    """Result of a health check."""

    name: str
    status: HealthStatus
    message: str
    timestamp: datetime
    details: dict[str, Any]
    latency_ms: float | None = None


class HealthChecker:
    """
    System health monitoring.

    Performs health checks on:
    - Database connectivity
    - Cache performance
    - File system access
    - System resources
    """

    def __init__(self, metrics: MetricsCollector | None = None):
        """
        Initialize health checker.

        Args:
            metrics: Optional metrics collector for tracking health check results
        """
        self.metrics = metrics or get_metrics()

    def check_database(self, db_path: str) -> HealthCheckResult:
        """
        Check database health.

        Args:
            db_path: Path to database file

        Returns:
            HealthCheckResult with database status
        """
        start = time.perf_counter()
        name = "database"

        try:
            import sqlite3

            path = Path(db_path)

            # Check if database file exists
            if not path.exists():
                latency = (time.perf_counter() - start) * 1000
                self.metrics.increment("health_check_failures", labels={"check": name})
                return HealthCheckResult(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message="Database file does not exist",
                    timestamp=datetime.now(),
                    details={"path": str(path), "exists": False},
                    latency_ms=latency,
                )

            # Try to connect and query
            conn = sqlite3.connect(str(path))
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            conn.close()

            latency = (time.perf_counter() - start) * 1000
            self.metrics.increment("health_check_success", labels={"check": name})
            self.metrics.record_time("health_check_duration", latency / 1000, labels={"check": name})

            return HealthCheckResult(
                name=name,
                status=HealthStatus.HEALTHY,
                message="Database is accessible",
                timestamp=datetime.now(),
                details={"path": str(path), "latency_ms": round(latency, 2)},
                latency_ms=latency,
            )

        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            self.metrics.increment("health_check_failures", labels={"check": name})

            return HealthCheckResult(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Database check failed: {str(e)}",
                timestamp=datetime.now(),
                details={"error": str(e), "error_type": type(e).__name__},
                latency_ms=latency,
            )

    def check_cache_health(
        self, cache_hit_rate: float, threshold_healthy: float = 0.8, threshold_degraded: float = 0.5
    ) -> HealthCheckResult:
        """
        Check cache health based on hit rate.

        Args:
            cache_hit_rate: Current cache hit rate (0.0 to 1.0)
            threshold_healthy: Threshold for healthy status (default: 0.8)
            threshold_degraded: Threshold for degraded status (default: 0.5)

        Returns:
            HealthCheckResult with cache status
        """
        start = time.perf_counter()
        name = "cache"

        if cache_hit_rate >= threshold_healthy:
            status = HealthStatus.HEALTHY
            message = f"Cache hit rate is healthy ({cache_hit_rate:.1%})"
        elif cache_hit_rate >= threshold_degraded:
            status = HealthStatus.DEGRADED
            message = f"Cache hit rate is degraded ({cache_hit_rate:.1%})"
        else:
            status = HealthStatus.UNHEALTHY
            message = f"Cache hit rate is too low ({cache_hit_rate:.1%})"

        latency = (time.perf_counter() - start) * 1000

        if status == HealthStatus.HEALTHY:
            self.metrics.increment("health_check_success", labels={"check": name})
        else:
            self.metrics.increment("health_check_failures", labels={"check": name})

        return HealthCheckResult(
            name=name,
            status=status,
            message=message,
            timestamp=datetime.now(),
            details={
                "hit_rate": round(cache_hit_rate, 4),
                "threshold_healthy": threshold_healthy,
                "threshold_degraded": threshold_degraded,
            },
            latency_ms=latency,
        )

    def check_file_system(self, path: str) -> HealthCheckResult:
        """
        Check file system accessibility.

        Args:
            path: Path to check

        Returns:
            HealthCheckResult with file system status
        """
        start = time.perf_counter()
        name = "filesystem"

        try:
            p = Path(path)

            # Check if path exists
            if not p.exists():
                latency = (time.perf_counter() - start) * 1000
                self.metrics.increment("health_check_failures", labels={"check": name})

                return HealthCheckResult(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Path does not exist: {path}",
                    timestamp=datetime.now(),
                    details={"path": str(path), "exists": False},
                    latency_ms=latency,
                )

            # Check if readable/writable
            is_readable = p.is_dir() or p.is_file()
            is_writable = False

            try:
                # Try to create a temporary file to test write access
                test_file = p / ".health_check_test" if p.is_dir() else p.parent / ".health_check_test"
                test_file.touch()
                test_file.unlink()
                is_writable = True
            except (OSError, PermissionError):
                pass

            latency = (time.perf_counter() - start) * 1000

            if is_readable and is_writable:
                status = HealthStatus.HEALTHY
                message = "File system is accessible (read/write)"
            elif is_readable:
                status = HealthStatus.DEGRADED
                message = "File system is read-only"
            else:
                status = HealthStatus.UNHEALTHY
                message = "File system is not accessible"

            if status == HealthStatus.HEALTHY:
                self.metrics.increment("health_check_success", labels={"check": name})
            else:
                self.metrics.increment("health_check_failures", labels={"check": name})

            return HealthCheckResult(
                name=name,
                status=status,
                message=message,
                timestamp=datetime.now(),
                details={
                    "path": str(path),
                    "readable": is_readable,
                    "writable": is_writable,
                },
                latency_ms=latency,
            )

        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            self.metrics.increment("health_check_failures", labels={"check": name})

            return HealthCheckResult(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"File system check failed: {str(e)}",
                timestamp=datetime.now(),
                details={"error": str(e), "error_type": type(e).__name__},
                latency_ms=latency,
            )

    def check_performance_metrics(
        self,
        avg_operation_time: float,
        threshold_healthy: float = 0.1,
        threshold_degraded: float = 1.0,
    ) -> HealthCheckResult:
        """
        Check performance metrics.

        Args:
            avg_operation_time: Average operation time in seconds
            threshold_healthy: Threshold for healthy status in seconds (default: 0.1)
            threshold_degraded: Threshold for degraded status in seconds (default: 1.0)

        Returns:
            HealthCheckResult with performance status
        """
        start = time.perf_counter()
        name = "performance"

        if avg_operation_time <= threshold_healthy:
            status = HealthStatus.HEALTHY
            message = f"Performance is healthy (avg: {avg_operation_time:.3f}s)"
        elif avg_operation_time <= threshold_degraded:
            status = HealthStatus.DEGRADED
            message = f"Performance is degraded (avg: {avg_operation_time:.3f}s)"
        else:
            status = HealthStatus.UNHEALTHY
            message = f"Performance is too slow (avg: {avg_operation_time:.3f}s)"

        latency = (time.perf_counter() - start) * 1000

        if status == HealthStatus.HEALTHY:
            self.metrics.increment("health_check_success", labels={"check": name})
        else:
            self.metrics.increment("health_check_failures", labels={"check": name})

        return HealthCheckResult(
            name=name,
            status=status,
            message=message,
            timestamp=datetime.now(),
            details={
                "avg_operation_time_seconds": round(avg_operation_time, 4),
                "threshold_healthy": threshold_healthy,
                "threshold_degraded": threshold_degraded,
            },
            latency_ms=latency,
        )

    def run_all_checks(
        self,
        db_path: str | None = None,
        cache_hit_rate: float | None = None,
        fs_path: str | None = None,
        avg_operation_time: float | None = None,
    ) -> dict[str, HealthCheckResult]:
        """
        Run all configured health checks.

        Args:
            db_path: Optional database path to check
            cache_hit_rate: Optional cache hit rate to check
            fs_path: Optional file system path to check
            avg_operation_time: Optional average operation time to check

        Returns:
            Dictionary of check results by name
        """
        results = {}

        if db_path:
            results["database"] = self.check_database(db_path)

        if cache_hit_rate is not None:
            results["cache"] = self.check_cache_health(cache_hit_rate)

        if fs_path:
            results["filesystem"] = self.check_file_system(fs_path)

        if avg_operation_time is not None:
            results["performance"] = self.check_performance_metrics(avg_operation_time)

        return results

    def get_overall_status(self, results: dict[str, HealthCheckResult]) -> HealthStatus:
        """
        Get overall health status from individual check results.

        Args:
            results: Dictionary of health check results

        Returns:
            Overall health status (worst status from all checks)
        """
        if not results:
            return HealthStatus.HEALTHY

        statuses = [result.status for result in results.values()]

        if HealthStatus.UNHEALTHY in statuses:
            return HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY

    def format_health_report(self, results: dict[str, HealthCheckResult]) -> str:
        """
        Format health check results as a readable report.

        Args:
            results: Dictionary of health check results

        Returns:
            Formatted health report string
        """
        overall_status = self.get_overall_status(results)

        lines = []
        lines.append("=" * 80)
        lines.append(f"SYSTEM HEALTH CHECK - Status: {overall_status.value.upper()}")
        lines.append("=" * 80)
        lines.append("")

        for _name, result in results.items():
            status_symbol = {
                HealthStatus.HEALTHY: "✓",
                HealthStatus.DEGRADED: "⚠",
                HealthStatus.UNHEALTHY: "✗",
            }[result.status]

            lines.append(f"{status_symbol} {result.name.upper()}: {result.status.value}")
            lines.append(f"  Message: {result.message}")
            if result.latency_ms:
                lines.append(f"  Latency: {result.latency_ms:.2f}ms")
            if result.details:
                lines.append(f"  Details: {result.details}")
            lines.append("")

        lines.append("=" * 80)
        return "\n".join(lines)
