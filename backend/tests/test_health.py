"""
Tests for health check functionality.

Tests database health, cache health, and system status monitoring.
"""

import tempfile
from pathlib import Path

import pytest

from fileflow_core.health import HealthChecker, HealthStatus


class TestHealthChecker:
    """Test HealthChecker functionality."""

    def test_check_database_exists(self):
        """Test database health check with existing database."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        try:
            # Create a valid SQLite database
            import sqlite3

            conn = sqlite3.connect(db_path)
            conn.execute("CREATE TABLE test (id INTEGER)")
            conn.commit()
            conn.close()

            checker = HealthChecker()
            result = checker.check_database(db_path)

            assert result.name == "database"
            assert result.status == HealthStatus.HEALTHY
            assert "accessible" in result.message.lower()
            assert result.latency_ms is not None
            assert result.latency_ms >= 0

        finally:
            Path(db_path).unlink()

    def test_check_database_missing(self):
        """Test database health check with missing database."""
        checker = HealthChecker()
        result = checker.check_database("/nonexistent/database.db")

        assert result.status == HealthStatus.UNHEALTHY
        assert "does not exist" in result.message

    def test_check_cache_health_excellent(self):
        """Test cache health with excellent hit rate."""
        checker = HealthChecker()
        result = checker.check_cache_health(cache_hit_rate=0.95)

        assert result.status == HealthStatus.HEALTHY
        assert "0.95" in result.message or "95" in result.message

    def test_check_cache_health_degraded(self):
        """Test cache health with degraded hit rate."""
        checker = HealthChecker()
        result = checker.check_cache_health(cache_hit_rate=0.65)

        assert result.status == HealthStatus.DEGRADED
        assert "0.65" in result.message or "65" in result.message

    def test_check_cache_health_unhealthy(self):
        """Test cache health with unhealthy hit rate."""
        checker = HealthChecker()
        result = checker.check_cache_health(cache_hit_rate=0.3)

        assert result.status == HealthStatus.UNHEALTHY
        assert "0.3" in result.message or "30" in result.message

    def test_check_cache_health_custom_thresholds(self):
        """Test cache health with custom thresholds."""
        checker = HealthChecker()
        result = checker.check_cache_health(
            cache_hit_rate=0.7, threshold_healthy=0.9, threshold_degraded=0.6
        )

        assert result.status == HealthStatus.DEGRADED

    def test_check_file_system_accessible(self):
        """Test file system check with accessible path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checker = HealthChecker()
            result = checker.check_file_system(tmpdir)

            assert result.status == HealthStatus.HEALTHY
            assert "accessible" in result.message.lower()
            assert result.details["readable"] is True
            assert result.details["writable"] is True

    def test_check_file_system_nonexistent(self):
        """Test file system check with nonexistent path."""
        checker = HealthChecker()
        result = checker.check_file_system("/nonexistent/path")

        assert result.status == HealthStatus.UNHEALTHY
        assert "does not exist" in result.message

    def test_check_performance_healthy(self):
        """Test performance check with healthy metrics."""
        checker = HealthChecker()
        result = checker.check_performance_metrics(avg_operation_time=0.05)

        assert result.status == HealthStatus.HEALTHY
        assert "0.05" in result.message or "0.050" in result.message

    def test_check_performance_degraded(self):
        """Test performance check with degraded metrics."""
        checker = HealthChecker()
        result = checker.check_performance_metrics(avg_operation_time=0.5)

        assert result.status == HealthStatus.DEGRADED

    def test_check_performance_unhealthy(self):
        """Test performance check with unhealthy metrics."""
        checker = HealthChecker()
        result = checker.check_performance_metrics(avg_operation_time=2.0)

        assert result.status == HealthStatus.UNHEALTHY

    def test_run_all_checks(self):
        """Test running all health checks together."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # Create database
            import sqlite3

            conn = sqlite3.connect(str(db_path))
            conn.execute("CREATE TABLE test (id INTEGER)")
            conn.commit()
            conn.close()

            checker = HealthChecker()
            results = checker.run_all_checks(
                db_path=str(db_path),
                cache_hit_rate=0.85,
                fs_path=tmpdir,
                avg_operation_time=0.1,
            )

            assert "database" in results
            assert "cache" in results
            assert "filesystem" in results
            assert "performance" in results

            # All should be healthy
            for result in results.values():
                assert result.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]

    def test_get_overall_status_healthy(self):
        """Test overall status with all healthy checks."""
        checker = HealthChecker()
        results = {
            "check1": checker.check_cache_health(0.9),
            "check2": checker.check_performance_metrics(0.05),
        }

        overall = checker.get_overall_status(results)
        assert overall == HealthStatus.HEALTHY

    def test_get_overall_status_degraded(self):
        """Test overall status with some degraded checks."""
        checker = HealthChecker()
        results = {
            "check1": checker.check_cache_health(0.9),  # Healthy
            "check2": checker.check_cache_health(0.6),  # Degraded
        }

        overall = checker.get_overall_status(results)
        assert overall == HealthStatus.DEGRADED

    def test_get_overall_status_unhealthy(self):
        """Test overall status with some unhealthy checks."""
        checker = HealthChecker()
        results = {
            "check1": checker.check_cache_health(0.9),  # Healthy
            "check2": checker.check_cache_health(0.3),  # Unhealthy
        }

        overall = checker.get_overall_status(results)
        assert overall == HealthStatus.UNHEALTHY

    def test_format_health_report(self):
        """Test health report formatting."""
        checker = HealthChecker()
        results = {
            "cache": checker.check_cache_health(0.85),
            "performance": checker.check_performance_metrics(0.1),
        }

        report = checker.format_health_report(results)

        assert "SYSTEM HEALTH CHECK" in report
        assert "cache" in report.lower()
        assert "performance" in report.lower()
        assert "✓" in report  # Healthy checks should show checkmark

    def test_health_check_with_metrics(self):
        """Test that health checks record metrics."""
        from fileflow_core.observability import MetricsCollector

        metrics = MetricsCollector()
        checker = HealthChecker(metrics=metrics)

        # Run some checks
        checker.check_cache_health(0.9)
        checker.check_cache_health(0.3)

        # Should have recorded successes and failures
        success_count = metrics.get_counter("health_check_success", labels={"check": "cache"})
        failure_count = metrics.get_counter("health_check_failures", labels={"check": "cache"})

        assert success_count >= 1.0
        assert failure_count >= 1.0
