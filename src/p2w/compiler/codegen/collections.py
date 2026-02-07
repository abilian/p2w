"""Collection compilation - lists, sets, dicts."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from p2w.compiler.codegen.expressions import compile_expr

if TYPE_CHECKING:
    from p2w.compiler.context import CompilerContext

# Re-export comprehensions for backwards compatibility
from p2w.compiler.codegen.comprehensions import (  # noqa: F401
    compile_dictcomp,
    compile_listcomp,
)


def compile_list(elements: list[ast.expr], ctx: CompilerContext) -> None:
    """Compile list literal."""

    if not elements:
        ctx.emitter.emit_empty_list()
        return

    # Check if any element is a starred expression
    has_starred = any(isinstance(e, ast.Starred) for e in elements)

    if not has_starred:
        # Simple case: no starred expressions
        ctx.emitter.comment("list literal")
        for element in elements:
            compile_expr(element, ctx)
        ctx.emitter.emit_list_construct(len(elements))
    else:
        # Complex case: list contains starred expressions
        # Build list incrementally using list_concat
        ctx.emitter.comment("list literal with starred expressions")
        ctx.emitter.emit_list_terminator()  # Start with empty list

        for element in elements:
            if isinstance(element, ast.Starred):
                # Starred expression: compile the value and concat
                compile_expr(element.value, ctx)
                ctx.emitter.emit_call("$list_concat")
            else:
                # Regular element: wrap in single-element list and concat
                compile_expr(element, ctx)
                ctx.emitter.emit_null_eq()
                ctx.emitter.emit_struct_new("$PAIR")  # Single element list
                ctx.emitter.emit_call("$list_concat")


def compile_tuple(elements: list[ast.expr], ctx: CompilerContext) -> None:
    """Compile tuple literal using $TUPLE type for proper repr."""
    ctx.emitter.comment("tuple literal")
    for element in elements:
        compile_expr(element, ctx)
    ctx.emitter.emit_tuple_construct(len(elements))


def compile_set(elements: list[ast.expr], ctx: CompilerContext) -> None:
    """Compile set literal."""

    ctx.emitter.comment("set literal")
    ctx.emitter.emit_list_terminator()
    for element in elements:
        compile_expr(element, ctx)
        ctx.emitter.emit_set_add()


def compile_dict(
    keys: list[ast.expr | None], values: list[ast.expr], ctx: CompilerContext
) -> None:
    """Compile dict literal using hash table for O(1) operations."""

    has_spread = any(k is None for k in keys)

    if not keys:
        ctx.emitter.emit_empty_dict()
        return

    ctx.emitter.comment("dict literal (hash table)")
    # Create new hash table-based dict
    ctx.emitter.line("(call $dict_new)")

    for key, value in zip(keys, values):
        if key is None:
            # Spread operator: merge another dict
            compile_expr(value, ctx)
            ctx.emitter.line("call $dict_update  ;; merge spread dict")
        else:
            # Regular key-value: set in hash table
            compile_expr(key, ctx)
            compile_expr(value, ctx)
            ctx.emitter.line("call $dict_set_wrapped  ;; set key-value")
