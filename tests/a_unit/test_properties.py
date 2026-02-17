"""Property-based tests for type system using hypothesis.

These tests verify invariants that should hold for any input,
helping find edge cases that explicit tests might miss.

Note: Compilation property tests are in tests/b_integration/test_properties.py
"""

from __future__ import annotations

from hypothesis import given, strategies as st

from p2w.compiler.types import (
    BOOL,
    F64,
    FLOAT,
    I32,
    I64,
    INT,
    STRING,
    UNKNOWN,
    combine_types,
    is_native_type,
    is_numeric,
)

# =============================================================================
# Type System Properties
# =============================================================================


class TestTypeSystemProperties:
    """Property-based tests for the type system."""

    @given(st.sampled_from([INT, FLOAT, I32, I64, F64]))
    def test_numeric_types_are_numeric(self, typ):
        """All numeric types should be recognized as numeric."""
        assert is_numeric(typ)

    @given(st.sampled_from([STRING, BOOL, UNKNOWN]))
    def test_non_numeric_types_are_not_numeric(self, typ):
        """Non-numeric types should not be recognized as numeric."""
        assert not is_numeric(typ)

    @given(st.sampled_from([I32, I64, F64]))
    def test_native_types_are_native(self, typ):
        """Native WASM types should be recognized."""
        assert is_native_type(typ)

    @given(st.sampled_from([INT, FLOAT, STRING, BOOL]))
    def test_boxed_types_are_not_native(self, typ):
        """Boxed types should not be native."""
        assert not is_native_type(typ)


class TestCombineTypesProperties:
    """Property-based tests for type combination."""

    @given(st.sampled_from([I32, I64, F64]))
    def test_native_same_type_addition(self, typ):
        """Adding same native types should preserve type (except division)."""
        result = combine_types(typ, typ, "+")
        assert result == typ

    @given(st.sampled_from(["+", "-", "*"]))
    def test_string_plus_string_is_string(self, op):
        """String concatenation should return string."""
        if op == "+":
            result = combine_types(STRING, STRING, op)
            assert result == STRING
