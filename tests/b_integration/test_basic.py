"""Basic integration tests for p2w.

These tests verify that simple programs compile and produce correct output.
"""

from __future__ import annotations

import subprocess

import pytest

from p2w.compiler import compile_to_wat
from p2w.runner import run_python, run_wat, wat_to_wasm


def has_wasm_tools() -> bool:
    """Check if wasm-tools is available."""
    try:
        subprocess.run(
            ["wasm-tools", "--version"],
            check=True,
            capture_output=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def has_node_with_wasm_gc() -> bool:
    """Check if Node.js with WASM GC support is available."""
    try:
        result = subprocess.run(
            ["node", "--version"],
            check=True,
            capture_output=True,
            text=True,
        )
        # Node 22+ has WASM GC
        version = result.stdout.strip()
        major = int(version.lstrip("v").split(".")[0])
        return major >= 22
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
        return False


requires_wasm_tools = pytest.mark.skipif(
    not has_wasm_tools(),
    reason="wasm-tools not available",
)

requires_node_wasm_gc = pytest.mark.skipif(
    not has_node_with_wasm_gc(),
    reason="Node.js 22+ with WASM GC not available",
)


class TestWatGeneration:
    """Test that WAT is generated correctly."""

    def test_empty_program(self) -> None:
        wat = compile_to_wat("")
        assert "(module" in wat

    def test_print_simple(self) -> None:
        wat = compile_to_wat("print(1)")
        assert "(module" in wat
        assert "$print" in wat

    def test_arithmetic(self) -> None:
        wat = compile_to_wat("print(1 + 2)")
        assert "i32.add" in wat


@requires_wasm_tools
class TestWatValidity:
    """Test that generated WAT is valid."""

    def test_empty_program_valid(self) -> None:
        wat = compile_to_wat("")
        wasm = wat_to_wasm(wat)
        assert len(wasm) > 0

    def test_print_valid(self) -> None:
        wat = compile_to_wat("print(42)")
        wasm = wat_to_wasm(wat)
        assert len(wasm) > 0

    def test_arithmetic_valid(self) -> None:
        wat = compile_to_wat("print(1 + 2 * 3)")
        wasm = wat_to_wasm(wat)
        assert len(wasm) > 0


@requires_wasm_tools
@requires_node_wasm_gc
class TestExecution:
    """Test that programs execute correctly."""

    def test_print_integer(self) -> None:
        source = "print(42)"
        wat = compile_to_wat(source)
        output = run_wat(wat)
        expected = run_python(source)
        assert output == expected

    def test_print_addition(self) -> None:
        source = "print(1 + 2)"
        wat = compile_to_wat(source)
        output = run_wat(wat)
        expected = run_python(source)
        assert output == expected

    def test_print_subtraction(self) -> None:
        source = "print(10 - 3)"
        wat = compile_to_wat(source)
        output = run_wat(wat)
        expected = run_python(source)
        assert output == expected

    def test_print_multiplication(self) -> None:
        source = "print(6 * 7)"
        wat = compile_to_wat(source)
        output = run_wat(wat)
        expected = run_python(source)
        assert output == expected

    def test_print_division(self) -> None:
        source = "print(20 // 3)"
        wat = compile_to_wat(source)
        output = run_wat(wat)
        expected = run_python(source)
        assert output == expected

    def test_print_modulo(self) -> None:
        source = "print(17 % 5)"
        wat = compile_to_wat(source)
        output = run_wat(wat)
        expected = run_python(source)
        assert output == expected

    def test_print_boolean_true(self) -> None:
        source = "print(True)"
        wat = compile_to_wat(source)
        output = run_wat(wat)
        expected = run_python(source)
        assert output == expected

    def test_print_boolean_false(self) -> None:
        source = "print(False)"
        wat = compile_to_wat(source)
        output = run_wat(wat)
        expected = run_python(source)
        assert output == expected

    def test_print_none(self) -> None:
        source = "print(None)"
        wat = compile_to_wat(source)
        output = run_wat(wat)
        expected = run_python(source)
        assert output == expected

    def test_print_string(self) -> None:
        source = 'print("hello")'
        wat = compile_to_wat(source)
        output = run_wat(wat)
        expected = run_python(source)
        assert output == expected

    def test_comparison_gt(self) -> None:
        source = "print(5 > 3)"
        wat = compile_to_wat(source)
        output = run_wat(wat)
        expected = run_python(source)
        assert output == expected

    def test_comparison_lt(self) -> None:
        source = "print(3 < 5)"
        wat = compile_to_wat(source)
        output = run_wat(wat)
        expected = run_python(source)
        assert output == expected

    def test_comparison_eq(self) -> None:
        source = "print(5 == 5)"
        wat = compile_to_wat(source)
        output = run_wat(wat)
        expected = run_python(source)
        assert output == expected

    def test_if_true(self) -> None:
        source = """\
if True:
    print(1)
else:
    print(2)
"""
        wat = compile_to_wat(source)
        output = run_wat(wat)
        expected = run_python(source)
        assert output == expected

    def test_if_false(self) -> None:
        source = """\
if False:
    print(1)
else:
    print(2)
"""
        wat = compile_to_wat(source)
        output = run_wat(wat)
        expected = run_python(source)
        assert output == expected

    def test_if_comparison(self) -> None:
        source = """\
if 5 > 3:
    print(1)
else:
    print(2)
"""
        wat = compile_to_wat(source)
        output = run_wat(wat)
        expected = run_python(source)
        assert output == expected
