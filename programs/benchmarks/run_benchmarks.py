#!/usr/bin/env python3
"""Benchmark comparison tool: p2w vs CPython.

Runs benchmark programs and compares execution time between
p2w-compiled WASM and CPython.

Usage:
    python run_benchmarks.py              # Run benchmarks (no save)
    python run_benchmarks.py --save       # Run and save to database
    python run_benchmarks.py --list       # List saved sessions
    python run_benchmarks.py --compare 1  # Compare run #1 with latest
    python run_benchmarks.py --compare 1 3  # Compare run #1 with run #3
    python run_benchmarks.py --warmup 3 --runs 10  # Custom warmup/runs
"""

from __future__ import annotations

import argparse
import json
import math
import sqlite3
import statistics
import subprocess
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from p2w.compiler import compile_to_wat
from p2w.runner import wat_to_wasm

# Default benchmark configuration
DEFAULT_WARMUP_RUNS = 3
DEFAULT_TIMED_RUNS = 10

# Database path (alongside the benchmark scripts)
DB_PATH = Path(__file__).parent / "benchmark_results.db"


def init_database() -> sqlite3.Connection:
    """Initialize the SQLite database and return a connection."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            description TEXT
        )
    """)

    # Create results table (v2 with statistics)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            benchmark_name TEXT NOT NULL,
            cpython_time_ms REAL,
            cpython_min_ms REAL,
            cpython_median_ms REAL,
            cpython_stddev_ms REAL,
            p2w_compile_time_ms REAL,
            p2w_run_time_ms REAL,
            p2w_min_ms REAL,
            p2w_median_ms REAL,
            p2w_stddev_ms REAL,
            speedup REAL,
            speedup_min REAL,
            output_match INTEGER,
            error TEXT,
            warmup_runs INTEGER,
            timed_runs INTEGER,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
    """)

    conn.commit()
    return conn


def save_session(
    conn: sqlite3.Connection, results: list[dict], description: str | None = None
) -> int:
    """Save a benchmark session to the database. Returns the session ID."""
    cursor = conn.cursor()

    # Create session
    timestamp = datetime.now().isoformat()
    cursor.execute(
        "INSERT INTO sessions (timestamp, description) VALUES (?, ?)",
        (timestamp, description),
    )
    session_id = cursor.lastrowid

    # Save results - use MIN as primary (more stable for benchmarking)
    for r in results:
        cursor.execute(
            """
            INSERT INTO results (
                session_id, benchmark_name, cpython_time_ms,
                cpython_min_ms, cpython_median_ms, cpython_stddev_ms,
                p2w_compile_time_ms, p2w_run_time_ms,
                p2w_min_ms, p2w_median_ms, p2w_stddev_ms,
                speedup, speedup_min, output_match, error,
                warmup_runs, timed_runs
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                r["name"],
                r["cpython_min"] * 1000,  # Use min as primary (more stable)
                r["cpython_min"] * 1000,
                r["cpython_median"] * 1000,
                r["cpython_stddev"] * 1000 if r["cpython_stddev"] else 0,
                r["p2w_compile_time"] * 1000,
                r["p2w_min"] * 1000,  # Use min as primary (more stable)
                r["p2w_min"] * 1000,
                r["p2w_median"] * 1000,
                r["p2w_stddev"] * 1000 if r["p2w_stddev"] else 0,
                r["speedup_min"],  # Use min speedup as primary
                r["speedup_min"],
                1 if r["output_match"] else 0,
                r["p2w_error"],
                r["warmup_runs"],
                r["timed_runs"],
            ),
        )

    conn.commit()
    return session_id


def geometric_mean(values: list[float]) -> float:
    """Compute geometric mean of positive values.

    Geometric mean is appropriate for ratios/speedups because it treats
    "2x faster" and "2x slower" symmetrically.
    """
    if not values:
        return 0
    # Use log to avoid overflow with large products
    log_sum = sum(math.log(v) for v in values if v > 0)
    count = sum(1 for v in values if v > 0)
    return math.exp(log_sum / count) if count > 0 else 0


def list_sessions(conn: sqlite3.Connection) -> None:
    """List all saved benchmark sessions."""
    cursor = conn.cursor()
    # Get sessions with their speedups for geometric mean calculation
    cursor.execute("""
        SELECT s.id, s.timestamp, s.description
        FROM sessions s
        ORDER BY s.id DESC
    """)

    sessions = cursor.fetchall()
    if not sessions:
        print("No benchmark sessions recorded yet.")
        return

    print("\n" + "=" * 80)
    print("SAVED BENCHMARK SESSIONS")
    print("=" * 80)
    print(f"{'ID':>5} {'Date':>20} {'Benchmarks':>12} {'Geomean':>12}  Description")
    print("-" * 80)

    for session_id, timestamp, description in sessions:
        # Get speedups for this session
        cursor.execute(
            "SELECT speedup FROM results WHERE session_id = ? AND speedup > 0",
            (session_id,),
        )
        speedups = [row[0] for row in cursor.fetchall()]
        count = len(speedups)
        geomean = geometric_mean(speedups)

        # Parse and format timestamp
        dt = datetime.fromisoformat(timestamp)
        date_str = dt.strftime("%Y-%m-%d %H:%M")
        desc_str = description or ""
        speedup_str = f"{geomean:.2f}x" if geomean else "-"
        print(
            f"{session_id:>5} {date_str:>20} {count:>12} {speedup_str:>12}  {desc_str}"
        )

    print("-" * 80)
    print(f"\nTotal: {len(sessions)} session(s)")
    print("Note: Geomean = geometric mean of speedups (appropriate for ratios)")


def get_session_results(conn: sqlite3.Connection, session_id: int) -> dict[str, dict]:
    """Get results for a specific session as a dict keyed by benchmark name."""
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT benchmark_name, cpython_time_ms, p2w_compile_time_ms,
               p2w_run_time_ms, speedup, output_match, error
        FROM results
        WHERE session_id = ?
        """,
        (session_id,),
    )

    results = {}
    for row in cursor.fetchall():
        name, cpython_ms, compile_ms, run_ms, speedup, match, error = row
        results[name] = {
            "cpython_time_ms": cpython_ms,
            "p2w_compile_time_ms": compile_ms,
            "p2w_run_time_ms": run_ms,
            "speedup": speedup,
            "output_match": bool(match),
            "error": error,
        }
    return results


def get_session_info(
    conn: sqlite3.Connection, session_id: int
) -> tuple[str, str | None] | None:
    """Get session timestamp and description."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT timestamp, description FROM sessions WHERE id = ?",
        (session_id,),
    )
    row = cursor.fetchone()
    return row if row else None


def get_latest_session_id(conn: sqlite3.Connection) -> int | None:
    """Get the ID of the most recent session."""
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(id) FROM sessions")
    row = cursor.fetchone()
    return row[0] if row and row[0] else None


def compare_sessions(conn: sqlite3.Connection, id1: int, id2: int) -> None:
    """Compare two benchmark sessions."""
    info1 = get_session_info(conn, id1)
    info2 = get_session_info(conn, id2)

    if not info1:
        print(f"Error: Session #{id1} not found.")
        return
    if not info2:
        print(f"Error: Session #{id2} not found.")
        return

    results1 = get_session_results(conn, id1)
    results2 = get_session_results(conn, id2)

    if not results1:
        print(f"Error: No results found for session #{id1}.")
        return
    if not results2:
        print(f"Error: No results found for session #{id2}.")
        return

    # Format timestamps
    dt1 = datetime.fromisoformat(info1[0])
    dt2 = datetime.fromisoformat(info2[0])
    date1 = dt1.strftime("%Y-%m-%d %H:%M")
    date2 = dt2.strftime("%Y-%m-%d %H:%M")

    print("\n" + "=" * 90)
    print("BENCHMARK COMPARISON")
    print("=" * 90)
    print(f"Run #{id1}: {date1}" + (f" - {info1[1]}" if info1[1] else ""))
    print(f"Run #{id2}: {date2}" + (f" - {info2[1]}" if info2[1] else ""))
    print("=" * 90)
    print(
        f"{'Benchmark':<15} {'Run #' + str(id1):>12} {'Run #' + str(id2):>12} "
        f"{'Ratio':>12} {'Change':>10}"
    )
    print("-" * 90)

    all_names = sorted(set(results1.keys()) | set(results2.keys()))

    speedups1 = []
    speedups2 = []

    for name in all_names:
        r1 = results1.get(name)
        r2 = results2.get(name)

        if r1 and r2 and r1["speedup"] and r2["speedup"]:
            speedup1 = r1["speedup"]
            speedup2 = r2["speedup"]
            # For ratios, use ratio of speedups (speedup2/speedup1) to show relative change
            ratio = speedup2 / speedup1
            pct_change = (ratio - 1) * 100

            # Color indicator
            if pct_change > 5:
                indicator = "+"
            elif pct_change < -5:
                indicator = "-"
            else:
                indicator = "="

            print(
                f"{name:<15} {speedup1:>11.2f}x {speedup2:>11.2f}x "
                f"{ratio:>11.2f}x {pct_change:>+9.1f}% {indicator}"
            )

            speedups1.append(speedup1)
            speedups2.append(speedup2)
        elif r1 and not r2:
            speedup1 = r1["speedup"] if r1["speedup"] else 0
            print(f"{name:<15} {speedup1:>11.2f}x {'N/A':>12} {'-':>12} {'-':>10}")
        elif r2 and not r1:
            speedup2 = r2["speedup"] if r2["speedup"] else 0
            print(f"{name:<15} {'N/A':>12} {speedup2:>11.2f}x {'-':>12} {'-':>10}")

    print("-" * 90)

    if speedups1 and speedups2:
        geomean1 = geometric_mean(speedups1)
        geomean2 = geometric_mean(speedups2)
        ratio = geomean2 / geomean1 if geomean1 else 0
        pct_change = (ratio - 1) * 100 if ratio else 0
        print(
            f"{'GEOMEAN':<15} {geomean1:>11.2f}x {geomean2:>11.2f}x "
            f"{ratio:>11.2f}x {pct_change:>+9.1f}%"
        )

    print("\nLegend: + = improved (>5%), - = regressed (>5%), = = stable")
    print("Note: 'Ratio' column shows Run2/Run1 (>1 = faster in Run2)")


@dataclass
class TimingStats:
    """Statistics from multiple benchmark runs."""

    times: list[float]
    min: float
    max: float
    mean: float
    median: float
    stddev: float | None  # None if only 1 run

    @classmethod
    def from_times(cls, times: list[float]) -> "TimingStats":
        """Create stats from a list of times."""
        if not times:
            return cls([], 0, 0, 0, 0, None)
        return cls(
            times=times,
            min=min(times),
            max=max(times),
            mean=statistics.mean(times),
            median=statistics.median(times),
            stddev=statistics.stdev(times) if len(times) > 1 else None,
        )


def run_cpython_once(source: str) -> tuple[float, str]:
    """Run Python source with CPython once, return (time, output)."""
    start = time.perf_counter()
    result = subprocess.run(
        ["python", "-c", source],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    elapsed = time.perf_counter() - start
    return elapsed, result.stdout


def run_cpython(source: str, warmup: int, runs: int) -> tuple[TimingStats, str]:
    """Run Python source with CPython multiple times, return (stats, output).

    Args:
        source: Python source code to run
        warmup: Number of warmup runs (discarded)
        runs: Number of timed runs
    """
    output = ""

    # Warmup runs (discard results)
    for _ in range(warmup):
        _, output = run_cpython_once(source)

    # Timed runs
    times = []
    for _ in range(runs):
        elapsed, output = run_cpython_once(source)
        times.append(elapsed)

    return TimingStats.from_times(times), output


def compile_p2w(source: str) -> tuple[float, bytes]:
    """Compile Python source to WASM, return (compile_time, wasm_bytes)."""
    compile_start = time.perf_counter()
    wat = compile_to_wat(source)
    wasm = wat_to_wasm(wat)
    compile_time = time.perf_counter() - compile_start
    return compile_time, wasm


def run_p2w(source: str, warmup: int, runs: int) -> tuple[float, TimingStats, str]:
    """Run Python source with p2w multiple times, return (compile_time, run_stats, output).

    Runs all iterations in a single Node.js process to properly warm up V8's JIT.

    Args:
        source: Python source code to run
        warmup: Number of warmup runs (discarded)
        runs: Number of timed runs
    """
    # Compile once
    compile_time, wasm = compile_p2w(source)

    # Write WASM to temp file
    with tempfile.NamedTemporaryFile(suffix=".wasm", delete=False) as wasm_file:
        wasm_file.write(wasm)
        wasm_path = Path(wasm_file.name)

    total_iterations = warmup + runs

    # Create runner script that runs multiple iterations in one process
    # This properly warms up V8's JIT compiler
    runner_script = f"""
import {{ readFileSync }} from 'fs';
const wasmBuffer = readFileSync('{wasm_path}');

const WARMUP = {warmup};
const RUNS = {runs};

// Compile WASM module once (outside timing)
const module = await WebAssembly.compile(wasmBuffer);

const times = [];
let lastOutput = '';

for (let iter = 0; iter < WARMUP + RUNS; iter++) {{
  const outputBytes = [];
  let wasmMemory = null;

  const importObject = {{
    env: {{
      write_char: (byte) => {{ outputBytes.push(byte); }},
      write_i32: (value) => {{ const str = value.toString(); for (let i = 0; i < str.length; i++) outputBytes.push(str.charCodeAt(i)); }},
      write_i64: (value) => {{ const str = value.toString(); for (let i = 0; i < str.length; i++) outputBytes.push(str.charCodeAt(i)); }},
      write_f64: (value) => {{ const str = value.toString(); for (let i = 0; i < str.length; i++) outputBytes.push(str.charCodeAt(i)); }},
      f64_to_string: (value, offset) => {{ const str = value.toString(); const bytes = new TextEncoder().encode(str); const mem = new Uint8Array(wasmMemory.buffer); mem.set(bytes, offset); return bytes.length; }},
      f64_format_precision: (value, precision, offset) => {{ const str = value.toFixed(precision); const bytes = new TextEncoder().encode(str); const mem = new Uint8Array(wasmMemory.buffer); mem.set(bytes, offset); return bytes.length; }},
      math_pow: (base, exp) => Math.pow(base, exp),
    }},
    js: {{
      console_log: () => {{}}, alert: () => {{}}, get_element_by_id: () => 0, create_element: () => 0, query_selector: () => 0,
      get_context: () => 0, canvas_fill_rect: () => {{}}, canvas_fill_text: () => {{}}, canvas_begin_path: () => {{}},
      canvas_move_to: () => {{}}, canvas_line_to: () => {{}}, canvas_stroke: () => {{}}, canvas_set_fill_style: () => {{}},
      canvas_set_stroke_style: () => {{}}, canvas_set_line_width: () => {{}}, canvas_set_font: () => {{}},
      set_text_content: () => {{}}, get_text_content: () => 0, set_inner_html: () => {{}}, get_inner_html: () => 0,
      get_property: () => 0, set_property: () => {{}}, get_value: () => 0, set_value: () => {{}},
      append_child: () => {{}}, remove_child: () => {{}}, set_attribute: () => {{}},
      add_class: () => {{}}, remove_class: () => {{}}, toggle_class: () => {{}},
      add_event_listener: () => {{}}, prevent_default: () => {{}}, call_method: () => 0,
    }},
  }};

  // Time only the instantiation and execution
  const start = performance.now();
  const instance = await WebAssembly.instantiate(module, importObject);
  wasmMemory = instance.exports.memory;
  instance.exports._start();
  const elapsed = performance.now() - start;

  // Only record times after warmup
  if (iter >= WARMUP) {{
    times.push(elapsed);
  }}

  lastOutput = new TextDecoder('utf-8').decode(new Uint8Array(outputBytes));
}}

// Output times as JSON array, then the program output
console.log('__TIMES__:' + JSON.stringify(times));
process.stdout.write(lastOutput);
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".mjs", delete=False) as js_file:
        js_file.write(runner_script)
        js_path = Path(js_file.name)

    try:
        result = subprocess.run(
            ["node", str(js_path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        # Extract times and output
        lines = result.stdout.split("\n")
        times = []
        output_lines = []
        for line in lines:
            if line.startswith("__TIMES__:"):
                times_ms = json.loads(line.split(":", 1)[1])
                times = [t / 1000 for t in times_ms]  # Convert to seconds
            else:
                output_lines.append(line)

        return compile_time, TimingStats.from_times(times), "\n".join(output_lines)
    finally:
        wasm_path.unlink(missing_ok=True)
        js_path.unlink(missing_ok=True)


def run_benchmark(name: str, source: str, warmup: int, runs: int) -> dict:
    """Run a single benchmark and return results.

    Args:
        name: Benchmark name
        source: Python source code
        warmup: Number of warmup runs
        runs: Number of timed runs
    """
    print(f"Running {name} ({warmup} warmup + {runs} timed runs)...")

    # Run CPython
    cpython_stats, cpython_output = run_cpython(source, warmup, runs)

    # Run p2w
    try:
        p2w_compile_time, p2w_stats, p2w_output = run_p2w(source, warmup, runs)
        p2w_error = None
    except Exception as e:
        p2w_compile_time = 0
        p2w_stats = TimingStats.from_times([])
        p2w_output = ""
        p2w_error = str(e)

    # Verify output matches
    output_match = cpython_output.strip() == p2w_output.strip()

    # Calculate speedups (using median and min)
    speedup_median = (
        cpython_stats.median / p2w_stats.median if p2w_stats.median > 0 else 0
    )
    speedup_min = cpython_stats.min / p2w_stats.min if p2w_stats.min > 0 else 0

    return {
        "name": name,
        # CPython stats
        "cpython_min": cpython_stats.min,
        "cpython_median": cpython_stats.median,
        "cpython_mean": cpython_stats.mean,
        "cpython_stddev": cpython_stats.stddev,
        "cpython_times": cpython_stats.times,
        # p2w stats
        "p2w_compile_time": p2w_compile_time,
        "p2w_min": p2w_stats.min,
        "p2w_median": p2w_stats.median,
        "p2w_mean": p2w_stats.mean,
        "p2w_stddev": p2w_stats.stddev,
        "p2w_times": p2w_stats.times,
        # Comparison
        "output_match": output_match,
        "p2w_error": p2w_error,
        "speedup_median": speedup_median,
        "speedup_min": speedup_min,
        # Config
        "warmup_runs": warmup,
        "timed_runs": runs,
    }


def print_results(results: list[dict]) -> None:
    """Print benchmark results in a table format."""
    if not results:
        print("No results to display.")
        return

    warmup = results[0]["warmup_runs"]
    runs = results[0]["timed_runs"]

    print("\n" + "=" * 85)
    print(f"BENCHMARK RESULTS ({warmup} warmup + {runs} timed runs, showing min)")
    print("=" * 85)
    print(
        f"{'Benchmark':<15} {'CPython':>10} {'p2w':>10} {'Compile':>10} "
        f"{'Speedup':>10} {'(med)':>8} {'Match':>6}"
    )
    print("-" * 85)

    speedups = []

    for r in results:
        if r["p2w_error"]:
            print(
                f"{r['name']:<15} {r['cpython_min'] * 1000:>9.1f}ms "
                f"{'ERROR':>10} {'-':>10} {'-':>10} {'-':>8} {'-':>6}"
            )
        else:
            match_str = "OK" if r["output_match"] else "FAIL"
            speedup_min_str = f"{r['speedup_min']:.2f}x" if r["speedup_min"] else "-"
            speedup_med_str = (
                f"{r['speedup_median']:.2f}x" if r["speedup_median"] else "-"
            )
            print(
                f"{r['name']:<15} "
                f"{r['cpython_min'] * 1000:>9.1f}ms "
                f"{r['p2w_min'] * 1000:>9.1f}ms "
                f"{r['p2w_compile_time'] * 1000:>9.1f}ms "
                f"{speedup_min_str:>10} "
                f"{speedup_med_str:>8} "
                f"{match_str:>6}"
            )
            if r["speedup_min"] and r["speedup_min"] > 0:
                speedups.append(r["speedup_min"])

    print("-" * 85)

    if speedups:
        geomean = geometric_mean(speedups)
        print(f"{'GEOMEAN':<15} {'':<10} {'':<10} {'':<10} {geomean:>9.2f}x")

    print("\nNotes:")
    print("  - Times shown are MINIMUM of timed runs (most stable measurement)")
    print("  - 'Speedup' = CPython time / p2w time (higher = p2w faster)")
    print("  - '(med)' = Speedup using median times (typical case)")
    print("  - 'Compile' = One-time cost to compile Python to WASM")

    # Show detailed stats if stddev is available
    print("\n" + "-" * 85)
    print("DETAILED STATISTICS (stddev)")
    print("-" * 85)
    print(f"{'Benchmark':<15} {'CPython σ':>12} {'p2w σ':>12}")
    print("-" * 40)
    for r in results:
        if not r["p2w_error"]:
            cp_stddev = (
                f"±{r['cpython_stddev'] * 1000:.2f}ms" if r["cpython_stddev"] else "N/A"
            )
            bp_stddev = (
                f"±{r['p2w_stddev'] * 1000:.2f}ms" if r["p2w_stddev"] else "N/A"
            )
            print(f"{r['name']:<15} {cp_stddev:>12} {bp_stddev:>12}")


def run_all_benchmarks(
    warmup: int = DEFAULT_WARMUP_RUNS, runs: int = DEFAULT_TIMED_RUNS
) -> list[dict]:
    """Run all benchmarks and return results.

    Args:
        warmup: Number of warmup runs (discarded)
        runs: Number of timed runs
    """
    benchmark_dir = Path(__file__).parent

    benchmarks = [
        ("fibonacci", benchmark_dir / "fibonacci.py"),
        ("nbody", benchmark_dir / "nbody.py"),
        ("binarytrees", benchmark_dir / "binarytrees.py"),
        ("spectralnorm", benchmark_dir / "spectralnorm.py"),
        ("fannkuch", benchmark_dir / "fannkuch_native.py"),
        ("pystone", benchmark_dir / "pystone.py"),
        ("mandelbrot", benchmark_dir / "mandelbrot.py"),
        ("fasta", benchmark_dir / "fasta.py"),
        ("sieve", benchmark_dir / "sieve_native.py"),
        ("matmul", benchmark_dir / "matmul_native.py"),
        ("primes", benchmark_dir / "primes_native.py"),
    ]

    results = []
    for name, path in benchmarks:
        if path.exists():
            source = path.read_text()
            result = run_benchmark(name, source, warmup, runs)
            results.append(result)
        else:
            print(f"Skipping {name}: file not found")

    return results


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Benchmark comparison tool: p2w vs CPython",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_benchmarks.py              # Run benchmarks (no save)
  python run_benchmarks.py --save       # Run and save to database
  python run_benchmarks.py --save -m "Added optimization X"
  python run_benchmarks.py --list       # List saved sessions
  python run_benchmarks.py --compare 1  # Compare run #1 with latest
  python run_benchmarks.py --compare 1 3  # Compare run #1 with run #3
  python run_benchmarks.py --warmup 3 --runs 10  # Custom config
        """,
    )

    parser.add_argument(
        "--save",
        action="store_true",
        help="Save benchmark results to database",
    )
    parser.add_argument(
        "-m",
        "--message",
        type=str,
        help="Description for this benchmark run (used with --save)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all saved benchmark sessions",
    )
    parser.add_argument(
        "--compare",
        nargs="+",
        type=int,
        metavar="RUN_ID",
        help="Compare two runs (if only one ID given, compares with latest)",
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=DEFAULT_WARMUP_RUNS,
        metavar="N",
        help=f"Number of warmup runs to discard (default: {DEFAULT_WARMUP_RUNS})",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=DEFAULT_TIMED_RUNS,
        metavar="N",
        help=f"Number of timed runs for statistics (default: {DEFAULT_TIMED_RUNS})",
    )

    args = parser.parse_args()

    # Initialize database for any DB operation
    conn = init_database()

    try:
        if args.list:
            list_sessions(conn)
        elif args.compare:
            if len(args.compare) == 1:
                # Compare with latest
                latest_id = get_latest_session_id(conn)
                if latest_id is None:
                    print("Error: No benchmark sessions found.")
                    return
                if args.compare[0] == latest_id:
                    print(f"Error: Run #{args.compare[0]} is already the latest run.")
                    return
                compare_sessions(conn, args.compare[0], latest_id)
            elif len(args.compare) >= 2:
                compare_sessions(conn, args.compare[0], args.compare[1])
            else:
                print("Error: --compare requires at least one run ID.")
        else:
            # Run benchmarks
            results = run_all_benchmarks(warmup=args.warmup, runs=args.runs)
            print_results(results)

            if args.save:
                session_id = save_session(conn, results, args.message)
                print(f"\nResults saved as session #{session_id}")
                if args.message:
                    print(f"Description: {args.message}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
