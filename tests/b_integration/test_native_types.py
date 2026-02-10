"""Integration tests for native type (i32/i64/f64) coercion.

These tests verify that native WASM types properly coerce with boxed Python types.
"""

from __future__ import annotations

import subprocess

import pytest

from p2w.compiler import compile_to_wat
from p2w.runner import run_python, run_wat


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


@requires_wasm_tools
@requires_node_wasm_gc
class TestI32FunctionParams:
    """Test i32 in function parameters with int literals."""

    def test_i32_param_with_literal(self) -> None:
        """Function with i32 param should accept int literal."""
        source = """\
def add_one(x: i32) -> i32:
    return x + 1

print(add_one(5))
"""
        wat = compile_to_wat(source)
        output = run_wat(wat)
        assert output.strip() == "6"

    def test_i32_param_with_int_variable(self) -> None:
        """Function with i32 param should accept boxed int variable."""
        source = """\
def add_one(x: i32) -> i32:
    return x + 1

n: int = 5
print(add_one(n))
"""
        wat = compile_to_wat(source)
        output = run_wat(wat)
        assert output.strip() == "6"

    def test_i32_return_to_int_variable(self) -> None:
        """i32 return value should be assignable to int variable."""
        source = """\
def get_value() -> i32:
    return 42

result: int = get_value()
print(result)
"""
        wat = compile_to_wat(source)
        output = run_wat(wat)
        assert output.strip() == "42"


@requires_wasm_tools
@requires_node_wasm_gc
class TestI32MixedExpressions:
    """Test i32 in expressions with boxed int."""

    def test_i32_plus_int(self) -> None:
        """i32 + int should work."""
        source = """\
i: i32 = 5
n: int = 10
result: int = i + n
print(result)
"""
        wat = compile_to_wat(source)
        output = run_wat(wat)
        assert output.strip() == "15"

    def test_int_plus_i32(self) -> None:
        """int + i32 should work."""
        source = """\
n: int = 10
i: i32 = 5
result: int = n + i
print(result)
"""
        wat = compile_to_wat(source)
        output = run_wat(wat)
        assert output.strip() == "15"

    def test_i32_in_list_index(self) -> None:
        """i32 should work as list index."""
        source = """\
items: list[int] = [10, 20, 30]
i: i32 = 1
print(items[i])
"""
        wat = compile_to_wat(source)
        output = run_wat(wat)
        assert output.strip() == "20"

    def test_i32_loop_with_int_limit(self) -> None:
        """i32 loop counter should work with int limit."""
        source = """\
n: int = 5
total: int = 0
i: i32 = 0
while i < n:
    total = total + i
    i = i + 1
print(total)
"""
        wat = compile_to_wat(source)
        output = run_wat(wat)
        assert output.strip() == "10"


@requires_wasm_tools
@requires_node_wasm_gc
class TestI32ToBoxedAssignment:
    """Test assigning i32 results to boxed variables."""

    def test_i32_arithmetic_to_int(self) -> None:
        """i32 arithmetic result should be assignable to int."""
        source = """\
a: i32 = 5
b: i32 = 3
result: int = a + b
print(result)
"""
        wat = compile_to_wat(source)
        output = run_wat(wat)
        assert output.strip() == "8"

    def test_i32_to_list_element(self) -> None:
        """i32 should be assignable to list element."""
        source = """\
items: list[int] = [0, 0, 0]
i: i32 = 1
val: i32 = 42
items[i] = val
print(items[1])
"""
        wat = compile_to_wat(source)
        output = run_wat(wat)
        assert output.strip() == "42"


@requires_wasm_tools
@requires_node_wasm_gc
class TestF64Coercion:
    """Test f64 coercion with boxed float."""

    def test_f64_param_with_float_literal(self) -> None:
        """Function with f64 param should accept float literal."""
        source = """\
def double(x: f64) -> f64:
    return x * 2.0

print(double(3.5))
"""
        wat = compile_to_wat(source)
        output = run_wat(wat)
        assert output.strip() == "7.0"

    def test_f64_plus_float(self) -> None:
        """f64 + float should work."""
        source = """\
x: f64 = 1.5
y: float = 2.5
result: float = x + y
print(result)
"""
        wat = compile_to_wat(source)
        output = run_wat(wat)
        assert output.strip() == "4.0"

    def test_f64_arithmetic_to_float(self) -> None:
        """f64 arithmetic result should be assignable to float."""
        source = """\
a: f64 = 10.0
b: f64 = 3.0
result: float = a / b
print(result)
"""
        wat = compile_to_wat(source)
        output = run_wat(wat)
        # Check for approximate equality due to float representation
        assert "3.333" in output.strip()


@requires_wasm_tools
@requires_node_wasm_gc
class TestI32InSlices:
    """Test i32 in slice expressions.

    Regression tests for issue where i32 in slice indices caused
    'Invalid types for ref.cast: i32.add' WASM compile error.
    """

    def test_i32_as_slice_start(self) -> None:
        """i32 should work as slice start index."""
        source = """\
s: str = "hello"
i: i32 = 1
result: str = s[i:]
print(result)
"""
        wat = compile_to_wat(source)
        output = run_wat(wat)
        assert output.strip() == "ello"

    def test_i32_as_slice_end(self) -> None:
        """i32 should work as slice end index."""
        source = """\
s: str = "hello"
i: i32 = 3
result: str = s[:i]
print(result)
"""
        wat = compile_to_wat(source)
        output = run_wat(wat)
        assert output.strip() == "hel"

    def test_i32_expression_as_slice_end(self) -> None:
        """i32 expression (i + 2) should work as slice end index."""
        source = """\
s: str = "hello"
i: i32 = 1
result: str = s[i:i + 2]
print(result)
"""
        wat = compile_to_wat(source)
        output = run_wat(wat)
        assert output.strip() == "el"

    def test_i32_in_loop_with_slicing(self) -> None:
        """i32 loop counter used in slice expression."""
        source = """\
def count_subseqs(seq: str, frame: int) -> int:
    count: int = 0
    seq_len: int = len(seq)
    i: i32 = 0
    while i <= seq_len - frame:
        subseq: str = seq[i : i + frame]
        count = count + 1
        i = i + 1
    return count

result: int = count_subseqs("ATCGATCG", 2)
print(result)
"""
        wat = compile_to_wat(source)
        output = run_wat(wat)
        assert output.strip() == "7"

    def test_i32_list_slicing(self) -> None:
        """i32 should work in list slice indices."""
        source = """\
items: list[int] = [10, 20, 30, 40, 50]
i: i32 = 1
j: i32 = 4
result: list[int] = items[i:j]
print(len(result))
"""
        wat = compile_to_wat(source)
        output = run_wat(wat)
        assert output.strip() == "3"
