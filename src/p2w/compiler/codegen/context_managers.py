"""Context manager compilation (with statement)."""

from __future__ import annotations

import ast

from p2w.compiler.codegen.expressions import compile_expr
from p2w.compiler.codegen.statements import compile_stmt
from p2w.compiler.context import CompilerContext  # noqa: TC001


@compile_stmt.register
def _with(node: ast.With, ctx: CompilerContext) -> None:
    """Compile with statement (context managers).

    Compiles:
        with expr as var:
            body

    Into equivalent code:
        __cm = expr
        __val = __cm.__enter__()
        var = __val  # if 'as var' present
        __exc = None
        try:
            body
        except:
            __exc = current_exception
            if not __cm.__exit__(__exc):
                raise
        else:
            __cm.__exit__(None)

    For multiple context managers (with a, b, c:), we recursively compile
    as nested with statements.
    """
    ctx.emitter.comment("with statement")

    # Handle multiple context managers by recursively nesting
    if len(node.items) > 1:
        # Compile first context manager with remaining items as nested with
        first_item = node.items[0]
        remaining_items = node.items[1:]
        # Create a synthetic inner with node for remaining items
        inner_with = ast.With(items=remaining_items, body=node.body)
        # Compile outer with statement with inner_with as its body
        outer_node = ast.With(items=[first_item], body=[inner_with])
        _compile_single_with(outer_node.items[0], outer_node.body, ctx)
        return

    # Single context manager - compile directly
    _compile_single_with(node.items[0], node.body, ctx)


def _compile_single_with(
    item: ast.withitem, body: list[ast.stmt], ctx: CompilerContext
) -> None:
    """Compile a single context manager item with its body."""
    context_expr = item.context_expr
    optional_var = item.optional_vars

    # Generate unique IDs for this with statement
    with_id = ctx.next_with_id()  # For local variable names
    label_id = ctx.next_label_id()  # For block labels
    with_end_label = f"$with_end_{label_id}"
    with_catch_label = f"$with_catch_{label_id}"
    cm_local = f"$with_cm_{with_id}"  # Context manager local
    method_local = f"$with_method_{with_id}"  # Method local

    # Compile context expression and call __enter__
    ctx.emitter.comment("evaluate context manager")
    compile_expr(context_expr, ctx)
    ctx.emitter.emit_local_set(cm_local)  # Save context manager

    # Call __enter__ using method dispatch
    ctx.emitter.comment("call __enter__")
    ctx.emitter.emit_local_get(cm_local)  # object for attr lookup
    ctx.emitter.emit_string("__enter__")
    ctx.emitter.emit_call("$object_getattr")
    ctx.emitter.emit_local_set(method_local)  # save method
    ctx.emitter.emit_local_get(cm_local)  # object (self)
    ctx.emitter.emit_local_get(method_local)  # method
    ctx.emitter.emit_null_eq()  # No args
    ctx.emitter.emit_call("$call_method_dispatch")

    # Bind result if 'as var' present
    if optional_var is not None and isinstance(optional_var, ast.Name):
        var_name = optional_var.id
        if var_name in ctx.local_vars:
            ctx.emitter.emit_local_set(ctx.local_vars[var_name])
        elif var_name in ctx.global_vars:
            ctx.emitter.emit_global_set(f"$global_{var_name}")
        else:
            msg = f"Variable '{var_name}' not declared"
            raise NameError(msg)
    else:
        ctx.emitter.emit_drop()  # Discard __enter__ result

    # Body wrapped in try/except structure
    ctx.emitter.line(f"(block {with_end_label} (result (ref null eq))")
    ctx.emitter.indent_inc()

    ctx.emitter.line(f"(block {with_catch_label} (result (ref $EXCEPTION))")
    ctx.emitter.indent_inc()

    ctx.emitter.line(
        f"(try_table (result (ref null eq)) (catch $PyException {with_catch_label})"
    )
    ctx.emitter.indent_inc()

    # Compile body
    for stmt in body:
        compile_stmt(stmt, ctx)

    ctx.emitter.emit_null_eq()
    ctx.emitter.indent_dec()
    ctx.emitter.line(")")  # end try_table

    # No exception - call __exit__ with None
    ctx.emitter.comment("no exception - call __exit__(None, None, None)")
    ctx.emitter.emit_local_get(cm_local)  # context manager for attr lookup
    ctx.emitter.emit_string("__exit__")
    ctx.emitter.emit_call("$object_getattr")
    ctx.emitter.emit_local_set(method_local)  # save method
    ctx.emitter.emit_local_get(cm_local)  # object (self)
    ctx.emitter.emit_local_get(method_local)  # method
    # Build args list: (None, None, None)
    ctx.emitter.emit_null_eq()  # None
    ctx.emitter.emit_null_eq()  # None
    ctx.emitter.emit_null_eq()  # None
    ctx.emitter.emit_list_terminator()
    ctx.emitter.emit_pair_cons()
    ctx.emitter.emit_pair_cons()
    ctx.emitter.emit_pair_cons()
    ctx.emitter.emit_call("$call_method_dispatch")
    ctx.emitter.emit_drop()  # Ignore __exit__ return value

    ctx.emitter.line(f"br {with_end_label}")
    ctx.emitter.indent_dec()
    ctx.emitter.line(")")  # end catch block

    # Exception caught - call __exit__ with exception
    ctx.emitter.comment("exception - call __exit__ with exception info")
    ctx.emitter.emit_local_set("$exc")  # Save exception

    ctx.emitter.emit_local_get(cm_local)  # context manager for attr lookup
    ctx.emitter.emit_string("__exit__")
    ctx.emitter.emit_call("$object_getattr")
    ctx.emitter.emit_local_set(method_local)  # save method
    ctx.emitter.emit_local_get(cm_local)  # object (self)
    ctx.emitter.emit_local_get(method_local)  # method

    # Build args list with exception type name, exception, and None for traceback
    # For simplicity, pass exception type as string, exception object, and None
    ctx.emitter.emit_local_get("$exc")
    ctx.emitter.emit_ref_cast("$EXCEPTION")
    ctx.emitter.emit_struct_get("$EXCEPTION", "$type")  # Exception type name string
    ctx.emitter.emit_local_get("$exc")  # Exception object
    ctx.emitter.emit_null_eq()  # traceback (None)
    ctx.emitter.emit_list_terminator()
    ctx.emitter.emit_pair_cons()
    ctx.emitter.emit_pair_cons()
    ctx.emitter.emit_pair_cons()
    ctx.emitter.emit_call("$call_method_dispatch")

    # Check if __exit__ returned truthy (suppress exception)
    # $is_false returns 1 for falsy, so we check if it's NOT false
    ctx.emitter.emit_call("$is_false")
    ctx.emitter.line("i32.eqz")  # Invert: truthy if NOT false
    ctx.emitter.emit_if_start()
    # __exit__ returned True - suppress exception
    ctx.emitter.emit_null_eq()
    ctx.emitter.line(f"br {with_end_label}")
    ctx.emitter.emit_if_else()
    # __exit__ returned False - re-raise exception
    ctx.emitter.emit_local_get("$exc")
    ctx.emitter.emit_ref_cast("$EXCEPTION")
    ctx.emitter.emit_throw()
    ctx.emitter.emit_if_end()

    ctx.emitter.emit_null_eq()  # Unreachable, but needed for block result
    ctx.emitter.indent_dec()
    ctx.emitter.line(")")  # end with_end block

    ctx.emitter.emit_drop()  # Statement drops result
