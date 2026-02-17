"""Integration tests for large integer boundary handling.

Tests the i31/INT64 transition at 2^30 boundaries.
"""

from __future__ import annotations

import pytest

from p2w.testing import compare_outputs

# i31 range: -2^30 to 2^30-1
I31_MIN = -(2**30)  # -1073741824
I31_MAX = 2**30 - 1  # 1073741823

# INT64 kicks in beyond i31 range
INT64_SMALL_POS = 2**30  # First positive INT64
INT64_SMALL_NEG = -(2**30) - 1  # First negative INT64


class TestI31Boundaries:
    """Test values at i31 boundaries."""

    def test_max_i31(self):
        source = f"print({I31_MAX})"
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"

    def test_min_i31(self):
        source = f"print({I31_MIN})"
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"

    def test_zero(self):
        source = "print(0)"
        _py_out, _p2w_out, match = compare_outputs(source)
        assert match

    def test_small_positive(self):
        source = "print(42)"
        _py_out, _p2w_out, match = compare_outputs(source)
        assert match

    def test_small_negative(self):
        source = "print(-42)"
        _py_out, _p2w_out, match = compare_outputs(source)
        assert match


class TestINT64Boundaries:
    """Test values requiring INT64 representation."""

    def test_first_positive_int64(self):
        source = f"print({INT64_SMALL_POS})"
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"

    def test_first_negative_int64(self):
        source = f"print({INT64_SMALL_NEG})"
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"

    def test_large_positive(self):
        source = f"print({2**40})"
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"

    def test_large_negative(self):
        source = f"print({-(2**40)})"
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"

    def test_max_int64(self):
        source = f"print({2**63 - 1})"
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"


class TestArithmeticAcrossBoundaries:
    """Test arithmetic operations that cross i31/INT64 boundaries."""

    def test_i31_plus_i31_stays_i31(self):
        # Result: 100 (still i31)
        source = "print(50 + 50)"
        _py_out, _p2w_out, match = compare_outputs(source)
        assert match

    def test_i31_max_plus_one(self):
        # Result: crosses into INT64
        source = f"print({I31_MAX} + 1)"
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"

    def test_i31_min_minus_one(self):
        # Result: crosses into negative INT64
        source = f"print({I31_MIN} - 1)"
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"

    def test_large_multiply(self):
        # 1000000 * 1000000 = 10^12 (needs INT64)
        source = "print(1000000 * 1000000)"
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"

    def test_int64_subtract_to_i31(self):
        # Large - large might fit back in i31
        source = f"print({INT64_SMALL_POS} - 1)"
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"


class TestVariableOperations:
    """Test operations on variables containing large integers."""

    def test_assign_and_print_large(self):
        source = f"""
x = {2**40}
print(x)
"""
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"

    def test_arithmetic_with_variable(self):
        source = f"""
x = {I31_MAX}
y = x + 1
print(y)
"""
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"

    def test_loop_accumulation(self):
        source = """
total = 0
for i in range(100):
    total = total + 1000000000
print(total)
"""
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"


class TestComparisonWithLargeInts:
    """Test comparisons involving large integers."""

    def test_compare_i31_boundary(self):
        source = f"""
x = {I31_MAX}
y = {INT64_SMALL_POS}
print(x < y)
print(x == y)
print(x > y)
"""
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"

    def test_compare_large_ints(self):
        source = f"""
a = {2**40}
b = {2**41}
print(a < b)
print(a == b)
"""
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"


@pytest.mark.skip(reason="INT64 bitwise operations not yet implemented")
class TestBitwiseWithLargeInts:
    """Test bitwise operations with large integers."""

    def test_left_shift_to_int64(self):
        source = "print(1 << 35)"
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"

    def test_right_shift_from_int64(self):
        source = f"print({2**40} >> 20)"
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"

    def test_bitwise_and_large(self):
        source = f"print({2**40} & {2**40 - 1})"
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"

    def test_bitwise_or_large(self):
        source = f"print({2**30} | {2**31})"
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"


class TestDivisionWithLargeInts:
    """Test division operations with large integers."""

    def test_large_floor_div(self):
        source = f"print({2**50} // {2**10})"
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"

    def test_large_modulo(self):
        source = f"print({2**50} % {2**10})"
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"

    def test_true_division_large(self):
        source = f"print({2**40} / {2**20})"
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"
