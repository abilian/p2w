"""Runtime detection and execution for benchmarks.

Provides tools for detecting and running benchmarks on:
- CPython (standard Python interpreter)
- PyPy (JIT-compiled Python)
- Node.js (for WASM execution)
- GCC (C compiler)
- Clang (C/C++ compiler)
- Rust (rustc compiler)
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from p2w.benchmark.stats import BenchmarkStats, compute_stats


@dataclass(frozen=True)
class RuntimeInfo:
    """Information about a detected runtime.

    Attributes:
        name: Runtime identifier ("cpython", "pypy", "nodejs").
        version: Version string (e.g., "3.12.0", "22.1.0").
        available: Whether the runtime is available.
        path: Path to the runtime executable, or None if unavailable.
    """

    name: str
    version: str
    available: bool
    path: str | None


def _get_python_version(executable: str) -> str | None:
    """Get Python version from an executable."""
    try:
        result = subprocess.run(
            [executable, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        # Output is like "Python 3.12.0" or "Python 3.10.12 (PyPy 7.3.15)"
        output = result.stdout.strip() or result.stderr.strip()
        if output.startswith("Python "):
            return output[7:].split()[0]
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return None


def _get_pypy_version(executable: str) -> str | None:
    """Get PyPy-specific version from an executable."""
    try:
        result = subprocess.run(
            [executable, "-c", "import sys; print(sys.pypy_version_info[:3])"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            # Output is like "(7, 3, 15)"
            version_tuple = result.stdout.strip()
            if version_tuple.startswith("("):
                parts = version_tuple[1:-1].split(", ")
                return ".".join(parts)
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return None


def _get_node_version() -> str | None:
    """Get Node.js version."""
    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            # Output is like "v22.1.0"
            version = result.stdout.strip()
            if version.startswith("v"):
                return version[1:]
            return version
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return None


def detect_cpython() -> RuntimeInfo:
    """Detect CPython availability and version."""
    # Try common Python executable names
    for executable in ["python3", "python"]:
        path = shutil.which(executable)
        if path:
            version = _get_python_version(executable)
            if version:
                # Verify it's not PyPy
                pypy_version = _get_pypy_version(executable)
                if pypy_version is None:
                    return RuntimeInfo(
                        name="cpython",
                        version=version,
                        available=True,
                        path=path,
                    )

    return RuntimeInfo(
        name="cpython",
        version="",
        available=False,
        path=None,
    )


def detect_pypy() -> RuntimeInfo:
    """Detect PyPy availability and version.

    Only returns available=True for PyPy with Python 3 support,
    since the benchmarks use Python 3 syntax (type annotations, etc.).
    """
    # Try common PyPy executable names (prefer pypy3)
    for executable in ["pypy3", "pypy"]:
        path = shutil.which(executable)
        if path:
            pypy_version = _get_pypy_version(executable)
            python_version = _get_python_version(executable)
            if pypy_version and python_version:
                # Require Python 3.x
                major_version = python_version.split(".")[0]
                if major_version == "3":
                    return RuntimeInfo(
                        name="pypy",
                        version=pypy_version,
                        available=True,
                        path=path,
                    )

    return RuntimeInfo(
        name="pypy",
        version="",
        available=False,
        path=None,
    )


def detect_nodejs() -> RuntimeInfo:
    """Detect Node.js availability and version."""
    path = shutil.which("node")
    if path:
        version = _get_node_version()
        if version:
            return RuntimeInfo(
                name="nodejs",
                version=version,
                available=True,
                path=path,
            )

    return RuntimeInfo(
        name="nodejs",
        version="",
        available=False,
        path=None,
    )


def _get_compiler_version(
    executable: str, version_flag: str = "--version"
) -> str | None:
    """Get version from a compiler executable."""
    try:
        result = subprocess.run(
            [executable, version_flag],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            # First line usually contains version info
            first_line = result.stdout.strip().split("\n")[0]
            # Extract version number (look for patterns like X.Y.Z)
            import re

            match = re.search(r"(\d+\.\d+(?:\.\d+)?)", first_line)
            if match:
                return match.group(1)
            return first_line[:30]  # Fallback to truncated first line
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return None


def detect_gcc() -> RuntimeInfo:
    """Detect GCC availability and version."""
    path = shutil.which("gcc")
    if path:
        version = _get_compiler_version("gcc")
        if version:
            return RuntimeInfo(
                name="gcc",
                version=version,
                available=True,
                path=path,
            )

    return RuntimeInfo(
        name="gcc",
        version="",
        available=False,
        path=None,
    )


def detect_clang() -> RuntimeInfo:
    """Detect Clang availability and version."""
    path = shutil.which("clang")
    if path:
        version = _get_compiler_version("clang")
        if version:
            return RuntimeInfo(
                name="clang",
                version=version,
                available=True,
                path=path,
            )

    return RuntimeInfo(
        name="clang",
        version="",
        available=False,
        path=None,
    )


def detect_rustc() -> RuntimeInfo:
    """Detect Rust compiler availability and version."""
    path = shutil.which("rustc")
    if path:
        version = _get_compiler_version("rustc")
        if version:
            return RuntimeInfo(
                name="rustc",
                version=version,
                available=True,
                path=path,
            )

    return RuntimeInfo(
        name="rustc",
        version="",
        available=False,
        path=None,
    )


def detect_zig() -> RuntimeInfo:
    """Detect Zig compiler availability and version."""
    path = shutil.which("zig")
    if path:
        version = _get_compiler_version("zig", "version")
        if version:
            return RuntimeInfo(
                name="zig",
                version=version,
                available=True,
                path=path,
            )

    return RuntimeInfo(
        name="zig",
        version="",
        available=False,
        path=None,
    )


def detect_runtimes() -> dict[str, RuntimeInfo]:
    """Detect all available runtimes.

    Returns:
        Dictionary mapping runtime name to RuntimeInfo.
    """
    return {
        "cpython": detect_cpython(),
        "pypy": detect_pypy(),
        "nodejs": detect_nodejs(),
        "gcc": detect_gcc(),
        "clang": detect_clang(),
        "rustc": detect_rustc(),
        "zig": detect_zig(),
    }


def run_python(
    source: str,
    runtime: str = "cpython",
    timeout: float = 120.0,
) -> tuple[str, float]:
    """Run Python source on specified runtime.

    Args:
        source: Python source code to execute.
        runtime: Runtime to use ("cpython" or "pypy").
        timeout: Timeout in seconds.

    Returns:
        Tuple of (output, execution_time_in_seconds).

    Raises:
        ValueError: If runtime is not available.
    """
    runtimes = detect_runtimes()
    info = runtimes.get(runtime)

    if not info or not info.available or not info.path:
        raise ValueError(f"Runtime '{runtime}' is not available")

    # Write source to temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp:
        tmp.write(source)
        tmp_path = tmp.name

    try:
        start = time.perf_counter()
        result = subprocess.run(
            [info.path, tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        elapsed = time.perf_counter() - start

        if result.returncode != 0:
            return f"[EXIT {result.returncode}] {result.stderr}", elapsed

        return result.stdout, elapsed
    except subprocess.TimeoutExpired:
        return "[TIMEOUT]", timeout
    except Exception as e:
        return f"[ERROR] {e}", 0.0
    finally:
        Path(tmp_path).unlink()


def run_python_multi(
    source: str,
    runtime: str = "cpython",
    warmup: int = 3,
    runs: int = 5,
    timeout: float = 120.0,
) -> tuple[str, BenchmarkStats]:
    """Run Python source multiple times on specified runtime.

    Args:
        source: Python source code to execute.
        runtime: Runtime to use ("cpython" or "pypy").
        warmup: Number of warmup runs (discarded).
        runs: Number of timed runs.
        timeout: Timeout in seconds per run.

    Returns:
        Tuple of (last_output, BenchmarkStats).
    """
    # Warmup
    for _ in range(warmup):
        run_python(source, runtime, timeout)

    # Timed runs
    times: list[float] = []
    last_output = ""

    for _ in range(runs):
        output, elapsed = run_python(source, runtime, timeout)
        times.append(elapsed)
        last_output = output

    stats = compute_stats(times, runs_to_stable=runs)
    return last_output, stats


# JavaScript template for multi-run WASM benchmarking
_WASM_RUNNER_TEMPLATE = """\
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


def run_wasm_nodejs(
    wasm_bytes: bytes,
    warmup: int = 3,
    runs: int = 5,
    timeout: float = 120.0,
) -> tuple[str, BenchmarkStats]:
    """Run WASM with multi-run protocol in single Node.js process.

    This properly warms up V8's JIT and avoids Node.js startup overhead.

    Args:
        wasm_bytes: WASM binary to execute.
        warmup: Number of warmup runs (discarded).
        runs: Number of timed runs.
        timeout: Timeout in seconds for entire execution.

    Returns:
        Tuple of (output, BenchmarkStats).
    """
    nodejs = detect_nodejs()
    if not nodejs.available:
        raise ValueError("Node.js is not available")

    # Write WASM to temp file
    with tempfile.NamedTemporaryFile(suffix=".wasm", delete=False) as wasm_file:
        wasm_file.write(wasm_bytes)
        wasm_path = Path(wasm_file.name)

    # Create runner script
    runner_script = _WASM_RUNNER_TEMPLATE.format(
        wasm_path=str(wasm_path).replace("\\", "\\\\"),
        warmup=warmup,
        runs=runs,
    )

    with tempfile.NamedTemporaryFile(mode="w", suffix=".mjs", delete=False) as js_file:
        js_file.write(runner_script)
        js_path = Path(js_file.name)

    try:
        result = subprocess.run(
            ["node", str(js_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        if result.returncode != 0:
            empty_stats = compute_stats([])
            return f"[ERROR] {result.stderr}", empty_stats

        data = json.loads(result.stdout)
        # Convert times from ms to seconds
        times = [t / 1000.0 for t in data["times"]]
        stats = compute_stats(times, runs_to_stable=runs)

        return data["output"], stats

    except subprocess.TimeoutExpired:
        empty_stats = compute_stats([])
        return "[TIMEOUT]", empty_stats
    except json.JSONDecodeError as e:
        empty_stats = compute_stats([])
        return f"[JSON ERROR] {e}", empty_stats
    except Exception as e:
        empty_stats = compute_stats([])
        return f"[ERROR] {e}", empty_stats
    finally:
        wasm_path.unlink(missing_ok=True)
        js_path.unlink(missing_ok=True)


def run_wasm_nodejs_adaptive(
    wasm_bytes: bytes,
    min_runs: int = 5,
    max_runs: int = 50,
    target_cv: float = 0.01,
    warmup: int = 3,
    timeout: float = 300.0,
) -> tuple[str, BenchmarkStats]:
    """Run WASM adaptively until CV target is reached.

    Runs the benchmark multiple times in batches until the coefficient
    of variation is below target_cv or max_runs is reached.

    Args:
        wasm_bytes: WASM binary to execute.
        min_runs: Minimum number of timed runs.
        max_runs: Maximum number of timed runs.
        target_cv: Target coefficient of variation (default 0.01 = 1%).
        warmup: Number of warmup runs (discarded).
        timeout: Timeout in seconds for entire execution.

    Returns:
        Tuple of (output, BenchmarkStats).
    """
    # Start with min_runs
    output, stats = run_wasm_nodejs(
        wasm_bytes, warmup=warmup, runs=min_runs, timeout=timeout
    )

    if stats.cv <= target_cv:
        return output, stats

    # Collect more runs in batches
    all_times = list(stats.times)
    batch_size = 5

    while len(all_times) < max_runs:
        additional_runs = min(batch_size, max_runs - len(all_times))
        # No warmup for additional runs since JIT is already warmed
        new_output, new_stats = run_wasm_nodejs(
            wasm_bytes, warmup=0, runs=additional_runs, timeout=timeout
        )
        all_times.extend(new_stats.times)
        output = new_output  # Keep latest output

        # Check if stable
        combined_stats = compute_stats(all_times, runs_to_stable=len(all_times))
        if combined_stats.cv <= target_cv:
            return output, combined_stats

    # Return final stats even if CV not reached
    return output, compute_stats(all_times, runs_to_stable=len(all_times))


# =============================================================================
# Native Compiled Language Support (GCC, Clang, Rust, Zig)
# =============================================================================


def compile_c(
    source_path: Path,
    output_path: Path,
    compiler: str = "gcc",
    optimization: str = "-O3",
    extra_flags: list[str] | None = None,
    timeout: float = 60.0,
) -> tuple[bool, float, str | None]:
    """Compile C source code to native executable.

    Args:
        source_path: Path to C source file.
        output_path: Path for output executable.
        compiler: Compiler to use ("gcc" or "clang").
        optimization: Optimization level flag.
        extra_flags: Additional compiler flags.
        timeout: Compilation timeout in seconds.

    Returns:
        Tuple of (success, compile_time, error_message).
    """
    if extra_flags is None:
        extra_flags = []

    # Determine file extension and language flag
    suffix = source_path.suffix.lower()
    if suffix in (".c", ".gcc"):
        lang_flag = ["-x", "c"]
    elif suffix in (".cpp", ".cc", ".cxx"):
        lang_flag = ["-x", "c++"]
    else:
        lang_flag = ["-x", "c"]  # Default to C

    cmd = [
        compiler,
        *lang_flag,
        optimization,
        "-ffast-math",
        "-o",
        str(output_path),
        str(source_path),
        "-lm",
        *extra_flags,
    ]

    start = time.perf_counter()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        elapsed = time.perf_counter() - start

        if result.returncode != 0:
            return False, elapsed, result.stderr

        return True, elapsed, None
    except subprocess.TimeoutExpired:
        return False, timeout, "Compilation timed out"
    except Exception as e:
        return False, 0.0, str(e)


def compile_rust(
    source_path: Path,
    output_path: Path,
    optimization: str = "-C opt-level=3",
    extra_flags: list[str] | None = None,
    timeout: float = 60.0,
) -> tuple[bool, float, str | None]:
    """Compile Rust source code to native executable.

    Args:
        source_path: Path to Rust source file.
        output_path: Path for output executable.
        optimization: Optimization level flag.
        extra_flags: Additional compiler flags.
        timeout: Compilation timeout in seconds.

    Returns:
        Tuple of (success, compile_time, error_message).
    """
    if extra_flags is None:
        extra_flags = []

    # Parse optimization flag
    opt_parts = optimization.split()

    cmd = [
        "rustc",
        *opt_parts,
        "-o",
        str(output_path),
        str(source_path),
        *extra_flags,
    ]

    start = time.perf_counter()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        elapsed = time.perf_counter() - start

        if result.returncode != 0:
            return False, elapsed, result.stderr

        return True, elapsed, None
    except subprocess.TimeoutExpired:
        return False, timeout, "Compilation timed out"
    except Exception as e:
        return False, 0.0, str(e)


def compile_zig(
    source_path: Path,
    output_path: Path,
    optimization: str = "-OReleaseFast",
    extra_flags: list[str] | None = None,
    timeout: float = 60.0,
) -> tuple[bool, float, str | None]:
    """Compile Zig source code to native executable.

    Args:
        source_path: Path to Zig source file.
        output_path: Path for output executable.
        optimization: Optimization level flag (-OReleaseFast, -OReleaseSafe, etc.).
        extra_flags: Additional compiler flags.
        timeout: Compilation timeout in seconds.

    Returns:
        Tuple of (success, compile_time, error_message).
    """
    if extra_flags is None:
        extra_flags = []

    cmd = [
        "zig",
        "build-exe",
        str(source_path),
        optimization,
        "-femit-bin=" + str(output_path),
        *extra_flags,
    ]

    start = time.perf_counter()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        elapsed = time.perf_counter() - start

        if result.returncode != 0:
            return False, elapsed, result.stderr

        # Ensure the output file is executable (zig doesn't always set this)
        output_path.chmod(output_path.stat().st_mode | 0o111)

        return True, elapsed, None
    except subprocess.TimeoutExpired:
        return False, timeout, "Compilation timed out"
    except Exception as e:
        return False, 0.0, str(e)


def compile_c_with_zig(
    source_path: Path,
    output_path: Path,
    optimization: str = "-O3",
    extra_flags: list[str] | None = None,
    timeout: float = 60.0,
) -> tuple[bool, float, str | None]:
    """Compile C source code using Zig's C compiler (zig cc).

    Zig's C compiler is a drop-in replacement for GCC/Clang with
    better cross-compilation support and caching.

    Args:
        source_path: Path to C source file.
        output_path: Path for output executable.
        optimization: Optimization level flag.
        extra_flags: Additional compiler flags.
        timeout: Compilation timeout in seconds.

    Returns:
        Tuple of (success, compile_time, error_message).
    """
    if extra_flags is None:
        extra_flags = []

    # Determine file extension and language flag
    suffix = source_path.suffix.lower()
    if suffix in (".c", ".gcc"):
        lang_flag = ["-x", "c"]
    elif suffix in (".cpp", ".cc", ".cxx"):
        lang_flag = ["-x", "c++"]
    else:
        lang_flag = ["-x", "c"]  # Default to C

    cmd = [
        "zig",
        "cc",
        *lang_flag,
        optimization,
        "-ffast-math",
        "-o",
        str(output_path),
        str(source_path),
        "-lm",
        *extra_flags,
    ]

    start = time.perf_counter()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        elapsed = time.perf_counter() - start

        if result.returncode != 0:
            return False, elapsed, result.stderr

        # Ensure the output file is executable (zig cc doesn't set this by default)
        output_path.chmod(output_path.stat().st_mode | 0o111)

        return True, elapsed, None
    except subprocess.TimeoutExpired:
        return False, timeout, "Compilation timed out"
    except Exception as e:
        return False, 0.0, str(e)


def run_native(
    executable: Path,
    args: list[str] | None = None,
    timeout: float = 120.0,
) -> tuple[str, float]:
    """Run a native executable.

    Args:
        executable: Path to the executable.
        args: Command-line arguments.
        timeout: Timeout in seconds.

    Returns:
        Tuple of (output, execution_time_in_seconds).
    """
    if args is None:
        args = []

    cmd = [str(executable), *args]

    start = time.perf_counter()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        elapsed = time.perf_counter() - start

        if result.returncode != 0:
            return f"[EXIT {result.returncode}] {result.stderr}", elapsed

        return result.stdout, elapsed
    except subprocess.TimeoutExpired:
        return "[TIMEOUT]", timeout
    except Exception as e:
        return f"[ERROR] {e}", 0.0


def run_native_multi(
    executable: Path,
    args: list[str] | None = None,
    warmup: int = 3,
    runs: int = 5,
    timeout: float = 120.0,
) -> tuple[str, BenchmarkStats]:
    """Run a native executable multiple times.

    Args:
        executable: Path to the executable.
        args: Command-line arguments.
        warmup: Number of warmup runs (discarded).
        runs: Number of timed runs.
        timeout: Timeout in seconds per run.

    Returns:
        Tuple of (last_output, BenchmarkStats).
    """
    # Warmup
    for _ in range(warmup):
        run_native(executable, args, timeout)

    # Timed runs
    times: list[float] = []
    last_output = ""

    for _ in range(runs):
        output, elapsed = run_native(executable, args, timeout)
        times.append(elapsed)
        last_output = output

    stats = compute_stats(times, runs_to_stable=runs)
    return last_output, stats


@dataclass
class NativeCompileResult:
    """Result of compiling a native source file.

    Attributes:
        success: Whether compilation succeeded.
        executable: Path to the compiled executable (if successful).
        compile_time: Time taken to compile in seconds.
        error: Error message if compilation failed.
    """

    success: bool
    executable: Path | None
    compile_time: float
    error: str | None


def compile_and_run_native(
    source_path: Path,
    compiler: str = "gcc",
    args: list[str] | None = None,
    warmup: int = 3,
    runs: int = 5,
    timeout: float = 120.0,
    cleanup: bool = True,
) -> tuple[NativeCompileResult, str, BenchmarkStats]:
    """Compile and run a native source file.

    Args:
        source_path: Path to source file (.c, .rs, etc.).
        compiler: Compiler to use ("gcc", "clang", or "rustc").
        args: Runtime arguments.
        warmup: Number of warmup runs.
        runs: Number of timed runs.
        timeout: Timeout per run.
        cleanup: Whether to delete executable after running.

    Returns:
        Tuple of (compile_result, output, stats).
    """
    # Create temp executable
    with tempfile.NamedTemporaryFile(delete=False, suffix="") as tmp:
        exe_path = Path(tmp.name)

    # Compile based on source type
    suffix = source_path.suffix.lower()
    if suffix == ".rs":
        success, compile_time, error = compile_rust(source_path, exe_path)
    else:
        success, compile_time, error = compile_c(
            source_path, exe_path, compiler=compiler
        )

    compile_result = NativeCompileResult(
        success=success,
        executable=exe_path if success else None,
        compile_time=compile_time,
        error=error,
    )

    if not success:
        exe_path.unlink(missing_ok=True)
        return compile_result, "", compute_stats([])

    try:
        output, stats = run_native_multi(exe_path, args, warmup, runs, timeout)
        return compile_result, output, stats
    finally:
        if cleanup:
            exe_path.unlink(missing_ok=True)
