"""Benchmark orchestration and execution.

Provides the core benchmark runner that coordinates:
- Loading benchmark configurations
- Compiling Python to WASM
- Compiling and running native C/Rust/Zig code
- Running benchmarks on multiple runtimes
- Collecting and analyzing results
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import yaml

from p2w.benchmark.database import BenchmarkResult, Session, hash_output
from p2w.benchmark.runtimes import (
    RuntimeInfo,
    compile_c,
    compile_c_with_zig,
    compile_zig,
    detect_runtimes,
    run_native_multi,
    run_python_multi,
    run_wasm_nodejs_adaptive,
)
from p2w.benchmark.stats import BenchmarkStats, compute_stats


@dataclass
class BenchmarkConfig:
    """Configuration for a single benchmark.

    Attributes:
        name: Benchmark identifier.
        python_source: Path to Python source file.
        c_source: Path to C source file (optional).
        rust_source: Path to Rust source file (optional).
        zig_source: Path to Zig source file (optional).
        arg: Argument to pass (replaces hardcoded value in Python).
        native_args: Arguments to pass to native executables.
        main_call_old: Pattern to replace in Python source.
        main_call_new: Replacement pattern (uses {arg} placeholder).
        enabled: Whether benchmark is enabled.
    """

    name: str
    python_source: Path
    c_source: Path | None = None
    rust_source: Path | None = None
    zig_source: Path | None = None
    arg: str | None = None
    native_args: list[str] | None = None
    main_call_old: str | None = None
    main_call_new: str | None = None
    enabled: bool = True


@dataclass
class BenchmarkSuite:
    """Collection of benchmark configurations.

    Attributes:
        name: Suite name.
        benchmarks: List of benchmark configurations.
        base_path: Base path for source files.
        python_dir: Directory for Python sources.
        c_dir: Directory for C sources.
        rust_dir: Directory for Rust sources.
        zig_dir: Directory for Zig sources.
    """

    name: str
    benchmarks: list[BenchmarkConfig]
    base_path: Path
    python_dir: str = "python"
    c_dir: str = "gcc"
    rust_dir: str = "rust"
    zig_dir: str = "zig"


@dataclass
class BenchmarkRunResult:
    """Result of running a single benchmark on a single runtime.

    Attributes:
        benchmark: Benchmark name.
        runtime: Runtime name.
        output: Program output.
        stats: Timing statistics.
        compile_time: Compilation time in seconds (for compiled languages).
        error: Error message if failed.
    """

    benchmark: str
    runtime: str
    output: str
    stats: BenchmarkStats
    compile_time: float = 0.0
    error: str | None = None


@dataclass
class BenchmarkProgress:
    """Progress callback information.

    Attributes:
        benchmark: Current benchmark name.
        runtime: Current runtime name.
        phase: Current phase ("warmup", "timing", "compiling").
        runs_completed: Number of runs completed.
        total_runs: Total runs expected.
    """

    benchmark: str
    runtime: str
    phase: str
    runs_completed: int
    total_runs: int


# Type for progress callbacks
ProgressCallback = Callable[[BenchmarkProgress], None]


def load_suite_config(config_path: Path) -> BenchmarkSuite:
    """Load benchmark suite configuration from YAML.

    Args:
        config_path: Path to suite.yaml file.

    Returns:
        BenchmarkSuite configuration.
    """
    with Path(config_path).open() as f:
        data = yaml.safe_load(f)

    base_path = config_path.parent
    python_dir = data.get("python_dir", "python")
    c_dir = data.get("c_dir", "gcc")
    rust_dir = data.get("rust_dir", "rust")
    zig_dir = data.get("zig_dir", "zig")

    # Handle legacy format (source_dir)
    if "source_dir" in data:
        python_dir = data["source_dir"]

    benchmarks = []
    for bench_data in data.get("benchmarks", []):
        # Python source (required)
        python_source_name = bench_data.get("python_source") or bench_data.get("source")
        if not python_source_name:
            continue
        python_source = base_path / python_dir / python_source_name

        # C source (optional)
        c_source = None
        if "c_source" in bench_data:
            c_source = base_path / c_dir / bench_data["c_source"]

        # Rust source (optional)
        rust_source = None
        if "rust_source" in bench_data:
            rust_source = base_path / rust_dir / bench_data["rust_source"]

        # Zig source (optional)
        zig_source = None
        if "zig_source" in bench_data:
            zig_source = base_path / zig_dir / bench_data["zig_source"]

        # Native args - use arg if provided, for C programs that take command-line args
        native_args = None
        if bench_data.get("arg"):
            native_args = [bench_data["arg"]]

        config = BenchmarkConfig(
            name=bench_data["name"],
            python_source=python_source,
            c_source=c_source,
            rust_source=rust_source,
            zig_source=zig_source,
            arg=bench_data.get("arg"),
            native_args=native_args,
            main_call_old=bench_data.get("main_call_old"),
            main_call_new=bench_data.get("main_call_new"),
            enabled=bench_data.get("enabled", True),
        )
        benchmarks.append(config)

    return BenchmarkSuite(
        name=data.get("name", "benchmarks"),
        benchmarks=benchmarks,
        base_path=base_path,
        python_dir=python_dir,
        c_dir=c_dir,
        rust_dir=rust_dir,
        zig_dir=zig_dir,
    )


def prepare_python_source(config: BenchmarkConfig) -> str:
    """Prepare Python source with correct argument.

    Args:
        config: Benchmark configuration.

    Returns:
        Modified source code.
    """
    source = config.python_source.read_text()

    if config.arg and config.main_call_old and config.main_call_new:
        new_pattern = config.main_call_new.format(arg=config.arg)
        source = source.replace(config.main_call_old, new_pattern)

    return source


def compile_to_wasm(source: str) -> tuple[bytes, float, str | None]:
    """Compile Python source to WASM.

    Args:
        source: Python source code.

    Returns:
        Tuple of (wasm_bytes, compile_time, error_or_none).
    """
    import time

    from p2w.compiler import compile_to_wat
    from p2w.runner import wat_to_wasm

    start = time.perf_counter()
    try:
        wat_code = compile_to_wat(source)
        wasm_bytes = wat_to_wasm(wat_code)
        elapsed = time.perf_counter() - start
        return wasm_bytes, elapsed, None
    except Exception as e:
        elapsed = time.perf_counter() - start
        return b"", elapsed, str(e)


@dataclass
class BenchmarkRunner:
    """Main benchmark runner.

    Attributes:
        suite: Benchmark suite configuration.
        target_cv: Target coefficient of variation.
        min_runs: Minimum number of runs.
        max_runs: Maximum number of runs.
        warmup: Number of warmup runs.
        python_runtimes: Python runtimes to test.
        native_compilers: Native compilers to test.
        timeout: Timeout per benchmark in seconds.
        progress_callback: Optional callback for progress updates.
    """

    suite: BenchmarkSuite
    target_cv: float = 0.01
    min_runs: int = 5
    max_runs: int = 50
    warmup: int = 3
    python_runtimes: list[str] = field(default_factory=lambda: ["cpython", "pypy"])
    native_compilers: list[str] = field(default_factory=lambda: ["gcc"])
    timeout: float = 120.0
    progress_callback: ProgressCallback | None = None

    def _run_python_benchmark(
        self,
        config: BenchmarkConfig,
        source: str,
        runtime_name: str,
        runtimes: dict[str, RuntimeInfo],
    ) -> BenchmarkRunResult | None:
        """Run benchmark on a Python runtime."""
        info = runtimes.get(runtime_name)
        if not info or not info.available:
            return None

        if self.progress_callback:
            self.progress_callback(
                BenchmarkProgress(
                    benchmark=config.name,
                    runtime=runtime_name,
                    phase="timing",
                    runs_completed=0,
                    total_runs=self.min_runs,
                )
            )

        try:
            output, stats = run_python_multi(
                source,
                runtime=runtime_name,
                warmup=self.warmup,
                runs=self.min_runs,
                timeout=self.timeout,
            )
            return BenchmarkRunResult(
                benchmark=config.name,
                runtime=runtime_name,
                output=output,
                stats=stats,
            )
        except Exception as e:
            return BenchmarkRunResult(
                benchmark=config.name,
                runtime=runtime_name,
                output="",
                stats=compute_stats([]),
                error=str(e),
            )

    def _run_native_benchmark(
        self,
        config: BenchmarkConfig,
        compiler: str,
        runtimes: dict[str, RuntimeInfo],
    ) -> BenchmarkRunResult | None:
        """Run benchmark with a native compiler (GCC, Clang, Rust, Zig)."""
        import tempfile

        # Determine source file and runtime name
        if compiler in ("gcc", "clang"):
            source_path = config.c_source
            runtime_name = compiler
            runtime_key = compiler
        elif compiler == "zig-cc":
            # Use Zig's C compiler to compile C source
            source_path = config.c_source
            runtime_name = "zig-cc"
            runtime_key = "zig"  # Use zig runtime info
        elif compiler == "zig":
            # Native Zig source
            source_path = config.zig_source
            runtime_name = "zig"
            runtime_key = "zig"
        elif compiler == "rustc":
            source_path = config.rust_source
            runtime_name = "rustc"
            runtime_key = "rustc"
        else:
            return None

        if not source_path or not source_path.exists():
            return None

        compiler_info = runtimes.get(runtime_key)
        if not compiler_info or not compiler_info.available:
            return None

        if self.progress_callback:
            self.progress_callback(
                BenchmarkProgress(
                    benchmark=config.name,
                    runtime=runtime_name,
                    phase="compiling",
                    runs_completed=0,
                    total_runs=self.min_runs,
                )
            )

        # Compile
        with tempfile.NamedTemporaryFile(delete=False, suffix="") as tmp:
            exe_path = Path(tmp.name)

        try:
            if compiler == "rustc":
                from p2w.benchmark.runtimes import compile_rust

                success, compile_time, error = compile_rust(source_path, exe_path)
            elif compiler == "zig":
                success, compile_time, error = compile_zig(source_path, exe_path)
            elif compiler == "zig-cc":
                success, compile_time, error = compile_c_with_zig(source_path, exe_path)
            else:
                success, compile_time, error = compile_c(
                    source_path, exe_path, compiler=compiler
                )

            if not success:
                return BenchmarkRunResult(
                    benchmark=config.name,
                    runtime=runtime_name,
                    output="",
                    stats=compute_stats([]),
                    compile_time=compile_time,
                    error=error or "Compilation failed",
                )

            if self.progress_callback:
                self.progress_callback(
                    BenchmarkProgress(
                        benchmark=config.name,
                        runtime=runtime_name,
                        phase="timing",
                        runs_completed=0,
                        total_runs=self.min_runs,
                    )
                )

            # Run
            output, stats = run_native_multi(
                exe_path,
                args=config.native_args,
                warmup=self.warmup,
                runs=self.min_runs,
                timeout=self.timeout,
            )

            return BenchmarkRunResult(
                benchmark=config.name,
                runtime=runtime_name,
                output=output,
                stats=stats,
                compile_time=compile_time,
            )

        except Exception as e:
            return BenchmarkRunResult(
                benchmark=config.name,
                runtime=runtime_name,
                output="",
                stats=compute_stats([]),
                error=str(e),
            )
        finally:
            exe_path.unlink(missing_ok=True)

    def _run_wasm_benchmark(
        self,
        config: BenchmarkConfig,
        source: str,
        runtimes: dict[str, RuntimeInfo],
    ) -> BenchmarkRunResult | None:
        """Run benchmark as p2w-compiled WASM."""
        nodejs_info = runtimes.get("nodejs")
        if not nodejs_info or not nodejs_info.available:
            return None

        if self.progress_callback:
            self.progress_callback(
                BenchmarkProgress(
                    benchmark=config.name,
                    runtime="p2w-nodejs",
                    phase="compiling",
                    runs_completed=0,
                    total_runs=self.min_runs,
                )
            )

        wasm_bytes, compile_time, error = compile_to_wasm(source)

        if error:
            return BenchmarkRunResult(
                benchmark=config.name,
                runtime="p2w-nodejs",
                output="",
                stats=compute_stats([]),
                compile_time=compile_time,
                error=error,
            )

        if self.progress_callback:
            self.progress_callback(
                BenchmarkProgress(
                    benchmark=config.name,
                    runtime="p2w-nodejs",
                    phase="timing",
                    runs_completed=0,
                    total_runs=self.min_runs,
                )
            )

        try:
            output, stats = run_wasm_nodejs_adaptive(
                wasm_bytes,
                min_runs=self.min_runs,
                max_runs=self.max_runs,
                target_cv=self.target_cv,
                warmup=self.warmup,
                timeout=self.timeout * 2,
            )
            return BenchmarkRunResult(
                benchmark=config.name,
                runtime="p2w-nodejs",
                output=output,
                stats=stats,
                compile_time=compile_time,
            )
        except Exception as e:
            return BenchmarkRunResult(
                benchmark=config.name,
                runtime="p2w-nodejs",
                output="",
                stats=compute_stats([]),
                compile_time=compile_time,
                error=str(e),
            )

    def run_benchmark(
        self,
        config: BenchmarkConfig,
        runtimes: dict[str, RuntimeInfo],
    ) -> list[BenchmarkRunResult]:
        """Run a single benchmark on all available runtimes.

        Args:
            config: Benchmark configuration.
            runtimes: Available runtimes.

        Returns:
            List of results for each runtime.
        """
        results: list[BenchmarkRunResult] = []
        source = prepare_python_source(config)

        # Run on native compilers first (baseline)
        for compiler in self.native_compilers:
            result = self._run_native_benchmark(config, compiler, runtimes)
            if result:
                results.append(result)

        # Run on Python runtimes
        for runtime_name in self.python_runtimes:
            result = self._run_python_benchmark(config, source, runtime_name, runtimes)
            if result:
                results.append(result)

        # Run on p2w/WASM
        result = self._run_wasm_benchmark(config, source, runtimes)
        if result:
            results.append(result)

        return results

    def run_all(
        self,
        benchmark_filter: str | None = None,
    ) -> Session:
        """Run all benchmarks in the suite.

        Args:
            benchmark_filter: If provided, only run this benchmark.

        Returns:
            Session with all results.
        """
        runtimes = detect_runtimes()
        all_results: list[BenchmarkResult] = []

        for config in self.suite.benchmarks:
            if not config.enabled:
                continue
            if benchmark_filter and config.name != benchmark_filter:
                continue

            run_results = self.run_benchmark(config, runtimes)

            for result in run_results:
                if not result.error:
                    all_results.append(
                        BenchmarkResult(
                            benchmark=result.benchmark,
                            runtime=result.runtime,
                            stats=result.stats,
                            output_hash=hash_output(result.output),
                        )
                    )

        return Session(
            timestamp=datetime.now(),
            description=None,
            git_commit=None,
            results=all_results,
            runtime_info=runtimes,
        )


def _geometric_mean(values: list[float]) -> float:
    """Compute geometric mean of positive values."""
    if not values:
        return 0.0
    import math

    log_sum = sum(math.log(v) for v in values if v > 0)
    return math.exp(log_sum / len(values)) if values else 0.0


def format_results_table(session: Session) -> str:
    """Format benchmark results as a table.

    Args:
        session: Session with results.

    Returns:
        Formatted table string.
    """
    lines = []

    # Header
    lines.append("=" * 100)
    lines.append("BENCHMARK RESULTS")
    lines.append("=" * 100)

    # Group results by benchmark
    benchmarks: dict[str, dict[str, BenchmarkResult]] = {}
    for result in session.results:
        if result.benchmark not in benchmarks:
            benchmarks[result.benchmark] = {}
        benchmarks[result.benchmark][result.runtime] = result

    # Collect all runtimes that have results
    all_runtimes: set[str] = set()
    for runtime_results in benchmarks.values():
        all_runtimes.update(runtime_results.keys())

    # Order runtimes: native compilers first, then Python, then p2w
    runtime_order = [
        "gcc",
        "clang",
        "zig-cc",
        "zig",
        "rustc",
        "cpython",
        "pypy",
        "p2w-nodejs",
    ]
    ordered_runtimes = [r for r in runtime_order if r in all_runtimes]

    # Results table with all runtimes as columns
    lines.append("\nExecution times (ms):")
    header = f"{'Benchmark':<15}"
    for runtime in ordered_runtimes:
        header += f" {runtime:>12}"
    lines.append(header)
    lines.append("-" * (15 + 13 * len(ordered_runtimes)))

    for bench_name, runtime_results in sorted(benchmarks.items()):
        row = f"{bench_name:<15}"
        for runtime in ordered_runtimes:
            if runtime in runtime_results:
                mean_ms = runtime_results[runtime].stats.mean * 1000
                row += f" {mean_ms:>12.1f}"
            else:
                row += f" {'-':>12}"
        lines.append(row)

    # p2w performance comparison table
    if "p2w-nodejs" in all_runtimes:
        lines.append("\n" + "=" * 80)
        lines.append(
            "p2w PERFORMANCE (speedup = how much faster p2w is, <1 means slower)"
        )
        lines.append("=" * 80)

        # Comparison runtimes (exclude p2w-nodejs itself)
        compare_runtimes = [r for r in ordered_runtimes if r != "p2w-nodejs"]

        header = f"{'Benchmark':<15}"
        for runtime in compare_runtimes:
            header += f" {'vs ' + runtime:>12}"
        lines.append(header)
        lines.append("-" * (15 + 13 * len(compare_runtimes)))

        # Collect ratios for geometric mean
        ratio_by_runtime: dict[str, list[float]] = {r: [] for r in compare_runtimes}

        for bench_name, runtime_results in sorted(benchmarks.items()):
            p2w_result = runtime_results.get("p2w-nodejs")
            if not p2w_result or p2w_result.stats.mean == 0:
                continue

            p2w_mean = p2w_result.stats.mean
            row = f"{bench_name:<15}"

            for runtime in compare_runtimes:
                if (
                    runtime in runtime_results
                    and runtime_results[runtime].stats.mean > 0
                ):
                    other_mean = runtime_results[runtime].stats.mean
                    # Speedup: how much faster p2w is (>1 = p2w faster, <1 = p2w slower)
                    speedup = other_mean / p2w_mean
                    ratio_by_runtime[runtime].append(speedup)
                    row += f" {speedup:>12.2f}x"
                else:
                    row += f" {'-':>12}"
            lines.append(row)

        # Geometric mean of speedups
        lines.append("-" * (15 + 13 * len(compare_runtimes)))
        geomean_row = f"{'GEOM. MEAN':<15}"
        for runtime in compare_runtimes:
            if ratio_by_runtime[runtime]:
                gm = _geometric_mean(ratio_by_runtime[runtime])
                geomean_row += f" {gm:>12.2f}x"
            else:
                geomean_row += f" {'-':>12}"
        lines.append(geomean_row)

        # Summary interpretation
        lines.append("\n" + "-" * 80)
        lines.append("Summary:")
        for runtime in compare_runtimes:
            if ratio_by_runtime[runtime]:
                gm = _geometric_mean(ratio_by_runtime[runtime])
                if gm >= 1:
                    lines.append(
                        f"  p2w is {gm:.2f}x FASTER than {runtime} (geometric mean)"
                    )
                else:
                    lines.append(
                        f"  p2w is {1 / gm:.2f}x SLOWER than {runtime} (geometric mean)"
                    )

    return "\n".join(lines)
