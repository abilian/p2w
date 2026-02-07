"""Comparison compilation."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from p2w.compiler.codegen.expressions import compile_expr
from p2w.compiler.types import (
    F64Type,
    FloatType,
    I64Type,
    IntType,
    NativeType,
    is_native_type,
)

if TYPE_CHECKING:
    from p2w.compiler.context import CompilerContext


def compile_compare(
    left: ast.expr,
    ops: list[ast.cmpop],
    comparators: list[ast.expr],
    ctx: CompilerContext,
) -> None:
    """Compile comparison expression."""

    if len(ops) == 1:
        _compile_single_compare(left, ops[0], comparators[0], ctx)
    else:
        # Chained comparison
        ctx.emitter.comment("chained comparison")
        _compile_single_compare(left, ops[0], comparators[0], ctx)

        for i in range(1, len(ops)):
            ctx.emitter.emit_local_tee("$tmp")
            ctx.emitter.emit_call("$is_false")
            ctx.emitter.line("if (result (ref null eq))")
            ctx.emitter.indent_inc()
            ctx.emitter.emit_local_get("$tmp")
            ctx.emitter.indent_dec()
            ctx.emitter.line("else")
            ctx.emitter.indent_inc()
            _compile_single_compare(comparators[i - 1], ops[i], comparators[i], ctx)
            ctx.emitter.indent_dec()
            ctx.emitter.line("end")


def _is_native_f64_expr(expr: ast.expr, ctx: CompilerContext) -> bool:
    """Check if expression produces a native f64 value."""
    match expr:
        case ast.Name(id=name) if name in ctx.native_locals:
            return ctx.native_locals[name] == NativeType.F64
        case ast.Constant(value=float()):
            return True
        case ast.BinOp(left=left, right=right):
            # BinOp is native if both operands are native f64
            return _is_native_f64_expr(left, ctx) and _is_native_f64_expr(right, ctx)
        case ast.UnaryOp(operand=operand):
            return _is_native_f64_expr(operand, ctx)
        case _:
            return False


def _can_use_native_compare(
    left: ast.expr, right: ast.expr, left_type, right_type, ctx: CompilerContext
) -> bool:
    """Check if types can use native WASM comparison."""
    # Check if both operands produce native f64 values
    left_is_native_f64 = _is_native_f64_expr(left, ctx)
    right_is_native_f64 = _is_native_f64_expr(right, ctx)

    if left_is_native_f64 and right_is_native_f64:
        return True

    # Both native types - obviously yes
    if is_native_type(left_type) and is_native_type(right_type):
        return True
    # One native, one boxed numeric
    if is_native_type(left_type) and isinstance(right_type, (IntType, FloatType)):
        return True
    return bool(
        is_native_type(right_type) and isinstance(left_type, (IntType, FloatType))
    )


def _compile_single_compare(
    left: ast.expr, op: ast.cmpop, right: ast.expr, ctx: CompilerContext
) -> None:
    """Compile a single comparison."""
    # Check for native type comparisons
    left_type = ctx.get_expr_type(left)
    right_type = ctx.get_expr_type(right)

    if _can_use_native_compare(left, right, left_type, right_type, ctx):
        _compile_native_compare(left, op, right, left_type, right_type, ctx)
        return

    match op:
        case ast.Is():
            compile_expr(left, ctx)
            compile_expr(right, ctx)
            ctx.emitter.line("ref.eq")
            _emit_bool_result(ctx)

        case ast.IsNot():
            compile_expr(left, ctx)
            compile_expr(right, ctx)
            ctx.emitter.line("ref.eq")
            _emit_bool_result(ctx, invert=True)

        case ast.In():
            _compile_in_operator(left, right, negated=False, ctx=ctx)

        case ast.NotIn():
            _compile_in_operator(left, right, negated=True, ctx=ctx)

        case ast.Eq():
            compile_expr(left, ctx)
            compile_expr(right, ctx)
            ctx.emitter.emit_call("$values_equal")
            _emit_bool_result(ctx)

        case ast.NotEq():
            compile_expr(left, ctx)
            compile_expr(right, ctx)
            ctx.emitter.emit_call("$values_equal")
            ctx.emitter.line("i32.eqz")
            _emit_bool_result(ctx)

        case ast.Lt() | ast.LtE() | ast.Gt() | ast.GtE():
            # Comparisons - use helper functions that dispatch to __lt__/__gt__/__le__/__ge__
            compile_expr(left, ctx)
            compile_expr(right, ctx)

            match op:
                case ast.Lt():
                    ctx.emitter.emit_call("$compare_lt")
                case ast.LtE():
                    ctx.emitter.emit_call("$compare_le")
                case ast.Gt():
                    ctx.emitter.emit_call("$compare_gt")
                case ast.GtE():
                    ctx.emitter.emit_call("$compare_ge")

            _emit_bool_result(ctx)

        case _:
            msg = f"Comparison: {type(op).__name__}"
            raise NotImplementedError(msg)


def _compile_native_compare(
    left: ast.expr,
    op: ast.cmpop,
    right: ast.expr,
    left_type,
    right_type,
    ctx: CompilerContext,
) -> None:
    """Compile comparison between native types using WASM instructions."""
    # Determine the comparison type (promote to larger type)
    # Check for native locals first
    left_is_f64 = (
        isinstance(left, ast.Name)
        and left.id in ctx.native_locals
        and ctx.native_locals[left.id] == NativeType.F64
    )
    right_is_f64 = (
        isinstance(right, ast.Name)
        and right.id in ctx.native_locals
        and ctx.native_locals[right.id] == NativeType.F64
    )
    left_is_float_const = isinstance(left, ast.Constant) and isinstance(
        left.value, float
    )
    right_is_float_const = isinstance(right, ast.Constant) and isinstance(
        right.value, float
    )

    # Determine comparison type
    if (
        left_is_f64
        or right_is_f64
        or left_is_float_const
        or right_is_float_const
        or isinstance(left_type, (F64Type, FloatType))
        or isinstance(right_type, (F64Type, FloatType))
    ):
        cmp_type = "f64"
    elif isinstance(left_type, I64Type) or isinstance(right_type, I64Type):
        cmp_type = "i64"
    else:
        cmp_type = "i32"

    ctx.emitter.comment(f"native {cmp_type} compare")

    # Emit operands
    _emit_native_compare_operand(left, left_type, cmp_type, ctx)
    _emit_native_compare_operand(right, right_type, cmp_type, ctx)

    # Emit comparison instruction
    match (cmp_type, op):
        case ("i32", ast.Lt()):
            ctx.emitter.line("i32.lt_s")
        case ("i32", ast.LtE()):
            ctx.emitter.line("i32.le_s")
        case ("i32", ast.Gt()):
            ctx.emitter.line("i32.gt_s")
        case ("i32", ast.GtE()):
            ctx.emitter.line("i32.ge_s")
        case ("i32", ast.Eq()):
            ctx.emitter.line("i32.eq")
        case ("i32", ast.NotEq()):
            ctx.emitter.line("i32.ne")

        case ("i64", ast.Lt()):
            ctx.emitter.line("i64.lt_s")
        case ("i64", ast.LtE()):
            ctx.emitter.line("i64.le_s")
        case ("i64", ast.Gt()):
            ctx.emitter.line("i64.gt_s")
        case ("i64", ast.GtE()):
            ctx.emitter.line("i64.ge_s")
        case ("i64", ast.Eq()):
            ctx.emitter.line("i64.eq")
        case ("i64", ast.NotEq()):
            ctx.emitter.line("i64.ne")

        case ("f64", ast.Lt()):
            ctx.emitter.line("f64.lt")
        case ("f64", ast.LtE()):
            ctx.emitter.line("f64.le")
        case ("f64", ast.Gt()):
            ctx.emitter.line("f64.gt")
        case ("f64", ast.GtE()):
            ctx.emitter.line("f64.ge")
        case ("f64", ast.Eq()):
            ctx.emitter.line("f64.eq")
        case ("f64", ast.NotEq()):
            ctx.emitter.line("f64.ne")

        case _:
            msg = f"Native {cmp_type} comparison: {type(op).__name__}"
            raise NotImplementedError(msg)

    # Convert i32 result to BOOL
    _emit_bool_result(ctx)


def _emit_native_compare_operand(
    expr: ast.expr, expr_type, target_type: str, ctx: CompilerContext
) -> None:
    """Emit operand for native comparison."""
    match expr:
        # Constants
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

        # Native variable
        case ast.Name(id=name) if name in ctx.native_locals:
            native_local = ctx.get_native_local_name(name)
            native_type = ctx.native_locals[name]

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
                    pass

        # Fallback: compile and unbox (unless already native)
        case _:
            compile_expr(expr, ctx)
            # Check if compile_expr produced a native value
            if ctx.has_native_value:
                ctx.clear_native_value()
                # Value is already native, may need conversion
                # For now assume it matches target_type (native binops produce correct type)
            else:
                # Value is boxed, need to unbox
                match target_type:
                    case "i32":
                        ctx.emitter.line("(i31.get_s (ref.cast (ref i31)))")
                    case "i64":
                        ctx.emitter.line(
                            "(i64.extend_i32_s (i31.get_s (ref.cast (ref i31))))"
                        )
                    case "f64":
                        ctx.emitter.line(
                            "(struct.get $FLOAT 0 (ref.cast (ref $FLOAT)))"
                        )


def _emit_bool_result(ctx: CompilerContext, *, invert: bool = False) -> None:
    """Emit code to convert i32 result to bool."""
    ctx.emitter.line("if (result (ref null eq))")
    ctx.emitter.indent_inc()
    ctx.emitter.emit_bool(not invert)
    ctx.emitter.indent_dec()
    ctx.emitter.line("else")
    ctx.emitter.indent_inc()
    ctx.emitter.emit_bool(invert)
    ctx.emitter.indent_dec()
    ctx.emitter.line("end")


def _compile_in_operator(
    item: ast.expr, container: ast.expr, *, negated: bool, ctx: CompilerContext
) -> None:
    """Compile 'in' or 'not in' operator."""
    ctx.emitter.comment("in operator")
    compile_expr(item, ctx)
    compile_expr(container, ctx)
    ctx.emitter.emit_call("$container_contains")
    _emit_bool_result(ctx, invert=negated)
