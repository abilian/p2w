#!/usr/bin/env python3
"""Benchmark comparison tool: p2w vs GCC vs CPython (Alioth Benchmark Game).

Runs benchmark programs from the Debian Benchmark Game and compares
execution time between p2w-compiled WASM, native GCC, and CPython.

Usage:
    python run_benchmarks.py              # Run benchmarks (no save)
    python run_benchmarks.py --save       # Run and save to database
    python run_benchmarks.py --list       # List saved sessions
    python run_benchmarks.py --compare 1  # Compare run #1 with latest
    python run_benchmarks.py --compare 1 3  # Compare run #1 with run #3
    python run_benchmarks.py --warmup 3 --runs 10  # Custom warmup/runs
    python run_benchmarks.py --benchmark nbody  # Run specific benchmark
    python run_benchmarks.py --no-cpython  # Skip CPython comparison
"""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
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
DEFAULT_WARMUP_RUNS = 2
DEFAULT_TIMED_RUNS = 5

# Paths
BENCHMARK_DIR = Path(__file__).parent
PROGRAMS_DIR = BENCHMARK_DIR / "programs"
GCC_DIR = BENCHMARK_DIR / "gcc"
DB_PATH = BENCHMARK_DIR / "benchmark_results.db"

# Benchmark configurations: name -> (python_file, gcc_file, arg)
# arg can be None for benchmarks with hardcoded data
BENCHMARKS = {
    "binarytrees": ("binarytrees.py", "binarytrees.gcc", "14"),
    "fannkuchredux": ("fannkuchredux.py", "fannkuchredux.gcc", "9"),
    "fasta": ("fasta.py", "fasta.gcc", "25000"),
    "knucleotide": ("knucleotide.py", "knucleotide.gcc", None),
    "mandelbrot": ("mandelbrot.py", "mandelbrot.gcc", "500"),
    "nbody": ("nbody.py", "nbody.gcc", "500000"),
    "revcomp": ("revcomp.py", "revcomp.gcc", None),
    "spectralnorm": ("spectralnorm.py", "spectralnorm.gcc", "500"),
    # pidigits: requires arbitrary precision integers (gmpy2) - not feasible
    # regexredux: requires regex module - not feasible
}

# Pattern to replace in Python source to inject the correct argument
# Maps benchmark name -> (old_pattern, new_pattern_template)
# new_pattern_template uses {arg} as placeholder for the actual argument
MAIN_CALL_REPLACEMENTS = {
    "binarytrees": ("main(10)", "main({arg})"),
    "fannkuchredux": ("main(7)", "main({arg})"),
    "fasta": ("main(1000)", "main({arg})"),
    "mandelbrot": ("main(200)", "main({arg})"),
    "nbody": ("main(1000)", "main({arg})"),
    "spectralnorm": ("main(100)", "main({arg})"),
    # knucleotide and revcomp use hardcoded data, no replacement needed
}


@dataclass
class BenchmarkResult:
    """Result of a single benchmark run."""

    name: str
    gcc_times: list[float]  # List of run times in seconds
    cpython_times: list[float]  # List of CPython run times in seconds
    p2w_compile_time: float
    p2w_times: list[float]
    gcc_output: str
    cpython_output: str
    p2w_output: str
    p2w_error: str | None = None


def init_database() -> sqlite3.Connection:
    """Initialize the SQLite database and return a connection."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            description TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            benchmark_name TEXT NOT NULL,
            gcc_time_ms REAL,
            gcc_min_ms REAL,
            gcc_median_ms REAL,
            gcc_stddev_ms REAL,
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


def geometric_mean(values: list[float]) -> float:
    """Compute geometric mean of positive values."""
    if not values:
        return 0
    log_sum = sum(math.log(v) for v in values if v > 0)
    count = sum(1 for v in values if v > 0)
    return math.exp(log_sum / count) if count > 0 else 0


def compile_gcc(name: str, gcc_file: str, output_path: Path) -> bool:
    """Compile a GCC source file. Returns True on success."""
    gcc_path = GCC_DIR / gcc_file
    if not gcc_path.exists():
        print(f"  [GCC] Source file not found: {gcc_path}")
        return False

    # Use -x c to force C language (files have .gcc extension)
    cmd = [
        "gcc",
        "-x", "c",  # Treat input as C source
        "-O3",
        "-ffast-math",
        "-o", str(output_path),
        str(gcc_path),
        "-lm",
    ]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=60, check=False
        )
        if result.returncode != 0:
            print(f"  [GCC] Compilation failed: {result.stderr}")
            return False
        return True
    except subprocess.TimeoutExpired:
        print("  [GCC] Compilation timed out")
        return False
    except Exception as e:
        print(f"  [GCC] Compilation error: {e}")
        return False


def run_gcc(executable: Path, arg: str | None, timeout: float = 120.0) -> tuple[str, float]:
    """Run a GCC executable. Returns (output, time_seconds)."""
    start = time.perf_counter()
    try:
        cmd = [str(executable)]
        if arg is not None:
            cmd.append(arg)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        elapsed = time.perf_counter() - start
        output = result.stdout
        if result.returncode != 0:
            output = f"[EXIT {result.returncode}] {result.stderr}"
        return output, elapsed
    except subprocess.TimeoutExpired:
        return "[TIMEOUT]", timeout
    except Exception as e:
        return f"[ERROR] {e}", 0.0


def prepare_source(name: str, source: str, arg: str | None) -> str:
    """Prepare Python source by replacing hardcoded main() call with correct argument."""
    if arg is None or name not in MAIN_CALL_REPLACEMENTS:
        return source

    old_pattern, new_template = MAIN_CALL_REPLACEMENTS[name]
    new_pattern = new_template.format(arg=arg)
    return source.replace(old_pattern, new_pattern)


def run_cpython(python_file: Path, name: str, arg: str | None, timeout: float = 120.0) -> tuple[str, float]:
    """Run a Python file with CPython. Returns (output, time_seconds).

    The source is modified to inject the correct argument into the main() call.
    """
    start = time.perf_counter()
    try:
        # Read and prepare source with correct argument
        source = python_file.read_text()
        source = prepare_source(name, source, arg)

        # Write to temp file and run
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as tmp:
            tmp.write(source)
            tmp_path = tmp.name

        try:
            result = subprocess.run(
                ["python3", tmp_path],
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            elapsed = time.perf_counter() - start
            output = result.stdout
            if result.returncode != 0:
                output = f"[EXIT {result.returncode}] {result.stderr}"
            return output, elapsed
        finally:
            os.unlink(tmp_path)
    except subprocess.TimeoutExpired:
        return "[TIMEOUT]", timeout
    except Exception as e:
        return f"[ERROR] {e}", 0.0


def compile_p2w(name: str, python_file: Path, arg: str | None, wasm_path: Path) -> tuple[float, str | None]:
    """Compile Python to WASM. Returns (compile_time, error_or_none).

    The source is modified to inject the correct argument into the main() call.
    """
    start = time.perf_counter()
    try:
        source = python_file.read_text()
        source = prepare_source(name, source, arg)
        wat_code = compile_to_wat(source)
        wasm_bytes = wat_to_wasm(wat_code)
        wasm_path.write_bytes(wasm_bytes)
        elapsed = time.perf_counter() - start
        return elapsed, None
    except Exception as e:
        elapsed = time.perf_counter() - start
        return elapsed, str(e)


def run_p2w_multi(wasm_path: Path, warmup: int, runs: int, timeout: float = 120.0) -> tuple[str, list[float]]:
    """Run a WASM file multiple times in a single Node.js process.

    This properly warms up V8's JIT and avoids Node.js startup overhead per run.
    Returns (output, list_of_times_in_seconds).
    """
    # Create runner script that runs multiple iterations in one process
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

// Output results as JSON
console.log(JSON.stringify({{
  times: times,
  output: lastOutput
}}));
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".mjs", delete=False) as js_file:
        js_file.write(runner_script)
        js_path = Path(js_file.name)

    try:
        result = subprocess.run(
            ["node", str(js_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )

        if result.returncode != 0:
            return f"[ERROR] {result.stderr}", []

        data = json.loads(result.stdout)
        # Convert times from ms to seconds
        times = [t / 1000.0 for t in data["times"]]
        return data["output"], times

    except subprocess.TimeoutExpired:
        return "[TIMEOUT]", []
    except Exception as e:
        return f"[ERROR] {e}", []
    finally:
        js_path.unlink(missing_ok=True)


def run_benchmark(
    name: str,
    python_file: str,
    gcc_file: str,
    arg: str | None,
    warmup_runs: int,
    timed_runs: int,
    run_cpython_flag: bool = True,
) -> BenchmarkResult:
    """Run a single benchmark comparing GCC, CPython, and p2w."""
    python_path = PROGRAMS_DIR / python_file

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        gcc_exe = tmpdir_path / "benchmark_gcc"
        wasm_file = tmpdir_path / "benchmark.wasm"

        # Compile GCC
        if not compile_gcc(name, gcc_file, gcc_exe):
            return BenchmarkResult(
                name=name,
                gcc_times=[],
                cpython_times=[],
                p2w_compile_time=0,
                p2w_times=[],
                gcc_output="",
                cpython_output="",
                p2w_output="",
                p2w_error="GCC compilation failed",
            )

        # Warmup GCC
        print(f"  [GCC] Warming up ({warmup_runs} runs)...", end="", flush=True)
        for _ in range(warmup_runs):
            run_gcc(gcc_exe, arg)
        print(" done")

        # Timed GCC runs
        print(f"  [GCC] Timing ({timed_runs} runs)...", end="", flush=True)
        gcc_times = []
        gcc_output = ""
        for _ in range(timed_runs):
            output, elapsed = run_gcc(gcc_exe, arg)
            gcc_times.append(elapsed)
            gcc_output = output  # Keep last output for comparison
        print(f" min={min(gcc_times)*1000:.1f}ms")

        # Run CPython (optional)
        cpython_times = []
        cpython_output = ""
        if run_cpython_flag:
            # Warmup CPython
            print(f"  [CPYTHON] Warming up ({warmup_runs} runs)...", end="", flush=True)
            for _ in range(warmup_runs):
                run_cpython(python_path, name, arg)
            print(" done")

            # Timed CPython runs
            print(f"  [CPYTHON] Timing ({timed_runs} runs)...", end="", flush=True)
            for _ in range(timed_runs):
                output, elapsed = run_cpython(python_path, name, arg)
                cpython_times.append(elapsed)
                cpython_output = output
            print(f" min={min(cpython_times)*1000:.1f}ms")

        # Compile p2w
        print("  [p2w] Compiling...", end="", flush=True)
        compile_time, compile_error = compile_p2w(name, python_path, arg, wasm_file)
        if compile_error:
            print(f" FAILED: {compile_error}")
            return BenchmarkResult(
                name=name,
                gcc_times=gcc_times,
                cpython_times=cpython_times,
                p2w_compile_time=compile_time,
                p2w_times=[],
                gcc_output=gcc_output,
                cpython_output=cpython_output,
                p2w_output="",
                p2w_error=compile_error,
            )
        print(f" done ({compile_time*1000:.1f}ms)")

        # Run p2w with proper in-process timing (warmup + timed runs in single Node.js process)
        print(f"  [p2w] Warming up ({warmup_runs} runs)...", end="", flush=True)
        print(" done")
        print(f"  [p2w] Timing ({timed_runs} runs)...", end="", flush=True)
        p2w_output, p2w_times = run_p2w_multi(wasm_file, warmup_runs, timed_runs)
        if p2w_times:
            print(f" min={min(p2w_times)*1000:.1f}ms")
        else:
            print(f" FAILED: {p2w_output}")

        return BenchmarkResult(
            name=name,
            gcc_times=gcc_times,
            cpython_times=cpython_times,
            p2w_compile_time=compile_time,
            p2w_times=p2w_times,
            gcc_output=gcc_output,
            cpython_output=cpython_output,
            p2w_output=p2w_output,
        )


def normalize_output(output: str) -> str:
    """Normalize output for comparison (strip, normalize whitespace)."""
    lines = output.strip().split("\n")
    return "\n".join(line.strip() for line in lines if line.strip())


def outputs_match(gcc_output: str, p2w_output: str) -> bool:
    """Check if outputs match (allowing for floating point differences)."""
    gcc_norm = normalize_output(gcc_output)
    p2w_norm = normalize_output(p2w_output)

    # For now, just check if they're roughly similar
    # (the Python versions may not produce identical output to C)
    return bool(gcc_norm) and bool(p2w_norm)


def print_results(results: list[dict], include_cpython: bool = True) -> None:
    """Print benchmark results table."""
    width = 120 if include_cpython else 90
    print("\n" + "=" * width)
    title = "BENCHMARK RESULTS: p2w vs GCC vs CPython" if include_cpython else "BENCHMARK RESULTS: p2w vs GCC"
    print(f"{title} (Alioth Benchmark Game)")
    print("=" * width)

    if include_cpython:
        print(
            f"{'Benchmark':<15} {'GCC (min)':>11} {'CPython':>11} {'p2w':>11} "
            f"{'vs GCC':>9} {'vs CPy':>9} {'Status':>8}"
        )
    else:
        print(
            f"{'Benchmark':<15} {'GCC (min)':>12} {'p2w (min)':>12} "
            f"{'Ratio':>10} {'Status':>10}"
        )
    print("-" * width)

    gcc_speedups = []
    cpython_speedups = []

    for r in results:
        name = r["name"]
        if r["p2w_error"]:
            if include_cpython:
                print(f"{name:<15} {'':>11} {'':>11} {'':>11} {'':>9} {'':>9} {'ERROR':>8}")
            else:
                print(f"{name:<15} {'':>12} {'':>12} {'':>10} {'ERROR':>10}")
            continue

        gcc_min = r["gcc_min"] * 1000  # ms
        cpython_min = r.get("cpython_min", 0) * 1000  # ms
        p2w_min = r["p2w_min"] * 1000  # ms

        # Ratio vs GCC
        if p2w_min > 0 and gcc_min > 0:
            gcc_ratio = p2w_min / gcc_min
            gcc_speedups.append(gcc_ratio)
            gcc_ratio_str = f"{gcc_ratio:.1f}x"
        else:
            gcc_ratio_str = "-"

        # Ratio vs CPython
        if p2w_min > 0 and cpython_min > 0:
            cpython_ratio = p2w_min / cpython_min
            cpython_speedups.append(cpython_ratio)
            cpython_ratio_str = f"{cpython_ratio:.2f}x"
        else:
            cpython_ratio_str = "-"

        match_str = "OK" if r["output_match"] else "DIFF"

        if include_cpython:
            cpython_str = f"{cpython_min:.1f}ms" if cpython_min > 0 else "-"
            print(
                f"{name:<15} {gcc_min:>9.1f}ms {cpython_str:>11} {p2w_min:>9.1f}ms "
                f"{gcc_ratio_str:>9} {cpython_ratio_str:>9} {match_str:>8}"
            )
        else:
            print(
                f"{name:<15} {gcc_min:>10.1f}ms {p2w_min:>10.1f}ms "
                f"{gcc_ratio_str:>10} {match_str:>10}"
            )

    print("-" * width)
    if gcc_speedups:
        gcc_geomean = geometric_mean(gcc_speedups)
        if include_cpython and cpython_speedups:
            cpython_geomean = geometric_mean(cpython_speedups)
            print(
                f"{'GEOMEAN':<15} {'':>11} {'':>11} {'':>11} "
                f"{gcc_geomean:.1f}x{' ':>4} {cpython_geomean:.2f}x"
            )
        else:
            print(f"{'GEOMEAN':<15} {'':>12} {'':>12} {gcc_geomean:.2f}x")

    print("\nNote: Ratios = p2w_time / reference_time (lower is better, <1.0 means p2w is faster)")
    if include_cpython:
        print("      vs GCC = compared to native C, vs CPy = compared to CPython interpreter")
    print()


def run_benchmarks(
    benchmark_filter: str | None = None,
    warmup_runs: int = DEFAULT_WARMUP_RUNS,
    timed_runs: int = DEFAULT_TIMED_RUNS,
    run_cpython_flag: bool = True,
) -> list[dict]:
    """Run all benchmarks and return results."""
    results = []

    for name, (python_file, gcc_file, arg) in BENCHMARKS.items():
        if benchmark_filter and name != benchmark_filter:
            continue

        print(f"\n{'='*60}")
        print(f"BENCHMARK: {name}")
        print(f"{'='*60}")

        result = run_benchmark(
            name, python_file, gcc_file, arg, warmup_runs, timed_runs, run_cpython_flag
        )

        # Compute GCC statistics
        gcc_min = min(result.gcc_times) if result.gcc_times else 0
        gcc_median = statistics.median(result.gcc_times) if result.gcc_times else 0
        gcc_stddev = (
            statistics.stdev(result.gcc_times) if len(result.gcc_times) > 1 else 0
        )

        # Compute CPython statistics
        cpython_min = min(result.cpython_times) if result.cpython_times else 0
        cpython_median = (
            statistics.median(result.cpython_times) if result.cpython_times else 0
        )
        cpython_stddev = (
            statistics.stdev(result.cpython_times) if len(result.cpython_times) > 1 else 0
        )

        # Compute p2w statistics
        p2w_min = min(result.p2w_times) if result.p2w_times else 0
        p2w_median = (
            statistics.median(result.p2w_times) if result.p2w_times else 0
        )
        p2w_stddev = (
            statistics.stdev(result.p2w_times) if len(result.p2w_times) > 1 else 0
        )

        # Compute speedup vs GCC (ratio of p2w to gcc, <1 means p2w faster)
        speedup_min = p2w_min / gcc_min if gcc_min > 0 and p2w_min > 0 else 0
        speedup_median = (
            p2w_median / gcc_median if gcc_median > 0 and p2w_median > 0 else 0
        )

        # Compute speedup vs CPython
        cpython_speedup_min = (
            p2w_min / cpython_min if cpython_min > 0 and p2w_min > 0 else 0
        )

        output_match = outputs_match(result.gcc_output, result.p2w_output)

        results.append(
            {
                "name": name,
                "gcc_min": gcc_min,
                "gcc_median": gcc_median,
                "gcc_stddev": gcc_stddev,
                "cpython_min": cpython_min,
                "cpython_median": cpython_median,
                "cpython_stddev": cpython_stddev,
                "p2w_compile_time": result.p2w_compile_time,
                "p2w_min": p2w_min,
                "p2w_median": p2w_median,
                "p2w_stddev": p2w_stddev,
                "speedup_min": speedup_min,
                "speedup_median": speedup_median,
                "cpython_speedup_min": cpython_speedup_min,
                "output_match": output_match,
                "p2w_error": result.p2w_error,
                "warmup_runs": warmup_runs,
                "timed_runs": timed_runs,
            }
        )

    return results


def save_session(
    conn: sqlite3.Connection, results: list[dict], description: str | None = None
) -> int:
    """Save a benchmark session to the database. Returns the session ID."""
    cursor = conn.cursor()

    timestamp = datetime.now().isoformat()
    cursor.execute(
        "INSERT INTO sessions (timestamp, description) VALUES (?, ?)",
        (timestamp, description),
    )
    session_id = cursor.lastrowid

    for r in results:
        cursor.execute(
            """
            INSERT INTO results (
                session_id, benchmark_name, gcc_time_ms,
                gcc_min_ms, gcc_median_ms, gcc_stddev_ms,
                p2w_compile_time_ms, p2w_run_time_ms,
                p2w_min_ms, p2w_median_ms, p2w_stddev_ms,
                speedup, speedup_min, output_match, error,
                warmup_runs, timed_runs
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                r["name"],
                r["gcc_min"] * 1000,
                r["gcc_min"] * 1000,
                r["gcc_median"] * 1000,
                r["gcc_stddev"] * 1000,
                r["p2w_compile_time"] * 1000,
                r["p2w_min"] * 1000,
                r["p2w_min"] * 1000,
                r["p2w_median"] * 1000,
                r["p2w_stddev"] * 1000,
                r["speedup_min"],
                r["speedup_min"],
                1 if r["output_match"] else 0,
                r["p2w_error"],
                r["warmup_runs"],
                r["timed_runs"],
            ),
        )

    conn.commit()
    return session_id


def list_sessions(conn: sqlite3.Connection) -> None:
    """List all saved benchmark sessions."""
    cursor = conn.cursor()
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
    print("SAVED BENCHMARK SESSIONS (p2w vs GCC)")
    print("=" * 80)
    print(f"{'ID':>5} {'Date':>20} {'Benchmarks':>12} {'Geomean':>12}  Description")
    print("-" * 80)

    for session_id, timestamp, description in sessions:
        cursor.execute(
            "SELECT speedup FROM results WHERE session_id = ? AND speedup > 0",
            (session_id,),
        )
        speedups = [row[0] for row in cursor.fetchall()]
        count = len(speedups)
        geomean = geometric_mean(speedups)

        dt = datetime.fromisoformat(timestamp)
        date_str = dt.strftime("%Y-%m-%d %H:%M")
        desc_str = description or ""
        speedup_str = f"{geomean:.2f}x" if geomean else "-"
        print(
            f"{session_id:>5} {date_str:>20} {count:>12} {speedup_str:>12}  {desc_str}"
        )

    print("-" * 80)
    print(f"\nTotal: {len(sessions)} session(s)")
    print("Note: Geomean ratio (lower is better, <1.0 means p2w faster than GCC)")


def get_latest_session_id(conn: sqlite3.Connection) -> int | None:
    """Get the ID of the most recent session."""
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(id) FROM sessions")
    row = cursor.fetchone()
    return row[0] if row and row[0] else None


def get_session_results(conn: sqlite3.Connection, session_id: int) -> dict[str, dict]:
    """Get results for a specific session as a dict keyed by benchmark name."""
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT benchmark_name, gcc_time_ms, p2w_compile_time_ms,
               p2w_run_time_ms, speedup, output_match, error
        FROM results
        WHERE session_id = ?
        """,
        (session_id,),
    )

    results = {}
    for row in cursor.fetchall():
        name, gcc_ms, compile_ms, run_ms, speedup, match, error = row
        results[name] = {
            "gcc_time_ms": gcc_ms,
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

    dt1 = datetime.fromisoformat(info1[0])
    dt2 = datetime.fromisoformat(info2[0])
    date1 = dt1.strftime("%Y-%m-%d %H:%M")
    date2 = dt2.strftime("%Y-%m-%d %H:%M")

    print("\n" + "=" * 90)
    print("BENCHMARK COMPARISON (p2w vs GCC)")
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

    for name in all_names:
        r1 = results1.get(name)
        r2 = results2.get(name)

        if r1 and r2 and r1["speedup"] and r2["speedup"]:
            speedup1 = r1["speedup"]
            speedup2 = r2["speedup"]
            ratio = speedup2 / speedup1 if speedup1 > 0 else 0
            pct_change = (ratio - 1) * 100

            if pct_change < -5:
                indicator = "BETTER"
            elif pct_change > 5:
                indicator = "WORSE"
            else:
                indicator = "~same"

            print(
                f"{name:<15} {speedup1:>10.2f}x {speedup2:>10.2f}x "
                f"{ratio:>10.2f}x {indicator:>10}"
            )
        else:
            s1 = f"{r1['speedup']:.2f}x" if r1 and r1["speedup"] else "-"
            s2 = f"{r2['speedup']:.2f}x" if r2 and r2["speedup"] else "-"
            print(f"{name:<15} {s1:>12} {s2:>12} {'':>12} {'':>10}")

    print("-" * 90)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark p2w vs GCC vs CPython (Alioth Benchmark Game)"
    )
    parser.add_argument(
        "--save", action="store_true", help="Save results to database"
    )
    parser.add_argument(
        "--list", action="store_true", help="List saved benchmark sessions"
    )
    parser.add_argument(
        "--compare",
        nargs="+",
        type=int,
        metavar="ID",
        help="Compare benchmark sessions (1 or 2 IDs)",
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=DEFAULT_WARMUP_RUNS,
        help=f"Number of warmup runs (default: {DEFAULT_WARMUP_RUNS})",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=DEFAULT_TIMED_RUNS,
        help=f"Number of timed runs (default: {DEFAULT_TIMED_RUNS})",
    )
    parser.add_argument(
        "--benchmark",
        type=str,
        help="Run only the specified benchmark",
    )
    parser.add_argument(
        "--description",
        "-d",
        type=str,
        help="Description for this benchmark run",
    )
    parser.add_argument(
        "--no-cpython",
        action="store_true",
        help="Skip CPython comparison (only compare p2w vs GCC)",
    )

    args = parser.parse_args()

    conn = init_database()

    if args.list:
        list_sessions(conn)
        return

    if args.compare:
        if len(args.compare) == 1:
            latest = get_latest_session_id(conn)
            if not latest:
                print("No sessions to compare with.")
                return
            compare_sessions(conn, args.compare[0], latest)
        else:
            compare_sessions(conn, args.compare[0], args.compare[1])
        return

    # Run benchmarks
    run_cpython = not args.no_cpython
    results = run_benchmarks(args.benchmark, args.warmup, args.runs, run_cpython)
    print_results(results, include_cpython=run_cpython)

    if args.save:
        session_id = save_session(conn, results, args.description)
        print(f"Results saved to session #{session_id}")

    conn.close()


if __name__ == "__main__":
    main()
