"""Code generation module - compiles Python AST to WAT."""
# ruff: noqa: I001 - Import order is intentional (handlers must follow dispatchers)

from __future__ import annotations

# Import dispatchers first
from p2w.compiler.codegen.expressions import compile_expr
from p2w.compiler.codegen.statements import compile_stmt

# Import handlers to register them with the dispatchers
from p2w.compiler.codegen import expr_handlers as _expr_handlers  # noqa: F401
from p2w.compiler.codegen import stmt_handlers as _stmt_handlers  # noqa: F401

__all__ = ["compile_expr", "compile_stmt"]
