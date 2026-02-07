"""F-string compilation."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from p2w.compiler.codegen.expressions import compile_expr

if TYPE_CHECKING:
    from p2w.compiler.context import CompilerContext


def compile_fstring(values: list[ast.expr], ctx: CompilerContext) -> None:
    """Compile f-string."""

    ctx.emitter.comment("f-string")

    if not values:
        ctx.emitter.emit_string("")
        return

    # Emit all parts
    for value in values:
        match value:
            case ast.Constant(value=str() as s):
                ctx.emitter.emit_string(s)
            case ast.FormattedValue():
                compile_expr(value, ctx)
            case _:
                compile_expr(value, ctx)
                ctx.emitter.emit_call("$value_to_string")

    # Concatenate
    if len(values) > 1:
        for _ in range(len(values) - 1):
            ctx.emitter.emit_call("$string_concat")
