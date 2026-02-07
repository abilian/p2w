"""Testing utilities for p2w."""

from __future__ import annotations

import subprocess
from pathlib import Path

from p2w.compiler import compile_to_wat
from p2w.runner import run_python, run_wat, wat_to_wasm


def compile_and_run(source: str) -> str:
    """Compile Python source to WASM and run it.

    Args:
        source: Python source code.

    Returns:
        Standard output from WASM execution.
    """
    wat_code = compile_to_wat(source)
    return run_wat(wat_code)


def compare_outputs(source: str) -> tuple[str, str, bool]:
    """Compare Python and p2w outputs for the same source.

    Args:
        source: Python source code.

    Returns:
        Tuple of (python_output, p2w_output, match).
    """
    py_output = run_python(source)
    p2w_output = compile_and_run(source)
    return py_output, p2w_output, py_output == p2w_output


def check_wat_valid(wat_code: str) -> tuple[bool, str]:
    """Check if WAT code is valid by trying to parse it.

    Args:
        wat_code: WebAssembly Text format code.

    Returns:
        Tuple of (valid, error_message).
    """
    try:
        wat_to_wasm(wat_code)
        return True, ""
    except subprocess.CalledProcessError as e:
        return False, e.stderr


def get_test_programs(
    directory: Path | str = "programs/internal",
) -> list[Path]:
    """Get all Python test programs from a directory.

    Args:
        directory: Path to test programs directory.

    Returns:
        List of .py file paths.
    """
    dir_path = Path(directory)
    if not dir_path.exists():
        return []
    return sorted(dir_path.glob("*.py"))
