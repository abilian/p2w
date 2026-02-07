"""Expression compilation handlers.

This module registers all handlers for compile_expr.
Import this module to activate the handlers.
"""

from __future__ import annotations

import ast
import builtins

from p2w.compiler.analysis import (
    is_bool_expr,
    is_float_expr,
    is_large_int_constant,
    is_list_expr,
    is_string_expr,
    is_tuple_expr,
    is_unknown_type,
)
from p2w.compiler.codegen.calls import compile_call
from p2w.compiler.codegen.collections import (
    compile_dict,
    compile_dictcomp,
    compile_list,
    compile_listcomp,
    compile_set,
    compile_tuple,
)
from p2w.compiler.codegen.expressions import compile_expr
from p2w.compiler.codegen.fstrings import compile_fstring
from p2w.compiler.codegen.functions import compile_lambda
from p2w.compiler.codegen.operators import compile_compare
from p2w.compiler.codegen.subscript import compile_subscript
from p2w.compiler.codegen.variables import compile_var_load
from p2w.compiler.context import CompilerContext  # noqa: TC001
from p2w.compiler.types import (
    BobType,
    F64Type,
    FloatType,
    I64Type,
    IntType,
    ListType,
    NativeType,
    StringType,
    TupleType,
    UnknownType,
    is_native_type,
)

# =============================================================================
# Constants
# =============================================================================


# i31 range: -2^30 to 2^30-1
I31_MIN = -(2**30)  # -1073741824
I31_MAX = 2**30 - 1  # 1073741823


@compile_expr.register
def _constant(node: ast.Constant, ctx: CompilerContext) -> None:
    """Compile a constant value."""
    match node.value:
        case None:
            ctx.emitter.emit_none()
        case bool() as value:
            ctx.emitter.emit_bool(value)
        case int() as value:
            # Check if value fits in i31 range
            if I31_MIN <= value <= I31_MAX:
                ctx.emitter.emit_int(value)
            else:
                ctx.emitter.emit_int64(value)
        case float() as value:
            ctx.emitter.emit_float(value)
        case str() as value:
            ctx.emitter.emit_string(value)
        case bytes() as value:
            ctx.emitter.emit_bytes(value)
        case builtins.Ellipsis:
            ctx.emitter.emit_ellipsis()
        case _:
            msg = f"Constant type not implemented: {type(node.value)}"
            raise NotImplementedError(msg)


# =============================================================================
# Variables
# =============================================================================


@compile_expr.register
def _name(node: ast.Name, ctx: CompilerContext) -> None:
    """Compile variable load."""
    compile_var_load(node.id, ctx)


# =============================================================================
# Binary Operations
# =============================================================================

# i31 range: -1073741824 to 1073741823 (i.e., -2^30 to 2^30-1)
_I31_MIN = -(2**30)
_I31_MAX = 2**30 - 1


def _is_small_int_expr(node: ast.expr) -> bool:
    """Check if expression is guaranteed to be a small integer (fits in i31).

    Returns True only for integer constants within i31 range.
    Variables and other expressions might hold INT64 values at runtime,
    so we conservatively return False for them.
    """
    match node:
        case ast.Constant(value=int() as val):
            return _I31_MIN <= val <= _I31_MAX
        # For unary minus of a constant, check the negated value
        case ast.UnaryOp(op=ast.USub(), operand=ast.Constant(value=int() as val)):
            return _I31_MIN <= -val <= _I31_MAX
        case _:
            return False


def _get_const_int(node: ast.expr) -> int | None:
    """Get integer constant value from expression, or None if not a constant."""
    match node:
        case ast.Constant(value=int() as val):
            return val
        case ast.UnaryOp(op=ast.USub(), operand=ast.Constant(value=int() as val)):
            return -val
        case _:
            return None


def _operation_might_overflow(
    left: ast.expr, op: ast.operator, right: ast.expr
) -> bool:
    """Check if an operation between two constants might overflow i31.

    Returns True when both operands are constants that fit in i31,
    but the result might overflow i31 range.
    """
    left_val = _get_const_int(left)
    right_val = _get_const_int(right)

    # Only applies to constant expressions
    if left_val is None or right_val is None:
        return False

    # If either doesn't fit in i31, already handled elsewhere
    if not (_I31_MIN <= left_val <= _I31_MAX and _I31_MIN <= right_val <= _I31_MAX):
        return False

    # Check if result might overflow
    match op:
        case ast.Add():
            result = left_val + right_val
            return result < _I31_MIN or result > _I31_MAX
        case ast.Sub():
            result = left_val - right_val
            return result < _I31_MIN or result > _I31_MAX
        case ast.Mult():
            result = left_val * right_val
            return result < _I31_MIN or result > _I31_MAX
        case _:
            return False


@compile_expr.register
def _binop(node: ast.BinOp, ctx: CompilerContext) -> None:
    """Compile binary operation."""
    left, op, right = node.left, node.op, node.right

    # Get inferred types for specialized code generation
    left_type = ctx.get_expr_type(left)
    right_type = ctx.get_expr_type(right)
    left_known = not isinstance(left_type, UnknownType)
    right_known = not isinstance(right_type, UnknownType)

    # Native type operations - use direct WASM instructions
    # Both operands must be numeric for native binop (can't do list * int natively)
    left_is_numeric = is_native_type(left_type) or isinstance(
        left_type, IntType | FloatType
    )
    right_is_numeric = is_native_type(right_type) or isinstance(
        right_type, IntType | FloatType
    )
    if (
        (is_native_type(left_type) or is_native_type(right_type))
        and left_is_numeric
        and right_is_numeric
    ):
        _compile_native_binop(node, left_type, right_type, ctx)
        # _compile_native_binop sets the native value flag
        return

    # Use type inference for specialized code generation
    # Float involved (even with unknown) -> float dispatch for numeric ops
    # This handles cases like: float_var * unknown_param
    match (left_type, right_type):
        case (FloatType(), _) | (_, FloatType()):
            _compile_float_binop(node, ctx)
            return

    # Division always returns float, regardless of operand types
    match op:
        case ast.Div():
            ctx.emitter.comment("true division (returns float)")
            compile_expr(left, ctx)
            compile_expr(right, ctx)
            ctx.emitter.emit_call("$div_dispatch")
            return

    # Type-inferred specialized code generation
    # Only use when both types are known
    if left_known and right_known:
        match (left_type, right_type, op):
            # Integer + Integer -> direct i32 arithmetic
            # Only use fast path when RESULT fits in i31 (not just operands)
            case (IntType(), IntType(), ast.Add()) if (
                _is_small_int_expr(left)
                and _is_small_int_expr(right)
                and isinstance(left, ast.Constant)
                and isinstance(right, ast.Constant)
                and isinstance(left.value, int)
                and isinstance(right.value, int)
                and _I31_MIN <= left.value + right.value <= _I31_MAX
            ):
                _compile_int_binop(node, ctx)
                return

            case (IntType(), IntType(), ast.Sub()) if (
                _is_small_int_expr(left)
                and _is_small_int_expr(right)
                and isinstance(left, ast.Constant)
                and isinstance(right, ast.Constant)
                and isinstance(left.value, int)
                and isinstance(right.value, int)
                and _I31_MIN <= left.value - right.value <= _I31_MAX
            ):
                _compile_int_binop(node, ctx)
                return

            case (IntType(), IntType(), ast.Mult()) if (
                _is_small_int_expr(left)
                and _is_small_int_expr(right)
                and isinstance(left, ast.Constant)
                and isinstance(right, ast.Constant)
                and isinstance(left.value, int)
                and isinstance(right.value, int)
                and _I31_MIN <= left.value * right.value <= _I31_MAX
            ):
                _compile_int_binop(node, ctx)
                return

            case (
                IntType(),
                IntType(),
                ast.BitAnd() | ast.BitOr() | ast.BitXor() | ast.LShift() | ast.RShift(),
            ):
                _compile_int_binop(node, ctx)
                return

            # FloorDiv and Mod: use native i32 when both operands are
            # known small constants (guaranteed to fit in i31)
            case (IntType(), IntType(), ast.FloorDiv() | ast.Mod()) if (
                _is_small_int_expr(left) and _is_small_int_expr(right)
            ):
                _compile_int_binop(node, ctx)
                return

            # String + String -> concatenation
            case (StringType(), StringType(), ast.Add()):
                ctx.emitter.comment("string concatenation (inferred)")
                compile_expr(left, ctx)
                ctx.emitter.emit_ref_cast("$STRING")
                compile_expr(right, ctx)
                ctx.emitter.emit_ref_cast("$STRING")
                ctx.emitter.emit_call("$string_concat")
                return

            # String * Int -> repetition
            case (StringType(), IntType(), ast.Mult()):
                ctx.emitter.comment("string repetition (inferred)")
                compile_expr(left, ctx)
                compile_expr(right, ctx)
                ctx.emitter.emit_call("$string_repeat")
                return

            # List + List -> concatenation
            case (ListType(), ListType(), ast.Add()):
                ctx.emitter.comment("list concatenation (inferred)")
                compile_expr(left, ctx)
                compile_expr(right, ctx)
                ctx.emitter.emit_call("$list_concat")
                return

            # List * Int -> repetition
            case (ListType(), IntType(), ast.Mult()):
                ctx.emitter.comment("list repetition (inferred)")
                compile_expr(left, ctx)
                compile_expr(right, ctx)
                ctx.emitter.emit_call("$list_repeat")
                return

            # Tuple + Tuple -> concatenation
            case (TupleType(), TupleType(), ast.Add()):
                ctx.emitter.comment("tuple concatenation (inferred)")
                compile_expr(left, ctx)
                compile_expr(right, ctx)
                ctx.emitter.emit_call("$tuple_concat")
                return

            # Tuple * Int -> repetition
            case (TupleType(), IntType(), ast.Mult()):
                ctx.emitter.comment("tuple repetition (inferred)")
                compile_expr(left, ctx)
                compile_expr(right, ctx)
                ctx.emitter.emit_call("$tuple_repeat")
                return

    # Fall back to heuristic-based analysis
    match op:
        case ast.Add():
            # String concatenation
            if is_string_expr(left) or is_string_expr(right):
                ctx.emitter.comment("string concatenation")
                compile_expr(left, ctx)
                ctx.emitter.emit_ref_cast("$STRING")
                compile_expr(right, ctx)
                ctx.emitter.emit_ref_cast("$STRING")
                ctx.emitter.emit_call("$string_concat")
                return

            # List concatenation
            if is_list_expr(left) or is_list_expr(right):
                ctx.emitter.comment("list concatenation")
                compile_expr(left, ctx)
                compile_expr(right, ctx)
                ctx.emitter.emit_call("$list_concat")
                return

            # Tuple concatenation
            if is_tuple_expr(left) or is_tuple_expr(right):
                ctx.emitter.comment("tuple concatenation")
                compile_expr(left, ctx)
                compile_expr(right, ctx)
                ctx.emitter.emit_call("$tuple_concat")
                return

            # Runtime dispatch for unknown types
            if is_unknown_type(left) or is_unknown_type(right):
                ctx.emitter.comment("runtime-dispatch add")
                compile_expr(left, ctx)
                compile_expr(right, ctx)
                ctx.emitter.emit_call("$add_dispatch")
                return

        case ast.Mult():
            # List/string/tuple repetition
            if is_list_expr(left):
                ctx.emitter.comment("list repetition")
                compile_expr(left, ctx)
                compile_expr(right, ctx)
                ctx.emitter.emit_call("$list_repeat")
                return
            if is_tuple_expr(left):
                ctx.emitter.comment("tuple repetition")
                compile_expr(left, ctx)
                compile_expr(right, ctx)
                ctx.emitter.emit_call("$tuple_repeat")
                return
            if is_string_expr(left):
                ctx.emitter.comment("string repetition")
                compile_expr(left, ctx)
                compile_expr(right, ctx)
                ctx.emitter.emit_call("$string_repeat")
                return
            if is_unknown_type(left):
                ctx.emitter.comment("runtime-dispatch mult")
                compile_expr(left, ctx)
                compile_expr(right, ctx)
                ctx.emitter.emit_call("$mult_dispatch")
                return

        case ast.Sub():
            # Runtime dispatch for unknown types (variables, function calls, etc.)
            if is_unknown_type(left) or is_unknown_type(right):
                ctx.emitter.comment("runtime-dispatch sub")
                compile_expr(left, ctx)
                compile_expr(right, ctx)
                ctx.emitter.emit_call("$sub_dispatch")
                return

        case ast.Div():
            # Division always returns float, always use dispatch
            ctx.emitter.comment("true division (returns float)")
            compile_expr(left, ctx)
            compile_expr(right, ctx)
            ctx.emitter.emit_call("$div_dispatch")
            return

        case ast.FloorDiv():
            # Floor division needs dispatch for unknown types
            if is_unknown_type(left) or is_unknown_type(right):
                ctx.emitter.comment("runtime-dispatch floordiv")
                compile_expr(left, ctx)
                compile_expr(right, ctx)
                ctx.emitter.emit_call("$floordiv_dispatch")
                return

        case ast.Mod():
            # Modulo needs dispatch for unknown types
            if is_unknown_type(left) or is_unknown_type(right):
                ctx.emitter.comment("runtime-dispatch mod")
                compile_expr(left, ctx)
                compile_expr(right, ctx)
                ctx.emitter.emit_call("$mod_dispatch")
                return

        case ast.MatMult():
            # Matrix multiplication always uses runtime dispatch
            ctx.emitter.comment("runtime-dispatch matmul")
            compile_expr(left, ctx)
            compile_expr(right, ctx)
            ctx.emitter.emit_call("$matmul_dispatch")
            return

    # Float operations (heuristic fallback)
    if is_float_expr(left) or is_float_expr(right):
        _compile_float_binop(node, ctx)
        return

    # Boolean operations need runtime dispatch (booleans are BOOL structs, not i31)
    if is_bool_expr(left) or is_bool_expr(right):
        ctx.emitter.comment("runtime-dispatch (boolean operand)")
        compile_expr(left, ctx)
        compile_expr(right, ctx)
        match op:
            case ast.Add():
                ctx.emitter.emit_call("$add_dispatch")
            case ast.Sub():
                ctx.emitter.emit_call("$sub_dispatch")
            case ast.Mult():
                ctx.emitter.emit_call("$mult_dispatch")
            case _:
                # Fall through to int binop for other ops
                _compile_int_binop(node, ctx)
        return

    # Large integer constants need runtime dispatch (INT64, not i31)
    if is_large_int_constant(left) or is_large_int_constant(right):
        ctx.emitter.comment("runtime-dispatch (large int constant)")
        compile_expr(left, ctx)
        compile_expr(right, ctx)
        match op:
            case ast.Add():
                ctx.emitter.emit_call("$int_add")
            case ast.Sub():
                ctx.emitter.emit_call("$int_sub")
            case ast.Mult():
                ctx.emitter.emit_call("$int_mul")
            case ast.FloorDiv():
                ctx.emitter.emit_call("$int_div")
            case ast.Mod():
                ctx.emitter.emit_call("$int_mod")
            case ast.BitAnd():
                ctx.emitter.emit_call("$int_and")
            case ast.BitOr():
                ctx.emitter.emit_call("$int_or")
            case ast.BitXor():
                ctx.emitter.emit_call("$int_xor")
            case _:
                # Fall through to int binop for other ops
                _compile_int_binop(node, ctx)
        return

    # Check for constant operations that might overflow i31
    # (both operands fit in i31, but result might not)
    if _operation_might_overflow(left, op, right):
        ctx.emitter.comment("safe int op (potential overflow)")
        compile_expr(left, ctx)
        compile_expr(right, ctx)
        match op:
            case ast.Add():
                ctx.emitter.emit_call("$int_add")
            case ast.Sub():
                ctx.emitter.emit_call("$int_sub")
            case ast.Mult():
                ctx.emitter.emit_call("$int_mul")
            case _:
                # Other ops don't overflow in the same way
                _compile_int_binop(node, ctx)
        return

    # Integer operations (default path - i31 range only)
    _compile_int_binop(node, ctx)


def _compile_int_binop(node: ast.BinOp, ctx: CompilerContext) -> None:
    """Compile binary operation on integers.

    Uses fast i32 path for most operations. Large integer constants are
    already handled upstream (in _binop) before this function is called,
    so we can safely assume operands fit in i31 range here.

    Note: For annotated native types (i32, i64, f64), use _compile_native_binop
    instead - this function handles Python int (IntType) operands.
    """
    left, op, right = node.left, node.op, node.right

    # Power needs special handling (can easily overflow) - use dispatch
    if isinstance(op, ast.Pow):
        ctx.emitter.comment("int pow (dispatch)")
        compile_expr(left, ctx)
        compile_expr(right, ctx)
        ctx.emitter.emit_call("$pow_dispatch")
        return

    # Fast i32 path for arithmetic and bitwise operations
    # Large constants are filtered out before reaching here (see _binop lines 434-459)
    ctx.emitter.comment("int binop (specialized)")
    compile_expr(left, ctx)
    ctx.emitter.line("(i31.get_s (ref.cast (ref i31)))  ;; left")
    compile_expr(right, ctx)
    ctx.emitter.line("(i31.get_s (ref.cast (ref i31)))  ;; right")

    match op:
        case ast.Add():
            ctx.emitter.line("i32.add")
        case ast.Sub():
            ctx.emitter.line("i32.sub")
        case ast.Mult():
            ctx.emitter.line("i32.mul")
        case ast.FloorDiv():
            ctx.emitter.line("i32.div_s")
        case ast.Mod():
            ctx.emitter.line("i32.rem_s")
        case ast.BitAnd():
            ctx.emitter.line("i32.and")
        case ast.BitOr():
            ctx.emitter.line("i32.or")
        case ast.BitXor():
            ctx.emitter.line("i32.xor")
        case ast.LShift():
            ctx.emitter.line("i32.shl")
        case ast.RShift():
            ctx.emitter.line("i32.shr_s")
        case _:
            msg = f"Operator: {type(op).__name__}"
            raise NotImplementedError(msg)

    ctx.emitter.emit_ref_i31()


def _compile_native_binop(
    node: ast.BinOp, left_type: BobType, right_type: BobType, ctx: CompilerContext
) -> None:
    """Compile binary operation on native types (i32, i64, f64).

    Uses direct WASM instructions without boxing/unboxing overhead.
    """
    left, op, right = node.left, node.op, node.right

    # Determine result type and instruction prefix
    # f64 takes precedence, then i64, then i32
    match (left_type, right_type):
        case (F64Type(), _) | (_, F64Type()):
            result_type = "f64"
        case (I64Type(), _) | (_, I64Type()):
            result_type = "i64"
        case _:
            result_type = "i32"

    # Division always produces f64
    if isinstance(op, ast.Div):
        result_type = "f64"

    ctx.emitter.comment(f"native {result_type} binop")

    # Emit left operand
    _emit_native_operand(left, left_type, result_type, ctx)

    # Emit right operand
    _emit_native_operand(right, right_type, result_type, ctx)

    # Emit the operation
    match (result_type, op):
        # i32 operations
        case ("i32", ast.Add()):
            ctx.emitter.line("i32.add")
        case ("i32", ast.Sub()):
            ctx.emitter.line("i32.sub")
        case ("i32", ast.Mult()):
            ctx.emitter.line("i32.mul")
        case ("i32", ast.FloorDiv()):
            ctx.emitter.line("i32.div_s")
        case ("i32", ast.Mod()):
            ctx.emitter.line("i32.rem_s")
        case ("i32", ast.BitAnd()):
            ctx.emitter.line("i32.and")
        case ("i32", ast.BitOr()):
            ctx.emitter.line("i32.or")
        case ("i32", ast.BitXor()):
            ctx.emitter.line("i32.xor")
        case ("i32", ast.LShift()):
            ctx.emitter.line("i32.shl")
        case ("i32", ast.RShift()):
            ctx.emitter.line("i32.shr_s")

        # i64 operations
        case ("i64", ast.Add()):
            ctx.emitter.line("i64.add")
        case ("i64", ast.Sub()):
            ctx.emitter.line("i64.sub")
        case ("i64", ast.Mult()):
            ctx.emitter.line("i64.mul")
        case ("i64", ast.FloorDiv()):
            ctx.emitter.line("i64.div_s")
        case ("i64", ast.Mod()):
            ctx.emitter.line("i64.rem_s")
        case ("i64", ast.BitAnd()):
            ctx.emitter.line("i64.and")
        case ("i64", ast.BitOr()):
            ctx.emitter.line("i64.or")
        case ("i64", ast.BitXor()):
            ctx.emitter.line("i64.xor")
        case ("i64", ast.LShift()):
            # i64 shift needs i32 shift amount - handled in operand emission
            ctx.emitter.line("i64.shl")
        case ("i64", ast.RShift()):
            ctx.emitter.line("i64.shr_s")

        # f64 operations
        case ("f64", ast.Add()):
            ctx.emitter.line("f64.add")
        case ("f64", ast.Sub()):
            ctx.emitter.line("f64.sub")
        case ("f64", ast.Mult()):
            ctx.emitter.line("f64.mul")
        case ("f64", ast.Div()):
            ctx.emitter.line("f64.div")
        case ("f64", ast.FloorDiv()):
            ctx.emitter.line("f64.div")
            ctx.emitter.line("f64.floor")
        case ("f64", ast.Mod()):
            # a % b = a - floor(a/b) * b
            ctx.emitter.line("(local.set $ftmp2)")
            ctx.emitter.line("(local.tee $ftmp1)")
            ctx.emitter.line("(local.get $ftmp1)")
            ctx.emitter.line("(local.get $ftmp2)")
            ctx.emitter.line("f64.div")
            ctx.emitter.line("f64.floor")
            ctx.emitter.line("(local.get $ftmp2)")
            ctx.emitter.line("f64.mul")
            ctx.emitter.line("f64.sub")
        case ("f64", ast.Pow()):
            ctx.emitter.line("(call $math_pow)")

        case _:
            msg = f"Native {result_type} operator: {type(op).__name__}"
            raise NotImplementedError(msg)

    # Mark that we have a native value on the stack
    match result_type:
        case "i32":
            ctx.set_native_value(NativeType.I32)
        case "i64":
            ctx.set_native_value(NativeType.I64)
        case "f64":
            ctx.set_native_value(NativeType.F64)


def _emit_native_operand(
    expr: ast.expr, expr_type: BobType, target_type: str, ctx: CompilerContext
) -> None:
    """Emit an operand for native operations, converting if needed."""
    match expr:
        # Constants - emit directly
        case ast.Constant(value=int() as val):
            match target_type:
                case "i32":
                    ctx.emitter.line(f"(i32.const {val})")
                case "i64":
                    ctx.emitter.line(f"(i64.const {val})")
                case "f64":
                    ctx.emitter.line(f"(f64.const {float(val)})")

        case ast.Constant(value=float() as val):
            ctx.emitter.line(f"(f64.const {val})")

        # Native variable - load from native local
        case ast.Name(id=name) if name in ctx.native_locals:
            native_local = ctx.get_native_local_name(name)
            native_type = ctx.native_locals[name]

            # Load the value
            ctx.emitter.line(f"(local.get {native_local})")

            # Convert if needed
            match (native_type, target_type):
                case (NativeType.I32, "i64"):
                    ctx.emitter.line("i64.extend_i32_s")
                case (NativeType.I32, "f64"):
                    ctx.emitter.line("f64.convert_i32_s")
                case (NativeType.I64, "i32"):
                    ctx.emitter.line("i32.wrap_i64")
                case (NativeType.I64, "f64"):
                    ctx.emitter.line("f64.convert_i64_s")
                case (NativeType.F64, "i32"):
                    ctx.emitter.line("i32.trunc_f64_s")
                case (NativeType.F64, "i64"):
                    ctx.emitter.line("i64.trunc_f64_s")
                case _:
                    pass  # No conversion needed

        # BinOp with native types - compile recursively
        case ast.BinOp() if is_native_type(expr_type):
            _compile_native_binop(
                expr, ctx.get_expr_type(expr.left), ctx.get_expr_type(expr.right), ctx
            )
            ctx.clear_native_value()  # Clear flag after use

        # Boxed value - need to unbox
        case _:
            compile_expr(expr, ctx)
            match (expr_type, target_type):
                case (IntType(), "i32"):
                    ctx.emitter.line("(i31.get_s (ref.cast (ref i31)))")
                case (IntType(), "i64"):
                    ctx.emitter.line(
                        "(i64.extend_i32_s (i31.get_s (ref.cast (ref i31))))"
                    )
                case (IntType(), "f64"):
                    ctx.emitter.line(
                        "(f64.convert_i32_s (i31.get_s (ref.cast (ref i31))))"
                    )
                case (FloatType(), "f64"):
                    ctx.emitter.line("(struct.get $FLOAT 0 (ref.cast (ref $FLOAT)))")
                case (FloatType(), "i32"):
                    ctx.emitter.line(
                        "(i32.trunc_f64_s (struct.get $FLOAT 0 (ref.cast (ref $FLOAT))))"
                    )
                case _:
                    # Try to convert whatever is on stack
                    match target_type:
                        case "i32":
                            ctx.emitter.line("(i31.get_s (ref.cast (ref i31)))")
                        case "i64":
                            ctx.emitter.line(
                                "(i64.extend_i32_s (i31.get_s (ref.cast (ref i31))))"
                            )
                        case "f64":
                            ctx.emitter.line(
                                "(f64.convert_i32_s (i31.get_s (ref.cast (ref i31))))"
                            )


def _emit_f64_operand(expr: ast.expr, expr_type: BobType, ctx: CompilerContext) -> None:
    """Emit an operand as raw f64 on the stack, avoiding unnecessary boxing."""
    match (expr, expr_type):
        # Float constant: emit directly as f64.const
        case (ast.Constant(value=float() as val), _):
            ctx.emitter.line(f"(f64.const {val})")
        # Int constant: emit as converted f64
        case (ast.Constant(value=int() as val), _):
            ctx.emitter.line(f"(f64.const {float(val)})")
        # Native float variable: load directly from native local (no unboxing!)
        case (ast.Name(id=name), FloatType()) if (
            name in ctx.native_locals and ctx.native_locals[name] == NativeType.F64
        ):
            native_local = ctx.get_native_local_name(name)
            ctx.emitter.line(f"(local.get {native_local})  ;; native f64")
        # Native int variable: load and convert to f64
        case (ast.Name(id=name), IntType()) if (
            name in ctx.native_locals and ctx.native_locals[name] == NativeType.I32
        ):
            native_local = ctx.get_native_local_name(name)
            ctx.emitter.line(
                f"(f64.convert_i32_s (local.get {native_local}))  ;; native i32 to f64"
            )
        # BinOp that produces float: emit directly as raw f64 without boxing
        case (ast.BinOp() as binop, FloatType()):
            _compile_float_binop_raw(binop, ctx)
        # Otherwise compile normally and unbox/convert
        case (_, FloatType()):
            compile_expr(expr, ctx)
            ctx.emitter.line(
                "(struct.get $FLOAT 0 (ref.cast (ref $FLOAT)))  ;; unbox float"
            )
        case _:
            compile_expr(expr, ctx)
            ctx.emitter.line(
                "(f64.convert_i32_s (i31.get_s (ref.cast (ref i31))))  ;; int to f64"
            )


def _compile_float_binop(node: ast.BinOp, ctx: CompilerContext) -> None:
    """Compile binary operation involving floats with direct f64 ops when possible."""
    left, op, right = node.left, node.op, node.right

    left_type = ctx.get_expr_type(left)
    right_type = ctx.get_expr_type(right)

    # Both known numeric types -> direct f64 operations
    match (left_type, right_type):
        case (FloatType() | IntType(), FloatType() | IntType()):
            ctx.emitter.comment("float binop (direct f64)")

            # Compile left operand as raw f64
            _emit_f64_operand(left, left_type, ctx)

            # Compile right operand as raw f64
            _emit_f64_operand(right, right_type, ctx)

            # Direct f64 operation
            match op:
                case ast.Add():
                    ctx.emitter.line("f64.add")
                case ast.Sub():
                    ctx.emitter.line("f64.sub")
                case ast.Mult():
                    ctx.emitter.line("f64.mul")
                case ast.Div():
                    ctx.emitter.line("f64.div")
                case ast.FloorDiv():
                    ctx.emitter.line("f64.div")
                    ctx.emitter.line("f64.floor")
                case ast.Mod():
                    # a % b = a - floor(a/b) * b
                    ctx.emitter.line("(local.set $ftmp2)")
                    ctx.emitter.line("(local.tee $ftmp1)")
                    ctx.emitter.line("(local.get $ftmp1)")
                    ctx.emitter.line("(local.get $ftmp2)")
                    ctx.emitter.line("f64.div")
                    ctx.emitter.line("f64.floor")
                    ctx.emitter.line("(local.get $ftmp2)")
                    ctx.emitter.line("f64.mul")
                    ctx.emitter.line("f64.sub")
                case ast.Pow():
                    ctx.emitter.line("(call $math_pow)")
                case _:
                    ctx.emitter.line("f64.add")

            # Box result back to $FLOAT
            ctx.emitter.emit_struct_new("$FLOAT")
            return

    # Fallback: one operand is unknown type, use dispatch
    ctx.emitter.comment("float binop (dispatch fallback)")
    compile_expr(left, ctx)
    compile_expr(right, ctx)
    match op:
        case ast.Add():
            ctx.emitter.emit_call("$add_dispatch")
        case ast.Sub():
            ctx.emitter.emit_call("$sub_dispatch")
        case ast.Mult():
            ctx.emitter.emit_call("$mult_dispatch")
        case ast.Div():
            ctx.emitter.emit_call("$div_dispatch")
        case ast.FloorDiv():
            ctx.emitter.emit_call("$floordiv_dispatch")
        case ast.Mod():
            ctx.emitter.emit_call("$mod_dispatch")
        case ast.Pow():
            ctx.emitter.emit_call("$pow_dispatch")
        case _:
            ctx.emitter.emit_call("$add_dispatch")


def _compile_float_binop_raw(node: ast.BinOp, ctx: CompilerContext) -> None:
    """Compile float binop and leave raw f64 on stack (no boxing)."""
    left, op, right = node.left, node.op, node.right

    left_type = ctx.get_expr_type(left)
    right_type = ctx.get_expr_type(right)

    # Both known numeric types -> direct f64 operations
    match (left_type, right_type):
        case (FloatType() | IntType(), FloatType() | IntType()):
            # Compile left operand as raw f64
            _emit_f64_operand(left, left_type, ctx)

            # Compile right operand as raw f64
            _emit_f64_operand(right, right_type, ctx)

            # Direct f64 operation (no boxing)
            match op:
                case ast.Add():
                    ctx.emitter.line("f64.add")
                case ast.Sub():
                    ctx.emitter.line("f64.sub")
                case ast.Mult():
                    ctx.emitter.line("f64.mul")
                case ast.Div():
                    ctx.emitter.line("f64.div")
                case ast.FloorDiv():
                    ctx.emitter.line("f64.div")
                    ctx.emitter.line("f64.floor")
                case ast.Mod():
                    # a % b = a - floor(a/b) * b
                    ctx.emitter.line("(local.set $ftmp2)")
                    ctx.emitter.line("(local.tee $ftmp1)")
                    ctx.emitter.line("(local.get $ftmp1)")
                    ctx.emitter.line("(local.get $ftmp2)")
                    ctx.emitter.line("f64.div")
                    ctx.emitter.line("f64.floor")
                    ctx.emitter.line("(local.get $ftmp2)")
                    ctx.emitter.line("f64.mul")
                    ctx.emitter.line("f64.sub")
                case ast.Pow():
                    ctx.emitter.line("(call $math_pow)")
                case _:
                    ctx.emitter.line("f64.add")
            return

    # Fallback: compile binop normally and unbox the result
    _compile_float_binop(node, ctx)
    ctx.emitter.line("(struct.get $FLOAT 0 (ref.cast (ref $FLOAT)))  ;; unbox float")


# =============================================================================
# Unary Operations
# =============================================================================


@compile_expr.register
def _unaryop(node: ast.UnaryOp, ctx: CompilerContext) -> None:
    """Compile unary operation."""
    op, operand = node.op, node.operand

    match op:
        case ast.USub():
            # Unary minus
            # Check for constant - emit negated value directly
            match operand:
                case ast.Constant(value=int() as val):
                    neg_value = -val
                    if I31_MIN <= neg_value <= I31_MAX:
                        ctx.emitter.emit_int(neg_value)
                    else:
                        ctx.emitter.emit_int64(neg_value)
                case _ if is_float_expr(operand):
                    ctx.emitter.comment("float unary minus")
                    compile_expr(operand, ctx)
                    ctx.emitter.emit_ref_cast("$FLOAT")
                    ctx.emitter.emit_struct_get("$FLOAT", 0)
                    ctx.emitter.line("f64.neg")
                    ctx.emitter.emit_struct_new("$FLOAT")
                case _:
                    # For any integer expression (including BinOps that may overflow),
                    # use runtime negation which handles both i31 and INT64
                    ctx.emitter.comment("runtime unary minus")
                    compile_expr(operand, ctx)
                    ctx.emitter.emit_call("$int_neg")

        case ast.UAdd():
            # Unary plus: just return the value
            compile_expr(operand, ctx)

        case ast.Invert():
            # Bitwise not: ~x = -1 xor x
            ctx.emitter.comment("bitwise not")
            ctx.emitter.emit_i32_const(-1)
            compile_expr(operand, ctx)
            ctx.emitter.emit_i31_get_s()
            ctx.emitter.line("i32.xor")
            ctx.emitter.emit_ref_i31()

        case ast.Not():
            compile_expr(operand, ctx)
            ctx.emitter.emit_call("$is_false")
            ctx.emitter.line("if (result (ref null eq))")
            ctx.emitter.indent_inc()
            ctx.emitter.emit_bool(True)
            ctx.emitter.indent_dec()
            ctx.emitter.line("else")
            ctx.emitter.indent_inc()
            ctx.emitter.emit_bool(False)
            ctx.emitter.indent_dec()
            ctx.emitter.line("end")


# =============================================================================
# Comparisons
# =============================================================================


@compile_expr.register
def _compare(node: ast.Compare, ctx: CompilerContext) -> None:
    """Compile comparison expression."""
    compile_compare(node.left, node.ops, node.comparators, ctx)


# =============================================================================
# Boolean Operations
# =============================================================================


@compile_expr.register
def _boolop(node: ast.BoolOp, ctx: CompilerContext) -> None:
    """Compile boolean operation (and/or)."""
    op, values = node.op, node.values

    match op:
        case ast.And():
            # Short-circuit and: if first is false, return it
            compile_expr(values[0], ctx)
            for val in values[1:]:
                ctx.emitter.emit_local_tee("$tmp")
                ctx.emitter.emit_call("$is_false")
                ctx.emitter.line("if (result (ref null eq))")
                ctx.emitter.indent_inc()
                ctx.emitter.emit_local_get("$tmp")
                ctx.emitter.indent_dec()
                ctx.emitter.line("else")
                ctx.emitter.indent_inc()
                compile_expr(val, ctx)
                ctx.emitter.indent_dec()
                ctx.emitter.line("end")

        case ast.Or():
            # Short-circuit or: if first is true, return it
            compile_expr(values[0], ctx)
            for val in values[1:]:
                ctx.emitter.emit_local_tee("$tmp")
                ctx.emitter.emit_call("$is_false")
                ctx.emitter.line("if (result (ref null eq))")
                ctx.emitter.indent_inc()
                compile_expr(val, ctx)
                ctx.emitter.indent_dec()
                ctx.emitter.line("else")
                ctx.emitter.indent_inc()
                ctx.emitter.emit_local_get("$tmp")
                ctx.emitter.indent_dec()
                ctx.emitter.line("end")


# =============================================================================
# Conditional Expression
# =============================================================================


@compile_expr.register
def _ifexp(node: ast.IfExp, ctx: CompilerContext) -> None:
    """Compile conditional expression (ternary)."""
    compile_expr(node.test, ctx)
    ctx.emitter.emit_call("$is_false")
    ctx.emitter.line("if (result (ref null eq))")
    ctx.emitter.indent_inc()
    compile_expr(node.orelse, ctx)
    ctx.emitter.indent_dec()
    ctx.emitter.line("else")
    ctx.emitter.indent_inc()
    compile_expr(node.body, ctx)
    ctx.emitter.indent_dec()
    ctx.emitter.line("end")


# =============================================================================
# Collections
# =============================================================================


@compile_expr.register
def _list(node: ast.List, ctx: CompilerContext) -> None:
    """Compile list literal."""
    compile_list(node.elts, ctx)


@compile_expr.register
def _tuple(node: ast.Tuple, ctx: CompilerContext) -> None:
    """Compile tuple literal using $TUPLE type."""
    compile_tuple(node.elts, ctx)


@compile_expr.register
def _set(node: ast.Set, ctx: CompilerContext) -> None:
    """Compile set literal."""
    compile_set(node.elts, ctx)


@compile_expr.register
def _dict(node: ast.Dict, ctx: CompilerContext) -> None:
    """Compile dict literal."""
    compile_dict(node.keys, node.values, ctx)


# =============================================================================
# Comprehensions
# =============================================================================


@compile_expr.register
def _listcomp(node: ast.ListComp, ctx: CompilerContext) -> None:
    """Compile list comprehension."""
    compile_listcomp(node.elt, node.generators, ctx)


@compile_expr.register
def _generatorexp(node: ast.GeneratorExp, ctx: CompilerContext) -> None:
    """Compile generator expression as eager list.

    For now, generator expressions are compiled as lists.
    This works correctly for list(), sum(), join(), etc.
    True lazy generators would require state machine transformation.
    """
    compile_listcomp(node.elt, node.generators, ctx)


@compile_expr.register
def _setcomp(node: ast.SetComp, ctx: CompilerContext) -> None:
    """Compile set comprehension."""
    # First build as a list
    compile_listcomp(node.elt, node.generators, ctx)
    # Then convert to set (removes duplicates)
    ctx.emitter.emit_call("$list_to_set")


@compile_expr.register
def _dictcomp(node: ast.DictComp, ctx: CompilerContext) -> None:
    """Compile dict comprehension."""
    compile_dictcomp(node.key, node.value, node.generators, ctx)


# =============================================================================
# Subscript
# =============================================================================


@compile_expr.register
def _subscript(node: ast.Subscript, ctx: CompilerContext) -> None:
    """Compile subscript access."""
    compile_subscript(node.value, node.slice, ctx)


# =============================================================================
# Function Calls
# =============================================================================


@compile_expr.register
def _call(node: ast.Call, ctx: CompilerContext) -> None:
    """Compile function call."""
    compile_call(node.func, node.args, node.keywords, ctx)


# =============================================================================
# Lambda
# =============================================================================


@compile_expr.register
def _lambda(node: ast.Lambda, ctx: CompilerContext) -> None:
    """Compile lambda expression."""
    compile_lambda(node.args, node.body, ctx)


# =============================================================================
# Attribute Access
# =============================================================================


@compile_expr.register
def _attribute(node: ast.Attribute, ctx: CompilerContext) -> None:
    """Compile attribute access."""
    # Check for js.X pattern (JavaScript interop)
    match node.value:
        case ast.Name(id="js") if ctx.js_imported:
            _compile_js_global(node.attr, ctx)
            return

    # Check for js.document.X or js.window.X pattern
    if ctx.js_imported and _is_js_object_access(node.value, ctx):
        _compile_js_property_get(node, ctx)
        return

    # Check for slotted instance attribute access
    match node.value:
        case ast.Name(id=var_name):
            class_name = ctx.get_slotted_instance_class(var_name)
            if class_name:
                slot_idx = ctx.get_slot_index(class_name, node.attr)
                if slot_idx is not None:
                    # Direct struct field access for slotted class
                    type_name = ctx.get_slotted_type_name(class_name)
                    # Field index: 0 is $class, slots start at 1
                    field_idx = slot_idx + 1
                    ctx.emitter.comment(f"slotted attr: {var_name}.{node.attr}")
                    compile_expr(node.value, ctx)
                    ctx.emitter.emit_ref_cast(type_name)
                    ctx.emitter.line(f"(struct.get {type_name} {field_idx})")
                    return

    ctx.emitter.comment(f"attribute access: .{node.attr}")
    compile_expr(node.value, ctx)
    ctx.emitter.emit_string(node.attr)
    ctx.emitter.emit_call("$object_getattr")


def _is_js_object_access(node: ast.expr, ctx: CompilerContext) -> bool:
    """Check if expression is a JS object (document, window, element, etc.)."""
    if not ctx.js_imported:
        return False

    match node:
        # js.document, js.window, js.console
        case ast.Attribute(value=ast.Name(id="js"), attr=attr) if attr in {
            "document",
            "window",
            "console",
        }:
            return True
        # Variable known to hold JS handle
        case ast.Name(id=name) if name in ctx.js_handle_vars:
            return True
        # Chained access like js.document.body
        case ast.Attribute(value=inner):
            return _is_js_object_access(inner, ctx)
        case _:
            return False


def _compile_js_global(attr: str, ctx: CompilerContext) -> None:
    """Compile js.document, js.window, js.console access."""
    ctx.emitter.comment(f"js.{attr}")

    match attr:
        case "document":
            # Document handle is always 1
            ctx.emitter.line("(ref.i31 (i32.const 1))  ;; document handle")
        case "window":
            # Window handle is always 2
            ctx.emitter.line("(ref.i31 (i32.const 2))  ;; window handle")
        case "console":
            # Console handle is always 3
            ctx.emitter.line("(ref.i31 (i32.const 3))  ;; console handle")
        case _:
            msg = f"js.{attr} not supported"
            raise NotImplementedError(msg)


def _compile_js_property_get(node: ast.Attribute, ctx: CompilerContext) -> None:
    """Compile property access on JS object."""
    ctx.emitter.comment(f"js property get: .{node.attr}")
    compile_expr(node.value, ctx)
    ctx.emitter.emit_string(node.attr)
    ctx.emitter.emit_call("$js_get_property")


# =============================================================================
# F-Strings
# =============================================================================


@compile_expr.register
def _joinedstr(node: ast.JoinedStr, ctx: CompilerContext) -> None:
    """Compile f-string."""
    compile_fstring(node.values, ctx)


@compile_expr.register
def _formattedvalue(node: ast.FormattedValue, ctx: CompilerContext) -> None:
    """Compile formatted value inside f-string."""
    compile_expr(node.value, ctx)

    # Check for format specifier
    format_spec = _extract_format_spec(node)
    if format_spec:
        _compile_formatted_with_spec(format_spec, ctx)
    else:
        ctx.emitter.emit_call("$value_to_string")


def _extract_format_spec(node: ast.FormattedValue) -> str | None:
    """Extract format specification string from FormattedValue node."""
    match node.format_spec:
        case ast.JoinedStr(values=[ast.Constant(value=str() as spec)]):
            return spec
        case _:
            return None


def _parse_format_spec(spec: str) -> dict:
    """Parse format specification string.

    Format: [[fill]align][sign][#][0][width][grouping_option][.precision][type]
    Returns dict with: fill, align, zero_pad, width, comma, precision, type
    """
    result = {
        "fill": " ",
        "align": None,
        "zero_pad": False,
        "width": 0,
        "comma": False,
        "precision": -1,
        "type": "",
    }

    if not spec:
        return result

    i = 0

    # Check for fill and align (fill can be any char if followed by align)
    if len(spec) >= 2 and spec[1] in "<>^=":
        result["fill"] = spec[0]
        result["align"] = spec[1]
        i = 2
    elif spec and spec[0] in "<>^=":
        result["align"] = spec[0]
        i = 1

    # Check for zero padding (0 before width)
    if i < len(spec) and spec[i] == "0":
        result["zero_pad"] = True
        result["fill"] = "0"
        result["align"] = result["align"] or ">"
        i += 1

    # Parse width
    width_start = i
    while i < len(spec) and spec[i].isdigit():
        i += 1
    if i > width_start:
        result["width"] = int(spec[width_start:i])

    # Check for comma (thousands separator)
    if i < len(spec) and spec[i] == ",":
        result["comma"] = True
        i += 1

    # Check for precision
    if i < len(spec) and spec[i] == ".":
        i += 1
        prec_start = i
        while i < len(spec) and spec[i].isdigit():
            i += 1
        if i > prec_start:
            result["precision"] = int(spec[prec_start:i])

    # Check for type
    if i < len(spec):
        result["type"] = spec[i]

    return result


def _compile_formatted_with_spec(spec: str, ctx: CompilerContext) -> None:
    """Compile value formatting with a format specification."""
    parsed = _parse_format_spec(spec)

    # Handle precision for floats first (before converting to string)
    if parsed["precision"] >= 0:
        ctx.emitter.comment(f"format with precision {parsed['precision']}")
        ctx.emitter.emit_i32_const(parsed["precision"])
        ctx.emitter.emit_call("$format_precision")
    else:
        ctx.emitter.emit_call("$value_to_string")

    # Handle thousands separator
    if parsed["comma"]:
        ctx.emitter.comment("add thousands separator")
        ctx.emitter.emit_call("$format_with_commas")

    # Handle width and alignment
    if parsed["width"] > 0:
        ctx.emitter.comment(f"align width={parsed['width']}")
        ctx.emitter.emit_i32_const(parsed["width"])
        # Encode fill char as i32
        fill_code = ord(parsed["fill"])
        ctx.emitter.emit_i32_const(fill_code)
        # Encode align: 0=right, 1=left, 2=center
        align_map = {">": 0, "<": 1, "^": 2, "=": 0, None: 0}
        align_code = align_map.get(parsed["align"], 0)
        ctx.emitter.emit_i32_const(align_code)
        ctx.emitter.emit_call("$format_align")


# =============================================================================
# Walrus Operator
# =============================================================================


@compile_expr.register
def _namedexpr(node: ast.NamedExpr, ctx: CompilerContext) -> None:
    """Compile walrus operator (:=)."""
    match node.target:
        case ast.Name(id=name):
            pass
        case _:
            msg = "Walrus operator target must be a name"
            raise NotImplementedError(msg)
    ctx.emitter.comment(f"walrus operator ':=' for '{name}'")
    compile_expr(node.value, ctx)

    # Box native value if needed ($tmp is ref null eq)
    if ctx.has_native_value:
        ctx.emitter.emit_ref_i31()  # Box i32 to i31 ref
        ctx.clear_native_value()

    ctx.emitter.emit_local_tee("$tmp")

    if name in ctx.local_vars:
        ctx.emitter.emit_local_set(ctx.local_vars[name])
    else:
        local_name = f"$var_{name}"
        ctx.local_vars[name] = local_name
        ctx.emitter.emit_local_set(local_name)

    # Also update native local if variable has one
    if name in ctx.native_locals:
        native_type = ctx.native_locals[name]
        native_local = ctx.get_native_local_name(name)
        ctx.emitter.emit_local_get("$tmp")
        match native_type:
            case NativeType.I32:
                ctx.emitter.line(
                    f"(local.set {native_local} (i31.get_s (ref.cast (ref i31))))"
                )
            case NativeType.I64:
                ctx.emitter.line(
                    f"(local.set {native_local} "
                    "(struct.get $INT64 0 (ref.cast (ref $INT64))))"
                )
            case NativeType.F64:
                ctx.emitter.line(
                    f"(local.set {native_local} "
                    "(struct.get $FLOAT 0 (ref.cast (ref $FLOAT))))"
                )

    ctx.emitter.emit_local_get("$tmp")


# =============================================================================
# Yield and YieldFrom
# =============================================================================


@compile_expr.register
def _yield(node: ast.Yield, ctx: CompilerContext) -> None:
    """Compile yield expression.

    Note: yield is typically handled specially in generator compilation.
    This handler is for when yield appears in non-generator context (error).
    """
    msg = "yield outside of generator function"
    raise SyntaxError(msg)


@compile_expr.register
def _yieldfrom(node: ast.YieldFrom, ctx: CompilerContext) -> None:
    """Compile yield from expression.

    Note: yield from is typically transformed before compilation.
    This handler is for when it appears in non-generator context (error).
    """
    msg = "yield from outside of generator function"
    raise SyntaxError(msg)
