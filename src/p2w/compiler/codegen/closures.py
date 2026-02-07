"""Closure-related helper functions."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from p2w.compiler.context import CompilerContext


def emit_captured_var(var: str, ctx: CompilerContext) -> None:
    """Emit code to capture a single variable for a closure."""
    if var in ctx.local_vars:
        ctx.emitter.line(f"(local.get {ctx.local_vars[var]})  ;; capture {var}")
        return

    if var in ctx.current_nonlocal_decls:
        try:
            depth, slot = ctx.lexical_env.lookup(var)
        except NameError:
            msg = f"Cannot find cell for pass-through: {var}"
            raise NameError(msg) from None

        ctx.emitter.comment(f"pass-through cell {var}")
        ctx.emitter.emit_local_get("$env")
        for _ in range(depth):
            ctx.emitter.line("(struct.get $ENV 0)  ;; parent")
        ctx.emitter.line("(struct.get $ENV 1)  ;; values")
        for _ in range(slot):
            ctx.emitter.line("(struct.get $PAIR 1 (ref.cast (ref $PAIR)))  ;; cdr")
        ctx.emitter.line("(struct.get $PAIR 0 (ref.cast (ref $PAIR)))  ;; cell")
        return

    msg = f"Cannot capture variable: {var}"
    raise NameError(msg)


def find_nested_nonlocals(body: list[ast.stmt], outer_locals: set[str]) -> set[str]:
    """Find variables that nested functions declare as nonlocal."""
    result: set[str] = set()

    def visit_stmts(stmts: list[ast.stmt]) -> None:
        for stmt in stmts:
            match stmt:
                case ast.FunctionDef(body=func_body):
                    for inner_stmt in func_body:
                        if isinstance(inner_stmt, ast.Nonlocal):
                            for name in inner_stmt.names:
                                if name in outer_locals:
                                    result.add(name)
                    visit_stmts(func_body)
                case ast.If(body=if_body, orelse=else_body):
                    visit_stmts(if_body)
                    visit_stmts(else_body)
                case ast.While(body=while_body):
                    visit_stmts(while_body)
                case ast.For(body=for_body):
                    visit_stmts(for_body)

    visit_stmts(body)
    return result


def find_all_nested_nonlocals(body: list[ast.stmt]) -> set[str]:
    """Find ALL variables that nested functions declare as nonlocal."""
    result: set[str] = set()

    def visit_stmts(stmts: list[ast.stmt]) -> None:
        for stmt in stmts:
            match stmt:
                case ast.FunctionDef(body=func_body):
                    for inner_stmt in func_body:
                        if isinstance(inner_stmt, ast.Nonlocal):
                            result.update(inner_stmt.names)
                    visit_stmts(func_body)
                case ast.If(body=if_body, orelse=else_body):
                    visit_stmts(if_body)
                    visit_stmts(else_body)
                case ast.While(body=while_body):
                    visit_stmts(while_body)
                case ast.For(body=for_body):
                    visit_stmts(for_body)

    visit_stmts(body)
    return result
