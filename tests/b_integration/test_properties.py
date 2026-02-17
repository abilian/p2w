"""Property-based compilation tests using hypothesis.

These tests verify that compilation works correctly for a wide range of inputs.
They require the full compilation pipeline (Node.js) so are integration tests.

Note: deadline=None is required because compilation involves subprocess calls
which have variable timing.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings, strategies as st

from p2w.testing import compare_outputs

# =============================================================================
# Integer Compilation Properties
# =============================================================================


class TestIntegerCompilationProperties:
    """Property-based tests for integer compilation."""

    @given(st.integers(min_value=-(2**29), max_value=2**29 - 1))
    @settings(max_examples=20, deadline=None)
    def test_small_integers_roundtrip(self, n):
        """Small integers should compile and evaluate correctly."""
        source = f"print({n})"
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Mismatch for {n}: {py_out!r} vs {p2w_out!r}"

    @given(st.integers(min_value=2**30, max_value=2**50))
    @settings(max_examples=10, deadline=None)
    def test_large_positive_integers_roundtrip(self, n):
        """Large positive integers should compile correctly."""
        source = f"print({n})"
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Mismatch for {n}: {py_out!r} vs {p2w_out!r}"

    @given(st.integers(min_value=-(2**50), max_value=-(2**30) - 1))
    @settings(max_examples=10, deadline=None)
    def test_large_negative_integers_roundtrip(self, n):
        """Large negative integers should compile correctly."""
        source = f"print({n})"
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Mismatch for {n}: {py_out!r} vs {p2w_out!r}"


# =============================================================================
# Arithmetic Properties
# =============================================================================


class TestArithmeticProperties:
    """Property-based tests for arithmetic operations."""

    @given(
        st.integers(min_value=-1000, max_value=1000),
        st.integers(min_value=-1000, max_value=1000),
    )
    @settings(max_examples=20, deadline=None)
    def test_addition_commutative(self, a, b):
        """Addition should be commutative."""
        source1 = f"print({a} + {b})"
        source2 = f"print({b} + {a})"
        py1, p2w1, match1 = compare_outputs(source1)
        py2, p2w2, match2 = compare_outputs(source2)
        assert match1 and match2
        assert p2w1 == p2w2

    @given(
        st.integers(min_value=-1000, max_value=1000),
        st.integers(min_value=-1000, max_value=1000),
    )
    @settings(max_examples=20, deadline=None)
    def test_multiplication_commutative(self, a, b):
        """Multiplication should be commutative."""
        source1 = f"print({a} * {b})"
        source2 = f"print({b} * {a})"
        py1, p2w1, match1 = compare_outputs(source1)
        py2, p2w2, match2 = compare_outputs(source2)
        assert match1 and match2
        assert p2w1 == p2w2

    @given(
        st.integers(min_value=-100, max_value=100),
        st.integers(min_value=1, max_value=100),
    )
    @settings(max_examples=15, deadline=None)
    def test_floor_division_roundtrip(self, a, b):
        """Floor division should match Python semantics."""
        source = f"print({a} // {b})"
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Mismatch for {a} // {b}: {py_out!r} vs {p2w_out!r}"

    @given(
        st.integers(min_value=-100, max_value=100),
        st.integers(min_value=1, max_value=100),
    )
    @settings(max_examples=15, deadline=None)
    def test_modulo_roundtrip(self, a, b):
        """Modulo should match Python semantics."""
        source = f"print({a} % {b})"
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Mismatch for {a} % {b}: {py_out!r} vs {p2w_out!r}"


# =============================================================================
# Comparison Properties
# =============================================================================


class TestComparisonProperties:
    """Property-based tests for comparison operations."""

    @given(
        st.integers(min_value=-1000, max_value=1000),
        st.integers(min_value=-1000, max_value=1000),
    )
    @settings(max_examples=10, deadline=None)
    def test_comparison_consistency(self, a, b):
        """Comparisons should be consistent with Python."""
        ops = ["<", "<=", "==", "!=", ">=", ">"]
        for op in ops:
            source = f"print({a} {op} {b})"
            py_out, p2w_out, match = compare_outputs(source)
            assert match, f"Mismatch for {a} {op} {b}: {py_out!r} vs {p2w_out!r}"

    @given(st.integers(min_value=-1000, max_value=1000))
    @settings(max_examples=10, deadline=None)
    def test_equality_reflexive(self, n):
        """Equality should be reflexive: n == n."""
        source = f"print({n} == {n})"
        py_out, p2w_out, match = compare_outputs(source)
        assert match
        assert p2w_out.strip() == "True"


# =============================================================================
# List Properties
# =============================================================================


class TestListProperties:
    """Property-based tests for list operations."""

    @given(st.lists(st.integers(min_value=-100, max_value=100), max_size=10))
    @settings(max_examples=10, deadline=None)
    def test_list_literal_roundtrip(self, lst):
        """List literals should compile correctly."""
        source = f"print({lst})"
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Mismatch for {lst}: {py_out!r} vs {p2w_out!r}"

    @given(
        st.lists(st.integers(min_value=-100, max_value=100), min_size=1, max_size=10)
    )
    @settings(max_examples=10, deadline=None)
    def test_list_length(self, lst):
        """List length should match."""
        source = f"print(len({lst}))"
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Mismatch for len({lst}): {py_out!r} vs {p2w_out!r}"


# =============================================================================
# Boolean Properties
# =============================================================================


class TestBooleanProperties:
    """Property-based tests for boolean operations."""

    @given(st.booleans(), st.booleans())
    @settings(max_examples=4, deadline=None)
    def test_and_operation(self, a, b):
        """Boolean AND should match Python."""
        source = f"print({a} and {b})"
        py_out, p2w_out, match = compare_outputs(source)
        assert match

    @given(st.booleans(), st.booleans())
    @settings(max_examples=4, deadline=None)
    def test_or_operation(self, a, b):
        """Boolean OR should match Python."""
        source = f"print({a} or {b})"
        py_out, p2w_out, match = compare_outputs(source)
        assert match

    @given(st.booleans())
    @settings(max_examples=2, deadline=None)
    def test_not_operation(self, a):
        """Boolean NOT should match Python."""
        source = f"print(not {a})"
        py_out, p2w_out, match = compare_outputs(source)
        assert match
