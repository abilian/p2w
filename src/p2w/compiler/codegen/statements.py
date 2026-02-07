"""Statement compilation dispatcher.

This module contains only the singledispatch function with no handlers.
Handlers are registered in stmt_handlers.py which must be imported
to activate them.
"""

from __future__ import annotations

from functools import singledispatch
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import ast

    from p2w.compiler.context import CompilerContext


@singledispatch
def compile_stmt(node: ast.stmt, ctx: CompilerContext) -> None:
    """Compile a statement."""
    msg = f"Statement not implemented: {type(node).__name__}"
    raise NotImplementedError(msg)
