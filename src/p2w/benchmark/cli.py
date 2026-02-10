"""Command-line interface for the benchmark suite.

Provides the `p2w-benchmark` command with subcommands for:
- Running benchmarks
- Listing saved sessions
- Comparing sessions
- Showing available runtimes
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from p2w.benchmark.database import BenchmarkDatabase
from p2w.benchmark.runner import (
    BenchmarkProgress,
    BenchmarkRunner,
    format_results_table,
    load_suite_config,
)
from p2w.benchmark.runtimes import detect_runtimes

# Default paths
DEFAULT_SUITE_PATH = (
    Path(__file__).parent.parent.parent.parent
    / "programs"
    / "benchmarks-alioth"
    / "suite.yaml"
)
DEFAULT_DB_PATH = (
    Path(__file__).parent.parent.parent.parent
    / "programs"
    / "benchmarks-alioth"
    / "benchmark_results.db"
)


def cmd_run(args: argparse.Namespace) -> int:
    """Run benchmarks."""
    # Resolve suite path
    suite_path = Path(args.suite) if args.suite else DEFAULT_SUITE_PATH

    if not suite_path.exists():
        print(f"Error: Suite configuration not found: {suite_path}")
        print("Create suite.yaml or specify --suite path")
        return 1

    # Load suite configuration
    try:
        suite = load_suite_config(suite_path)
    except Exception as e:
        print(f"Error loading suite configuration: {e}")
        return 1

    # Detect runtimes
    runtimes = detect_runtimes()
    print("p2w Benchmark Suite v1.0")
    print("=" * 60)
    print("\nDetected runtimes:")

    # Native compilers
    available_native = []
    print("  Native compilers:")
    for name in ["gcc", "clang", "rustc", "zig"]:
        info = runtimes[name]
        status = "+" if info.available else "-"
        if info.available:
            print(f"    {name:<8} {info.version:<12} {status}")
            available_native.append(name)
            # zig-cc uses same binary as zig, so add it too
            if name == "zig":
                available_native.append("zig-cc")
        else:
            print(f"    {name:<8} {'not found':<12} {status}")

    # Python runtimes
    available_python = []
    print("  Python runtimes:")
    for name in ["cpython", "pypy"]:
        info = runtimes[name]
        status = "+" if info.available else "-"
        if info.available:
            print(f"    {name:<8} {info.version:<12} {status}")
            available_python.append(name)
        else:
            print(f"    {name:<8} {'not found':<12} {status}")

    # Node.js (WASM runtime)
    print("  WASM runtimes:")
    nodejs = runtimes["nodejs"]
    if nodejs.available:
        print(f"    nodejs   {nodejs.version:<12} +")
    else:
        print(f"    nodejs   {'not found':<12} -")

    print()

    # Filter native compilers
    if args.native:
        requested = [r.strip() for r in args.native.split(",")]
        # Handle zig-cc specially: it requires zig to be available
        filtered = []
        for r in requested:
            if r == "zig-cc" and "zig-cc" in available_native:
                filtered.append(r)
            elif r in available_native:
                filtered.append(r)
        available_native = filtered
    else:
        # Default to gcc only
        available_native = [r for r in ["gcc"] if r in available_native]

    # Filter Python runtimes
    if args.python:
        requested = [r.strip() for r in args.python.split(",")]
        available_python = [r for r in requested if r in available_python]

    # Progress callback
    def progress(p: BenchmarkProgress) -> None:
        print(
            f"  [{p.runtime}] {p.phase}...",
            end="\r",
            flush=True,
        )

    # Create runner
    runner = BenchmarkRunner(
        suite=suite,
        target_cv=args.cv_target,
        min_runs=args.min_runs,
        max_runs=args.max_runs,
        warmup=args.warmup,
        python_runtimes=available_python,
        native_compilers=available_native,
        timeout=args.timeout,
        progress_callback=progress if not args.quiet else None,
    )

    # Run benchmarks
    benchmark_filter = args.benchmark if hasattr(args, "benchmark") else None
    print(f"Running benchmarks (target CV: {args.cv_target * 100:.1f}%)...")
    print(f"  Native compilers: {', '.join(available_native) or 'none'}")
    print(f"  Python runtimes: {', '.join(available_python) or 'none'}")
    print(f"  WASM: {'nodejs' if nodejs.available else 'none'}")
    print()

    for config in suite.benchmarks:
        if not config.enabled:
            continue
        if benchmark_filter and config.name != benchmark_filter:
            continue
        print(f"Running: {config.name}")

    print()

    session = runner.run_all(benchmark_filter=benchmark_filter)

    # Clear progress line and print results
    print(" " * 50, end="\r")
    print(format_results_table(session))

    # Save if requested
    if args.save:
        db_path = Path(args.db) if args.db else DEFAULT_DB_PATH
        with BenchmarkDatabase(db_path) as db:
            if args.description:
                session.description = args.description
            session_id = db.save_session(session)
            print(f"\nResults saved to session #{session_id}")

    return 0


def cmd_runtimes(args: argparse.Namespace) -> int:
    """Show available runtimes."""
    runtimes = detect_runtimes()

    print("Available Runtimes")
    print("=" * 70)
    print(f"{'Type':<10} {'Name':<10} {'Version':<15} {'Status':<12} Path")
    print("-" * 70)

    # Native compilers
    for name in ["gcc", "clang", "rustc", "zig"]:
        info = runtimes[name]
        status = "available" if info.available else "not found"
        version = info.version if info.available else "-"
        path = info.path or "-"
        print(f"{'native':<10} {name:<10} {version:<15} {status:<12} {path}")

    # Python runtimes
    for name in ["cpython", "pypy"]:
        info = runtimes[name]
        status = "available" if info.available else "not found"
        version = info.version if info.available else "-"
        path = info.path or "-"
        print(f"{'python':<10} {name:<10} {version:<15} {status:<12} {path}")

    # WASM runtimes
    info = runtimes["nodejs"]
    status = "available" if info.available else "not found"
    version = info.version if info.available else "-"
    path = info.path or "-"
    print(f"{'wasm':<10} {'nodejs':<10} {version:<15} {status:<12} {path}")

    return 0


def cmd_list(args: argparse.Namespace) -> int:
    """List saved sessions."""
    db_path = Path(args.db) if args.db else DEFAULT_DB_PATH

    if not db_path.exists():
        print("No benchmark database found.")
        return 0

    with BenchmarkDatabase(db_path) as db:
        sessions = db.list_sessions()

        if not sessions:
            print("No benchmark sessions recorded yet.")
            return 0

        print("Saved Benchmark Sessions")
        print("=" * 80)
        print(f"{'ID':>5} {'Date':>20} {'Commit':>12} Description")
        print("-" * 80)

        for session_id, timestamp, description, git_commit in sessions:
            date_str = timestamp.strftime("%Y-%m-%d %H:%M")
            commit = git_commit[:12] if git_commit else "-"
            desc = description or ""
            print(f"{session_id:>5} {date_str:>20} {commit:>12} {desc}")

        print("-" * 80)
        print(f"Total: {len(sessions)} session(s)")

    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    """Compare two sessions."""
    db_path = Path(args.db) if args.db else DEFAULT_DB_PATH

    if not db_path.exists():
        print("No benchmark database found.")
        return 1

    with BenchmarkDatabase(db_path) as db:
        id1 = args.id1
        id2 = args.id2

        if id2 is None:
            # Compare with latest
            id2 = db.get_latest_session_id()
            if id2 is None:
                print("No sessions to compare with.")
                return 1
            if id1 == id2:
                print("Only one session exists.")
                return 1

        session1 = db.load_session(id1)
        session2 = db.load_session(id2)

        if not session1:
            print(f"Error: Session #{id1} not found.")
            return 1
        if not session2:
            print(f"Error: Session #{id2} not found.")
            return 1

        # Print comparison
        print("Benchmark Comparison")
        print("=" * 90)
        print(f"Session #{id1}: {session1.timestamp.strftime('%Y-%m-%d %H:%M')}")
        if session1.description:
            print(f"  Description: {session1.description}")
        if session1.git_commit:
            print(f"  Commit: {session1.git_commit}")
        print(f"Session #{id2}: {session2.timestamp.strftime('%Y-%m-%d %H:%M')}")
        if session2.description:
            print(f"  Description: {session2.description}")
        if session2.git_commit:
            print(f"  Commit: {session2.git_commit}")
        print("=" * 90)

        comparison = db.compare_sessions(id1, id2)

        print(
            f"\n{'Benchmark':<15} {'Runtime':<12} {'#' + str(id1):>10} "
            f"{'#' + str(id2):>10} {'Ratio':>10} {'Change':>10}"
        )
        print("-" * 70)

        for bench_name, runtime_data in sorted(comparison.items()):
            for runtime, (mean1, mean2, ratio) in sorted(runtime_data.items()):
                mean1_str = f"{mean1:.1f}ms"
                mean2_str = f"{mean2:.1f}ms" if mean2 > 0 else "-"
                ratio_str = f"{ratio:.2f}x" if ratio > 0 else "-"

                # Calculate percentage change
                if ratio > 0:
                    pct = (ratio - 1) * 100
                    if pct < -5:
                        change = f"{pct:.1f}% BETTER"
                    elif pct > 5:
                        change = f"+{pct:.1f}% WORSE"
                    else:
                        change = "~same"
                else:
                    change = "-"

                print(
                    f"{bench_name:<15} {runtime:<12} {mean1_str:>10} "
                    f"{mean2_str:>10} {ratio_str:>10} {change:>10}"
                )

        print("-" * 70)

    return 0


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="p2w-benchmark",
        description="Robust multi-runtime benchmark suite for p2w",
    )
    parser.add_argument(
        "--db",
        help="Path to benchmark database (default: programs/benchmarks-alioth/benchmark_results.db)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # run command
    run_parser = subparsers.add_parser("run", help="Run benchmarks")
    run_parser.add_argument(
        "--benchmark",
        help="Run only the specified benchmark",
    )
    run_parser.add_argument(
        "--python",
        help="Comma-separated list of Python runtimes (cpython,pypy)",
    )
    run_parser.add_argument(
        "--native",
        help="Comma-separated list of native compilers (gcc,clang,rustc,zig,zig-cc)",
    )
    run_parser.add_argument(
        "--cv-target",
        type=float,
        default=0.01,
        help="Target coefficient of variation (default: 0.01 = 1%%)",
    )
    run_parser.add_argument(
        "--min-runs",
        type=int,
        default=5,
        help="Minimum number of timed runs (default: 5)",
    )
    run_parser.add_argument(
        "--max-runs",
        type=int,
        default=50,
        help="Maximum number of timed runs (default: 50)",
    )
    run_parser.add_argument(
        "--warmup",
        type=int,
        default=3,
        help="Number of warmup runs (default: 3)",
    )
    run_parser.add_argument(
        "--timeout",
        type=float,
        default=120.0,
        help="Timeout per benchmark in seconds (default: 120)",
    )
    run_parser.add_argument(
        "--suite",
        help="Path to suite.yaml configuration",
    )
    run_parser.add_argument(
        "--save",
        action="store_true",
        help="Save results to database",
    )
    run_parser.add_argument(
        "-d",
        "--description",
        help="Description for this benchmark run",
    )
    run_parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress output",
    )
    run_parser.set_defaults(func=cmd_run)

    # runtimes command
    runtimes_parser = subparsers.add_parser("runtimes", help="Show available runtimes")
    runtimes_parser.set_defaults(func=cmd_runtimes)

    # list command
    list_parser = subparsers.add_parser("list", help="List saved sessions")
    list_parser.set_defaults(func=cmd_list)

    # compare command
    compare_parser = subparsers.add_parser("compare", help="Compare two sessions")
    compare_parser.add_argument(
        "id1",
        type=int,
        help="First session ID",
    )
    compare_parser.add_argument(
        "id2",
        type=int,
        nargs="?",
        help="Second session ID (default: latest)",
    )
    compare_parser.set_defaults(func=cmd_compare)

    return parser


def main() -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
