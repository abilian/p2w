"""Unit tests for p2w.benchmark.stats module."""

from __future__ import annotations

import pytest

from p2w.benchmark.stats import (
    BenchmarkStats,
    compute_confidence_interval,
    compute_quartiles,
    compute_stats,
    detect_outliers,
    format_stats,
    run_until_stable,
)


class TestComputeQuartiles:
    """Tests for compute_quartiles function."""

    def test_basic_quartiles(self) -> None:
        """Test quartile computation with known data."""
        data = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
        q1, q2, q3 = compute_quartiles(data)

        assert q2 == 4.5  # median
        assert q1 == 2.5  # Q1
        assert q3 == 6.5  # Q3

    def test_odd_length(self) -> None:
        """Test quartiles with odd number of elements."""
        data = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]
        q1, q2, q3 = compute_quartiles(data)

        assert q2 == 4.0  # median
        assert q1 == 2.0  # Q1
        assert q3 == 6.0  # Q3

    def test_small_dataset(self) -> None:
        """Test quartiles with fewer than 4 elements."""
        data = [1.0, 2.0, 3.0]
        q1, q2, q3 = compute_quartiles(data)

        # For small datasets, all quartiles should be median
        assert q1 == q2 == q3 == 2.0


class TestDetectOutliers:
    """Tests for detect_outliers function."""

    def test_no_outliers(self) -> None:
        """Test with data containing no outliers."""
        data = [10.0, 11.0, 10.5, 10.2, 10.8, 11.1, 10.3]
        outliers = detect_outliers(data)
        assert outliers == []

    def test_with_outliers(self) -> None:
        """Test detection of clear outliers."""
        # Normal data around 10, with outliers at 1 and 100
        data = [10.0, 11.0, 10.5, 10.2, 10.8, 1.0, 100.0]
        outliers = detect_outliers(data)

        assert 1.0 in outliers
        assert 100.0 in outliers
        assert len(outliers) == 2

    def test_small_dataset(self) -> None:
        """Test with dataset too small for outlier detection."""
        data = [1.0, 2.0, 100.0]
        outliers = detect_outliers(data)
        assert outliers == []  # Too small to detect

    def test_custom_factor(self) -> None:
        """Test with custom IQR factor."""
        data = [10.0, 11.0, 10.5, 10.2, 10.8, 15.0]
        # With default factor 1.5, 15.0 might not be an outlier
        outliers_default = detect_outliers(data, factor=1.5)
        # With stricter factor 1.0, more values become outliers
        outliers_strict = detect_outliers(data, factor=0.5)

        assert len(outliers_strict) >= len(outliers_default)


class TestComputeConfidenceInterval:
    """Tests for compute_confidence_interval function."""

    def test_basic_ci(self) -> None:
        """Test confidence interval with known data."""
        data = [10.0, 10.5, 9.5, 10.2, 9.8]
        lower, upper = compute_confidence_interval(data)

        mean = sum(data) / len(data)
        assert lower < mean < upper
        assert lower > 0
        assert upper > lower

    def test_single_value(self) -> None:
        """Test CI with single value."""
        data = [10.0]
        lower, upper = compute_confidence_interval(data)
        assert lower == upper == 10.0

    def test_empty_data(self) -> None:
        """Test CI with empty data."""
        lower, upper = compute_confidence_interval([])
        assert lower == upper == 0.0

    def test_ci_narrows_with_more_samples(self) -> None:
        """Verify CI narrows as sample size increases."""
        small_data = [10.0, 10.5, 9.5]
        large_data = [10.0, 10.5, 9.5, 10.2, 9.8, 10.1, 9.9, 10.3, 9.7, 10.0]

        _, upper_small = compute_confidence_interval(small_data)
        lower_small, _ = compute_confidence_interval(small_data)
        _, upper_large = compute_confidence_interval(large_data)
        lower_large, _ = compute_confidence_interval(large_data)

        ci_width_small = upper_small - lower_small
        ci_width_large = upper_large - lower_large

        assert ci_width_large < ci_width_small


class TestComputeStats:
    """Tests for compute_stats function."""

    def test_basic_stats(self) -> None:
        """Test comprehensive stats computation."""
        times = [0.1, 0.11, 0.09, 0.10, 0.105]
        stats = compute_stats(times)

        assert stats.mean == pytest.approx(0.101, rel=0.01)
        assert stats.median == 0.10
        assert stats.stddev > 0
        assert stats.cv > 0
        assert stats.min == 0.09
        assert stats.max == 0.11

    def test_cv_calculation(self) -> None:
        """Test coefficient of variation calculation."""
        # Data with known CV
        # Mean = 100, StdDev = 5, CV = 0.05 (5%)
        times = [95.0, 100.0, 105.0, 100.0, 100.0]
        stats = compute_stats(times)

        assert stats.cv == pytest.approx(0.04, rel=0.5)  # Approximately 4-5%

    def test_empty_times(self) -> None:
        """Test stats with empty input."""
        stats = compute_stats([])

        assert stats.mean == 0.0
        assert stats.median == 0.0
        assert stats.cv == 0.0
        assert len(stats.times) == 0

    def test_outlier_removal(self) -> None:
        """Test that outliers are detected and reported."""
        times = [10.0, 10.1, 9.9, 10.0, 10.2, 100.0, 1.0]
        stats = compute_stats(times, remove_outliers=True)

        assert 100.0 in stats.outliers or 1.0 in stats.outliers
        # Mean should be closer to 10 after outlier removal
        assert 9.0 < stats.mean < 11.0

    def test_preserves_original_times(self) -> None:
        """Test that original times are preserved in output."""
        times = [10.0, 10.1, 9.9, 100.0]
        stats = compute_stats(times)

        assert list(stats.times) == times


class TestRunUntilStable:
    """Tests for run_until_stable function."""

    def test_reaches_stability(self) -> None:
        """Test that stable data reaches target CV quickly."""
        call_count = 0

        def stable_runner() -> float:
            nonlocal call_count
            call_count += 1
            return 0.1  # Perfectly stable

        stats = run_until_stable(
            stable_runner,
            min_runs=5,
            max_runs=50,
            target_cv=0.01,
            warmup=2,
        )

        # Should stop early since CV is 0
        assert len(stats.times) <= 10
        assert stats.cv == 0.0  # Perfect stability
        assert call_count >= 2 + 5  # warmup + min_runs

    def test_continues_for_unstable_data(self) -> None:
        """Test that unstable data runs more iterations."""
        call_count = 0

        def unstable_runner() -> float:
            nonlocal call_count
            call_count += 1
            # Alternating values with high variance
            return 0.5 if call_count % 2 == 0 else 1.5

        stats = run_until_stable(
            unstable_runner,
            min_runs=5,
            max_runs=20,
            target_cv=0.01,
            warmup=2,
        )

        # Should run more iterations due to instability
        assert len(stats.times) > 5
        assert stats.cv > 0.01  # Won't reach target

    def test_respects_max_runs(self) -> None:
        """Test that max_runs limit is enforced."""
        call_count = 0

        def runner() -> float:
            nonlocal call_count
            call_count += 1
            return call_count * 0.1  # Increasing values = high CV

        stats = run_until_stable(
            runner,
            min_runs=5,
            max_runs=15,
            target_cv=0.001,  # Very strict target
            warmup=2,
        )

        # Should stop at max_runs even though CV not reached
        assert len(stats.times) == 15
        assert call_count == 2 + 15  # warmup + max_runs

    def test_warmup_not_included(self) -> None:
        """Test that warmup runs are not included in statistics."""
        times_recorded: list[float] = []

        def runner() -> float:
            t = len(times_recorded) * 0.01 + 0.1
            times_recorded.append(t)
            return t

        stats = run_until_stable(
            runner,
            min_runs=5,
            max_runs=10,
            target_cv=1.0,  # Easy target
            warmup=3,
        )

        # Stats should not include warmup values
        assert stats.times[0] >= 0.13  # First post-warmup value


class TestFormatStats:
    """Tests for format_stats function."""

    def test_format_ms(self) -> None:
        """Test formatting in milliseconds."""
        stats = BenchmarkStats(
            times=(0.485, 0.490, 0.480),
            mean=0.485,
            median=0.485,
            stddev=0.005,
            cv=0.0103,
            min=0.480,
            max=0.490,
            iqr=0.005,
            outliers=(),
            confidence_95=(0.480, 0.490),
            runs_to_stable=3,
        )

        formatted = format_stats(stats, unit="ms")
        assert "485.0ms" in formatted
        assert "5.0ms" in formatted
        assert "1.03%" in formatted
        assert "3 runs" in formatted

    def test_format_seconds(self) -> None:
        """Test formatting in seconds."""
        stats = BenchmarkStats(
            times=(0.485,),
            mean=0.485,
            median=0.485,
            stddev=0.005,
            cv=0.01,
            min=0.480,
            max=0.490,
            iqr=0.005,
            outliers=(),
            confidence_95=(0.480, 0.490),
            runs_to_stable=1,
        )

        formatted = format_stats(stats, unit="s")
        assert "0.5s" in formatted or "0.49s" in formatted


class TestBenchmarkStatsDataclass:
    """Tests for BenchmarkStats dataclass."""

    def test_is_frozen(self) -> None:
        """Test that BenchmarkStats is immutable."""
        stats = BenchmarkStats(
            times=(0.1, 0.2),
            mean=0.15,
            median=0.15,
            stddev=0.05,
            cv=0.33,
            min=0.1,
            max=0.2,
            iqr=0.1,
            outliers=(),
            confidence_95=(0.1, 0.2),
            runs_to_stable=2,
        )

        with pytest.raises(Exception):  # FrozenInstanceError
            stats.mean = 0.5  # type: ignore[misc]

    def test_default_values(self) -> None:
        """Test default values for optional fields."""
        stats = BenchmarkStats(
            times=(0.1,),
            mean=0.1,
            median=0.1,
            stddev=0.0,
            cv=0.0,
            min=0.1,
            max=0.1,
            iqr=0.0,
        )

        assert stats.outliers == ()
        assert stats.runs_to_stable == 0
