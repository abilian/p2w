"""Statistical analysis for benchmark results.

Provides tools for computing benchmark statistics with:
- Coefficient of Variation (CV) targeting < 1%
- Outlier detection using IQR method
- 95% confidence interval calculation
- Adaptive run counts until statistical stability
"""

from __future__ import annotations

import math
import statistics
from collections.abc import Callable
from dataclasses import dataclass, field


@dataclass(frozen=True)
class BenchmarkStats:
    """Statistical summary of benchmark runs.

    Attributes:
        times: Raw timing data (in seconds)
        mean: Arithmetic mean
        median: Median value
        stddev: Standard deviation
        cv: Coefficient of variation (stddev/mean)
        min: Minimum time
        max: Maximum time
        iqr: Interquartile range
        outliers: Values detected as outliers
        confidence_95: 95% confidence interval (lower, upper)
        runs_to_stable: Number of runs needed to reach stability
    """

    times: tuple[float, ...]
    mean: float
    median: float
    stddev: float
    cv: float
    min: float
    max: float
    iqr: float
    outliers: tuple[float, ...] = field(default_factory=tuple)
    confidence_95: tuple[float, float] = field(default_factory=lambda: (0.0, 0.0))
    runs_to_stable: int = 0


def compute_quartiles(data: list[float]) -> tuple[float, float, float]:
    """Compute Q1, median (Q2), and Q3 quartiles.

    Args:
        data: Sorted list of values (at least 4 elements for meaningful results).

    Returns:
        Tuple of (Q1, Q2, Q3) values.
    """
    n = len(data)
    if n < 4:
        med = statistics.median(data)
        return med, med, med

    sorted_data = sorted(data)

    # Q2 (median)
    q2 = statistics.median(sorted_data)

    # Q1: median of lower half
    if n % 2 == 0:
        lower_half = sorted_data[: n // 2]
        upper_half = sorted_data[n // 2 :]
    else:
        lower_half = sorted_data[: n // 2]
        upper_half = sorted_data[n // 2 + 1 :]

    q1 = statistics.median(lower_half) if lower_half else q2
    q3 = statistics.median(upper_half) if upper_half else q2

    return q1, q2, q3


def detect_outliers(data: list[float], factor: float = 1.5) -> list[float]:
    """Detect outliers using the IQR method.

    Values outside [Q1 - factor*IQR, Q3 + factor*IQR] are considered outliers.

    Args:
        data: List of values to check.
        factor: IQR multiplier (default 1.5 for mild outliers).

    Returns:
        List of values detected as outliers.
    """
    if len(data) < 4:
        return []

    q1, _, q3 = compute_quartiles(data)
    iqr = q3 - q1

    lower_bound = q1 - factor * iqr
    upper_bound = q3 + factor * iqr

    return [x for x in data if x < lower_bound or x > upper_bound]


def compute_confidence_interval(
    data: list[float], confidence: float = 0.95
) -> tuple[float, float]:
    """Compute confidence interval for the mean.

    Uses t-distribution approximation for small samples.

    Args:
        data: Sample data.
        confidence: Confidence level (default 0.95 for 95% CI).

    Returns:
        Tuple of (lower_bound, upper_bound).
    """
    n = len(data)
    if n < 2:
        mean = data[0] if data else 0.0
        return mean, mean

    mean = statistics.mean(data)
    stddev = statistics.stdev(data)
    stderr = stddev / math.sqrt(n)

    # t-distribution critical values for common sample sizes
    # For 95% CI (two-tailed, alpha=0.05)
    t_values = {
        2: 12.706,
        3: 4.303,
        4: 3.182,
        5: 2.776,
        6: 2.571,
        7: 2.447,
        8: 2.365,
        9: 2.306,
        10: 2.262,
        15: 2.145,
        20: 2.093,
        30: 2.045,
        50: 2.009,
        100: 1.984,
    }

    # Find appropriate t-value
    if n >= 100:
        t = 1.96  # Normal approximation
    else:
        # Find closest sample size
        sizes = sorted(t_values.keys())
        for size in sizes:
            if n <= size:
                t = t_values[size]
                break
        else:
            t = 1.96

    margin = t * stderr
    return mean - margin, mean + margin


def compute_stats(
    times: list[float], remove_outliers: bool = True, runs_to_stable: int = 0
) -> BenchmarkStats:
    """Compute comprehensive statistics from timing data.

    Args:
        times: List of timing measurements (in seconds).
        remove_outliers: Whether to exclude outliers from calculations.
        runs_to_stable: Number of runs taken to reach stability.

    Returns:
        BenchmarkStats with all computed metrics.
    """
    if not times:
        return BenchmarkStats(
            times=(),
            mean=0.0,
            median=0.0,
            stddev=0.0,
            cv=0.0,
            min=0.0,
            max=0.0,
            iqr=0.0,
            outliers=(),
            confidence_95=(0.0, 0.0),
            runs_to_stable=0,
        )

    # Detect outliers
    outliers = detect_outliers(times)

    # Use filtered data for stats if removing outliers
    if remove_outliers and outliers:
        outlier_set = set(outliers)
        filtered = [t for t in times if t not in outlier_set]
        if len(filtered) < 2:
            filtered = times  # Fall back if too few remain
    else:
        filtered = times

    # Compute basic stats
    mean = statistics.mean(filtered)
    median = statistics.median(filtered)
    stddev = statistics.stdev(filtered) if len(filtered) > 1 else 0.0
    cv = stddev / mean if mean > 0 else 0.0

    # Compute quartiles and IQR
    q1, _, q3 = compute_quartiles(filtered)
    iqr = q3 - q1

    # Confidence interval
    ci = compute_confidence_interval(filtered)

    return BenchmarkStats(
        times=tuple(times),
        mean=mean,
        median=median,
        stddev=stddev,
        cv=cv,
        min=min(filtered),
        max=max(filtered),
        iqr=iqr,
        outliers=tuple(outliers),
        confidence_95=ci,
        runs_to_stable=runs_to_stable,
    )


def run_until_stable(
    runner: Callable[[], float],
    min_runs: int = 5,
    max_runs: int = 50,
    target_cv: float = 0.01,
    warmup: int = 3,
    batch_size: int = 5,
) -> BenchmarkStats:
    """Run benchmark until coefficient of variation is below target.

    Executes warmup runs (discarded), then iteratively adds measurements
    until CV < target_cv or max_runs is reached.

    Args:
        runner: Callable that returns execution time in seconds.
        min_runs: Minimum number of timed runs before checking CV.
        max_runs: Maximum number of timed runs.
        target_cv: Target coefficient of variation (default 0.01 = 1%).
        warmup: Number of warmup runs to discard.
        batch_size: Number of runs to add per iteration.

    Returns:
        BenchmarkStats with all measurements and stability info.
    """
    # Warmup phase
    for _ in range(warmup):
        runner()

    # Initial measurement phase
    times: list[float] = []
    for _ in range(min_runs):
        times.append(runner())

    runs_to_stable = min_runs

    # Adaptive phase: keep adding runs until stable or max reached
    while len(times) < max_runs:
        # Check current CV
        if len(times) >= min_runs:
            mean = statistics.mean(times)
            if mean > 0:
                stddev = statistics.stdev(times) if len(times) > 1 else 0.0
                cv = stddev / mean
                if cv <= target_cv:
                    break

        # Add more runs
        runs_to_add = min(batch_size, max_runs - len(times))
        for _ in range(runs_to_add):
            times.append(runner())

        runs_to_stable = len(times)

    return compute_stats(times, remove_outliers=True, runs_to_stable=runs_to_stable)


def format_stats(stats: BenchmarkStats, unit: str = "ms") -> str:
    """Format benchmark statistics for display.

    Args:
        stats: Benchmark statistics to format.
        unit: Time unit for display ("ms" or "s").

    Returns:
        Formatted string like "485.2ms +/- 2.1ms (CV=0.43%, 12 runs)".
    """
    multiplier = 1000.0 if unit == "ms" else 1.0
    mean = stats.mean * multiplier
    stddev = stats.stddev * multiplier
    cv_pct = stats.cv * 100

    return f"{mean:.1f}{unit} +/- {stddev:.1f}{unit} (CV={cv_pct:.2f}%, {len(stats.times)} runs)"
