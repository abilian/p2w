"""Tuple and starred unpacking compilation."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from p2w.compiler.codegen.expressions import compile_expr
from p2w.compiler.types import NativeType

if TYPE_CHECKING:
    from p2w.compiler.context import CompilerContext


def _update_native_local(name: str, ctx: CompilerContext) -> None:
    """Update native local after boxed assignment if variable has one.

    Assumes the boxed value is already stored in the boxed local.
    Reads from boxed local, unboxes, and stores to native local.
    """
    if name not in ctx.native_locals:
        return

    native_type = ctx.native_locals[name]
    native_local = ctx.get_native_local_name(name)
    boxed_local = ctx.local_vars[name]

    ctx.emitter.emit_local_get(boxed_local)
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


def compile_tuple_unpack(
    target: ast.Tuple | ast.List, value: ast.expr, ctx: CompilerContext
) -> None:
    """Compile tuple/list unpacking assignment."""
    # Check if there's a starred target
    starred_idx = None
    for i, elt in enumerate(target.elts):
        if isinstance(elt, ast.Starred):
            starred_idx = i
            break

    if starred_idx is not None:
        compile_starred_unpack(target, value, starred_idx, ctx)
        return

    ctx.emitter.comment("tuple unpacking")

    compile_expr(value, ctx)
    ctx.emitter.emit_local_set("$tmp")

    for i, elt in enumerate(target.elts):
        match elt:
            case ast.Name(id=name) if name in ctx.local_vars:
                ctx.emitter.emit_local_get("$tmp")
                ctx.emitter.emit_int(i)
                ctx.emitter.emit_call("$subscript_get")
                ctx.emitter.emit_local_set(ctx.local_vars[name])
                # Also update native local if variable has one
                _update_native_local(name, ctx)
            case ast.Name(id=name):
                msg = f"Variable '{name}' not declared"
                raise NameError(msg)
            case _:
                msg = f"Tuple unpack target not implemented: {type(elt).__name__}"
                raise NotImplementedError(msg)


def compile_starred_unpack(
    target: ast.Tuple | ast.List,
    value: ast.expr,
    starred_idx: int,
    ctx: CompilerContext,
) -> None:
    """Compile starred unpacking like: first, *rest, last = sequence."""
    ctx.emitter.comment("starred unpacking")

    elts = target.elts
    before_count = starred_idx
    after_count = len(elts) - starred_idx - 1

    # Compile the value and store in $tmp
    compile_expr(value, ctx)
    ctx.emitter.emit_local_set("$tmp")

    # Assign elements before the starred target
    for i in range(before_count):
        elt = elts[i]
        match elt:
            case ast.Name(id=name) if name in ctx.local_vars:
                ctx.emitter.emit_local_get("$tmp")
                ctx.emitter.emit_int(i)
                ctx.emitter.emit_call("$subscript_get")
                ctx.emitter.emit_local_set(ctx.local_vars[name])
                # Also update native local if variable has one
                _update_native_local(name, ctx)
            case _:
                msg = f"Starred unpack target not implemented: {type(elt).__name__}"
                raise NotImplementedError(msg)

    # Assign the starred element (rest)
    # Note: In Python, starred unpacking ALWAYS produces a list, even from tuples
    starred_elt = elts[starred_idx]
    match starred_elt:
        case ast.Starred(value=ast.Name(id=name)) if name in ctx.local_vars:
            # Get slice from before_count to len-after_count
            # $slice takes: container, lower (i32), upper (i32), step (i32)
            # -999999 is the sentinel for "use default"
            ctx.emitter.emit_local_get("$tmp")
            ctx.emitter.emit_i32_const(before_count)
            if after_count == 0:
                # rest goes to end: lst[before_count:]
                ctx.emitter.emit_i32_const(-999999)  # sentinel for "to end"
            else:
                # rest stops before trailing elements: lst[before_count:-after_count]
                ctx.emitter.emit_i32_const(-after_count)
            ctx.emitter.emit_i32_const(1)  # step = 1
            ctx.emitter.emit_call("$slice")
            # Convert to list if result is a tuple (starred always produces list)
            ctx.emitter.emit_call("$ensure_list")
            ctx.emitter.emit_local_set(ctx.local_vars[name])
        case ast.Starred(value=ast.Name(id=name)):
            msg = f"Variable '{name}' not declared"
            raise NameError(msg)
        case _:
            msg = "Starred target must be a simple name"
            raise NotImplementedError(msg)

    # Assign elements after the starred target
    for i in range(after_count):
        elt = elts[starred_idx + 1 + i]
        match elt:
            case ast.Name(id=name) if name in ctx.local_vars:
                # Use negative indexing: -(after_count - i)
                ctx.emitter.emit_local_get("$tmp")
                ctx.emitter.emit_int(-(after_count - i))
                ctx.emitter.emit_call("$subscript_get")
                ctx.emitter.emit_local_set(ctx.local_vars[name])
                # Also update native local if variable has one
                _update_native_local(name, ctx)
            case _:
                msg = f"Starred unpack target not implemented: {type(elt).__name__}"
                raise NotImplementedError(msg)
