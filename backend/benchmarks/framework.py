"""
Benchmarking framework for performance testing.

Provides utilities for timing operations, collecting statistics,
and generating performance reports.
"""

import statistics
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class BenchmarkResult:
    """Results from a single benchmark run."""

    name: str
    iterations: int
    total_time: float
    times: list[float] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def mean_time(self) -> float:
        """Average time per iteration."""
        return statistics.mean(self.times) if self.times else 0.0

    @property
    def median_time(self) -> float:
        """Median time per iteration."""
        return statistics.median(self.times) if self.times else 0.0

    @property
    def stddev(self) -> float:
        """Standard deviation of times."""
        return statistics.stdev(self.times) if len(self.times) > 1 else 0.0

    @property
    def min_time(self) -> float:
        """Minimum time."""
        return min(self.times) if self.times else 0.0

    @property
    def max_time(self) -> float:
        """Maximum time."""
        return max(self.times) if self.times else 0.0

    @property
    def ops_per_second(self) -> float:
        """Operations per second (based on mean time)."""
        return 1.0 / self.mean_time if self.mean_time > 0 else 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for reporting."""
        return {
            "name": self.name,
            "iterations": self.iterations,
            "total_time": round(self.total_time, 4),
            "mean_time": round(self.mean_time, 4),
            "median_time": round(self.median_time, 4),
            "stddev": round(self.stddev, 4),
            "min_time": round(self.min_time, 4),
            "max_time": round(self.max_time, 4),
            "ops_per_second": round(self.ops_per_second, 2),
            "metadata": self.metadata,
        }


class Benchmark:
    """Benchmark runner for timing operations."""

    def __init__(self, name: str):
        """Initialize benchmark."""
        self.name = name
        self.results: list[BenchmarkResult] = []

    def run(
        self,
        func: Callable[[], Any],
        iterations: int = 100,
        warmup: int = 10,
        name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> BenchmarkResult:
        """
        Run a benchmark.

        Args:
            func: Function to benchmark
            iterations: Number of iterations to run
            warmup: Number of warmup iterations
            name: Optional name for this specific run
            metadata: Optional metadata to include in results

        Returns:
            BenchmarkResult with timing statistics
        """
        benchmark_name = name or f"{self.name}-run"

        # Warmup runs
        for _ in range(warmup):
            func()

        # Benchmark runs
        times = []
        start_total = time.perf_counter()

        for _ in range(iterations):
            start = time.perf_counter()
            func()
            end = time.perf_counter()
            times.append(end - start)

        end_total = time.perf_counter()
        total_time = end_total - start_total

        result = BenchmarkResult(
            name=benchmark_name,
            iterations=iterations,
            total_time=total_time,
            times=times,
            metadata=metadata or {},
        )

        self.results.append(result)
        return result

    def compare(
        self,
        baseline_func: Callable[[], Any],
        optimized_func: Callable[[], Any],
        iterations: int = 100,
        warmup: int = 10,
        baseline_name: str = "baseline",
        optimized_name: str = "optimized",
    ) -> dict[str, Any]:
        """
        Compare two implementations.

        Args:
            baseline_func: Baseline implementation
            optimized_func: Optimized implementation
            iterations: Number of iterations
            warmup: Number of warmup iterations
            baseline_name: Name for baseline
            optimized_name: Name for optimized

        Returns:
            Comparison results with speedup calculation
        """
        baseline_result = self.run(
            baseline_func, iterations, warmup, name=baseline_name
        )
        optimized_result = self.run(
            optimized_func, iterations, warmup, name=optimized_name
        )

        speedup = baseline_result.mean_time / optimized_result.mean_time
        improvement_pct = ((speedup - 1.0) * 100) if speedup > 1.0 else 0.0

        return {
            "baseline": baseline_result.to_dict(),
            "optimized": optimized_result.to_dict(),
            "speedup": round(speedup, 2),
            "improvement_percent": round(improvement_pct, 2),
        }

    def get_summary(self) -> dict[str, Any]:
        """Get summary of all benchmark results."""
        return {
            "benchmark_name": self.name,
            "total_runs": len(self.results),
            "results": [result.to_dict() for result in self.results],
        }


def format_benchmark_report(results: dict[str, Any]) -> str:
    """
    Format benchmark results as a readable report.

    Args:
        results: Benchmark results dictionary

    Returns:
        Formatted report string
    """
    lines = []
    lines.append("=" * 80)
    lines.append(f"Benchmark: {results.get('name', 'Unnamed')}")
    lines.append("=" * 80)
    lines.append("")

    if "baseline" in results and "optimized" in results:
        # Comparison report
        baseline = results["baseline"]
        optimized = results["optimized"]

        lines.append(f"Baseline ({baseline['name']}):")
        lines.append(f"  Mean time:     {baseline['mean_time']:.4f}s")
        lines.append(f"  Median time:   {baseline['median_time']:.4f}s")
        lines.append(f"  Std dev:       {baseline['stddev']:.4f}s")
        lines.append(f"  Ops/sec:       {baseline['ops_per_second']:.2f}")
        lines.append("")

        lines.append(f"Optimized ({optimized['name']}):")
        lines.append(f"  Mean time:     {optimized['mean_time']:.4f}s")
        lines.append(f"  Median time:   {optimized['median_time']:.4f}s")
        lines.append(f"  Std dev:       {optimized['stddev']:.4f}s")
        lines.append(f"  Ops/sec:       {optimized['ops_per_second']:.2f}")
        lines.append("")

        lines.append("Performance Improvement:")
        lines.append(f"  Speedup:       {results['speedup']:.2f}x")
        lines.append(f"  Improvement:   {results['improvement_percent']:.2f}%")

    elif "results" in results:
        # Summary report
        for result in results["results"]:
            lines.append(f"Run: {result['name']}")
            lines.append(f"  Iterations:    {result['iterations']}")
            lines.append(f"  Total time:    {result['total_time']:.4f}s")
            lines.append(f"  Mean time:     {result['mean_time']:.4f}s")
            lines.append(f"  Median time:   {result['median_time']:.4f}s")
            lines.append(f"  Std dev:       {result['stddev']:.4f}s")
            lines.append(f"  Min time:      {result['min_time']:.4f}s")
            lines.append(f"  Max time:      {result['max_time']:.4f}s")
            lines.append(f"  Ops/sec:       {result['ops_per_second']:.2f}")

            if result.get("metadata"):
                lines.append("  Metadata:")
                for key, value in result["metadata"].items():
                    lines.append(f"    {key}: {value}")
            lines.append("")

    lines.append("=" * 80)
    return "\n".join(lines)
