"""Unit tests for type inference edge cases."""

from __future__ import annotations

import ast
import math

from p2w.compiler.inference import TypeInferencer
from p2w.compiler.types import (
    BOOL,
    F64,
    FLOAT,
    I32,
    I64,
    INT,
    NONE,
    STRING,
    DictType,
    ListType,
    NativeType,
)


class TestConstantInference:
    """Test type inference for constants."""

    def test_int_constant(self):
        inferencer = TypeInferencer()
        node = ast.Constant(value=42)
        assert inferencer.infer(node) == INT

    def test_float_constant(self):
        inferencer = TypeInferencer()
        node = ast.Constant(value=math.pi)
        assert inferencer.infer(node) == FLOAT

    def test_string_constant(self):
        inferencer = TypeInferencer()
        node = ast.Constant(value="hello")
        assert inferencer.infer(node) == STRING

    def test_bool_constant_true(self):
        inferencer = TypeInferencer()
        node = ast.Constant(value=True)
        assert inferencer.infer(node) == BOOL

    def test_bool_constant_false(self):
        inferencer = TypeInferencer()
        node = ast.Constant(value=False)
        assert inferencer.infer(node) == BOOL

    def test_none_constant(self):
        inferencer = TypeInferencer()
        node = ast.Constant(value=None)
        assert inferencer.infer(node) == NONE


class TestAnnotationParsing:
    """Test parsing of type annotations."""

    def test_native_i32_annotation(self):
        inferencer = TypeInferencer()
        ann = ast.Name(id="i32")
        assert inferencer._annotation_to_type(ann) == I32

    def test_native_i64_annotation(self):
        inferencer = TypeInferencer()
        ann = ast.Name(id="i64")
        assert inferencer._annotation_to_type(ann) == I64

    def test_native_f64_annotation(self):
        inferencer = TypeInferencer()
        ann = ast.Name(id="f64")
        assert inferencer._annotation_to_type(ann) == F64

    def test_boxed_int_annotation(self):
        inferencer = TypeInferencer()
        ann = ast.Name(id="int")
        assert inferencer._annotation_to_type(ann) == INT

    def test_boxed_float_annotation(self):
        inferencer = TypeInferencer()
        ann = ast.Name(id="float")
        assert inferencer._annotation_to_type(ann) == FLOAT

    def test_list_annotation(self):
        inferencer = TypeInferencer()
        ann = ast.Name(id="list")
        result = inferencer._annotation_to_type(ann)
        assert isinstance(result, ListType)

    def test_dict_annotation(self):
        inferencer = TypeInferencer()
        ann = ast.Name(id="dict")
        result = inferencer._annotation_to_type(ann)
        assert isinstance(result, DictType)

    def test_list_with_element_type(self):
        inferencer = TypeInferencer()
        # list[float]
        ann = ast.Subscript(
            value=ast.Name(id="list"),
            slice=ast.Name(id="float"),
        )
        result = inferencer._annotation_to_type(ann)
        assert isinstance(result, ListType)
        assert result.element_type == FLOAT


class TestBinaryOperationInference:
    """Test type inference for binary operations."""

    def test_int_plus_int(self):
        inferencer = TypeInferencer()
        node = ast.BinOp(
            left=ast.Constant(value=1),
            op=ast.Add(),
            right=ast.Constant(value=2),
        )
        assert inferencer.infer(node) == INT

    def test_float_plus_float(self):
        inferencer = TypeInferencer()
        node = ast.BinOp(
            left=ast.Constant(value=1.0),
            op=ast.Add(),
            right=ast.Constant(value=2.0),
        )
        assert inferencer.infer(node) == FLOAT

    def test_int_div_int_returns_float(self):
        inferencer = TypeInferencer()
        node = ast.BinOp(
            left=ast.Constant(value=1),
            op=ast.Div(),
            right=ast.Constant(value=2),
        )
        assert inferencer.infer(node) == FLOAT

    def test_string_concat(self):
        inferencer = TypeInferencer()
        node = ast.BinOp(
            left=ast.Constant(value="hello"),
            op=ast.Add(),
            right=ast.Constant(value=" world"),
        )
        assert inferencer.infer(node) == STRING

    def test_string_repeat(self):
        inferencer = TypeInferencer()
        node = ast.BinOp(
            left=ast.Constant(value="ab"),
            op=ast.Mult(),
            right=ast.Constant(value=3),
        )
        assert inferencer.infer(node) == STRING


class TestNativeTypeInference:
    """Test native type (i32, i64, f64) inference."""

    def test_i32_plus_i32(self):
        inferencer = TypeInferencer()
        inferencer.var_types["x"] = I32
        inferencer.var_types["y"] = I32
        node = ast.BinOp(
            left=ast.Name(id="x"),
            op=ast.Add(),
            right=ast.Name(id="y"),
        )
        assert inferencer.infer(node) == I32

    def test_i32_div_i32_returns_f64(self):
        inferencer = TypeInferencer()
        inferencer.var_types["x"] = I32
        inferencer.var_types["y"] = I32
        node = ast.BinOp(
            left=ast.Name(id="x"),
            op=ast.Div(),
            right=ast.Name(id="y"),
        )
        assert inferencer.infer(node) == F64

    def test_f64_plus_f64(self):
        inferencer = TypeInferencer()
        inferencer.var_types["x"] = F64
        inferencer.var_types["y"] = F64
        node = ast.BinOp(
            left=ast.Name(id="x"),
            op=ast.Add(),
            right=ast.Name(id="y"),
        )
        assert inferencer.infer(node) == F64

    def test_i32_plus_i64_promotes(self):
        inferencer = TypeInferencer()
        inferencer.var_types["x"] = I32
        inferencer.var_types["y"] = I64
        node = ast.BinOp(
            left=ast.Name(id="x"),
            op=ast.Add(),
            right=ast.Name(id="y"),
        )
        assert inferencer.infer(node) == I64

    def test_i32_plus_f64_promotes(self):
        inferencer = TypeInferencer()
        inferencer.var_types["x"] = I32
        inferencer.var_types["y"] = F64
        node = ast.BinOp(
            left=ast.Name(id="x"),
            op=ast.Add(),
            right=ast.Name(id="y"),
        )
        assert inferencer.infer(node) == F64


class TestEscapeAnalysis:
    """Test variable escape analysis for native type eligibility."""

    def test_var_escapes_in_function_call(self):
        source = """
def foo(x: float):
    print(x)
"""
        tree = ast.parse(source)
        func = tree.body[0]
        inferencer = TypeInferencer()
        inferencer.analyze_function(func)
        # x escapes to print(), so should NOT be native
        # (unless explicitly annotated as f64)
        assert "x" not in inferencer.native_vars

    def test_var_escapes_in_list_append(self):
        source = """
def foo():
    x: float = 1.0
    lst = []
    lst.append(x)
"""
        tree = ast.parse(source)
        func = tree.body[0]
        inferencer = TypeInferencer()
        inferencer.analyze_function(func)
        # x escapes to list, should not be native
        assert "x" not in inferencer.native_vars

    def test_loop_counter_can_be_native(self):
        source = """
def foo(n: i32):
    total: i32 = 0
    for i in range(n):
        total = total + i
    return total
"""
        tree = ast.parse(source)
        func = tree.body[0]
        inferencer = TypeInferencer()
        inferencer.analyze_function(func)
        # i is a loop counter that doesn't escape
        assert "i" in inferencer.native_vars
        assert inferencer.native_vars["i"] == NativeType.I32


class TestLargeIntegerDetection:
    """Test detection of large integers outside i32 range."""

    def test_small_positive_int(self):
        inferencer = TypeInferencer()
        node = ast.Constant(value=100)
        assert not inferencer._is_large_int_literal(node)

    def test_max_i32(self):
        inferencer = TypeInferencer()
        node = ast.Constant(value=2**31 - 1)
        assert not inferencer._is_large_int_literal(node)

    def test_beyond_i32_max(self):
        inferencer = TypeInferencer()
        node = ast.Constant(value=2**31)
        assert inferencer._is_large_int_literal(node)

    def test_min_i32(self):
        inferencer = TypeInferencer()
        node = ast.UnaryOp(
            op=ast.USub(),
            operand=ast.Constant(value=2**31),
        )
        assert not inferencer._is_large_int_literal(node)

    def test_beyond_i32_min(self):
        inferencer = TypeInferencer()
        node = ast.UnaryOp(
            op=ast.USub(),
            operand=ast.Constant(value=2**31 + 1),
        )
        assert inferencer._is_large_int_literal(node)


class TestWhileLoopCounterDetection:
    """Test detection of while loop counter patterns."""

    def test_simple_while_counter(self):
        source = """
def foo():
    i: int = 0
    while i < 10:
        i = i + 1
"""
        tree = ast.parse(source)
        func = tree.body[0]
        inferencer = TypeInferencer()
        inferencer.analyze_function(func)
        # i should be detected as loop counter candidate
        assert "i" in inferencer._loop_counter_vars

    def test_while_counter_promoted_to_native(self):
        source = """
def foo():
    i: int = 0
    while i < 10:
        i = i + 1
"""
        tree = ast.parse(source)
        func = tree.body[0]
        inferencer = TypeInferencer()
        inferencer.analyze_function(func)
        # Loop counter should be promoted to native i32
        assert "i" in inferencer.native_vars
        assert inferencer.native_vars["i"] == NativeType.I32
