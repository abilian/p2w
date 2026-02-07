"""Expression compilation dispatcher.

This module contains only the singledispatch function with no handlers.
Handlers are registered in expr_handlers.py which must be imported
to activate them.
"""

from __future__ import annotations

from functools import singledispatch
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import ast

    from p2w.compiler.context import CompilerContext


@singledispatch
def compile_expr(node: ast.expr, ctx: CompilerContext) -> None:
    """Compile an expression, leaving result on stack."""
    msg = f"Expression not implemented: {type(node).__name__}"
    raise NotImplementedError(msg)
