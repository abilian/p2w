"""Exception handling compilation (raise, try/except/finally)."""

from __future__ import annotations

import ast

from p2w.compiler.codegen.expressions import compile_expr
from p2w.compiler.codegen.statements import compile_stmt
from p2w.compiler.context import CompilerContext  # noqa: TC001


@compile_stmt.register
def _raise(node: ast.Raise, ctx: CompilerContext) -> None:
    """Compile raise statement."""
    ctx.emitter.comment("raise statement")

    if node.exc is None:
        # Bare 'raise' - re-raise current exception
        # This only works inside an except handler
        ctx.emitter.comment("re-raise current exception")
        ctx.emitter.emit_local_get("$exc")
        ctx.emitter.emit_throw()
        return

    # Evaluate the exception expression
    # It could be an exception type (like ValueError) or an exception instance
    exc_expr = node.exc

    match exc_expr:
        # Call like ValueError("message")
        case ast.Call(func=ast.Name(id=exc_type), args=args):
            ctx.emitter.comment(f"raise {exc_type}(...)")
            ctx.emitter.emit_string(exc_type)
            # Get the message argument if provided
            if args:
                compile_expr(args[0], ctx)
            else:
                ctx.emitter.emit_null_eq()
            # Handle 'from' clause for exception chaining
            if node.cause:
                compile_expr(node.cause, ctx)
                ctx.emitter.emit_call("$make_exception_with_cause")
            else:
                ctx.emitter.emit_call("$make_exception")
            ctx.emitter.emit_throw()

        # Bare exception type name (raise ValueError)
        case ast.Name(id=exc_type):
            ctx.emitter.comment(f"raise {exc_type}")
            ctx.emitter.emit_string(exc_type)
            ctx.emitter.emit_null_eq()  # No message
            ctx.emitter.emit_call("$make_exception")
            ctx.emitter.emit_throw()

        # General case: evaluate the expression and hope it's an exception
        case _:
            ctx.emitter.comment("raise (general expression)")
            compile_expr(exc_expr, ctx)
            # Assume it's already an exception object
            ctx.emitter.emit_ref_cast("$EXCEPTION")
            ctx.emitter.emit_throw()


@compile_stmt.register
def _try(node: ast.Try, ctx: CompilerContext) -> None:
    """Compile try/except/finally statement using try_table."""
    ctx.emitter.comment("try statement")

    has_finally = bool(node.finalbody)
    has_except = bool(node.handlers)
    has_else = bool(node.orelse)

    # We need a local to store the exception for handlers
    exc_local = "$exc"

    # Generate unique labels for this try statement
    label_id = ctx.next_label_id()
    try_end_label = f"$try_end_{label_id}"
    catch_label = f"$catch_{label_id}"

    if has_finally:
        # For finally, we need to track if an exception occurred
        # and rethrow it after finally block
        finally_label = f"$finally_{label_id}"
        catch_all_label = f"$catch_all_{label_id}"

        # Outer block for entire try/except/finally
        ctx.emitter.line(f"(block {try_end_label} (result (ref null eq))")
        ctx.emitter.indent_inc()

        # Block for finally (normal path)
        ctx.emitter.line(f"(block {finally_label}")
        ctx.emitter.indent_inc()

        # Block for catch_all (for rethrowing after finally)
        ctx.emitter.line(f"(block {catch_all_label} (result exnref)")
        ctx.emitter.indent_inc()

        if has_except:
            # Block for specific exception handler
            ctx.emitter.line(f"(block {catch_label} (result (ref $EXCEPTION))")
            ctx.emitter.indent_inc()

            # try_table with both catch and catch_all_ref
            ctx.emitter.line(
                f"(try_table (result (ref null eq)) "
                f"(catch $PyException {catch_label}) "
                f"(catch_all_ref {catch_all_label})"
            )
            ctx.emitter.indent_inc()

            # Compile try body
            for stmt in node.body:
                compile_stmt(stmt, ctx)

            # If no exception, execute else block (if any)
            if has_else:
                ctx.emitter.comment("else block (no exception)")
                for stmt in node.orelse:
                    compile_stmt(stmt, ctx)

            ctx.emitter.emit_null_eq()  # success result
            ctx.emitter.indent_dec()
            ctx.emitter.line(")")  # end try_table

            # No exception - jump to finally (normal path)
            ctx.emitter.line(f"br {finally_label}")
            ctx.emitter.indent_dec()
            ctx.emitter.line(")")  # end catch block

            # Exception caught - exception ref is on stack
            ctx.emitter.emit_local_set(exc_local)

            # Generate handler dispatch
            _compile_except_handlers(
                node.handlers, exc_local, ctx, finally_label, catch_all_label
            )

            # Jump to finally after handler
            ctx.emitter.line(f"br {finally_label}")
        else:
            # No except handlers, just try_table with catch_all_ref for finally
            ctx.emitter.line(
                f"(try_table (result (ref null eq)) (catch_all_ref {catch_all_label})"
            )
            ctx.emitter.indent_inc()

            for stmt in node.body:
                compile_stmt(stmt, ctx)
            ctx.emitter.emit_null_eq()

            ctx.emitter.indent_dec()
            ctx.emitter.line(")")  # end try_table
            ctx.emitter.line(f"br {finally_label}")

        ctx.emitter.indent_dec()
        ctx.emitter.line(")")  # end catch_all block

        # catch_all_ref path - exnref is on stack
        ctx.emitter.comment("finally block (exception path)")
        ctx.emitter.line("(local.set $exnref)")
        for stmt in node.finalbody:
            compile_stmt(stmt, ctx)
        ctx.emitter.line("(local.get $exnref)")
        ctx.emitter.line("(throw_ref)")
        ctx.emitter.line("unreachable")

        ctx.emitter.indent_dec()
        ctx.emitter.line(")")  # end finally block

        # finally block (normal path)
        ctx.emitter.comment("finally block (normal path)")
        for stmt in node.finalbody:
            compile_stmt(stmt, ctx)

        ctx.emitter.emit_null_eq()
        ctx.emitter.indent_dec()
        ctx.emitter.line(")")  # end try_end block

    elif has_except:
        # Simple try/except without finally
        ctx.emitter.line(f"(block {try_end_label} (result (ref null eq))")
        ctx.emitter.indent_inc()

        # Block for exception handler
        ctx.emitter.line(f"(block {catch_label} (result (ref $EXCEPTION))")
        ctx.emitter.indent_inc()

        # try_table
        ctx.emitter.line(
            f"(try_table (result (ref null eq)) (catch $PyException {catch_label})"
        )
        ctx.emitter.indent_inc()

        # Compile try body
        for stmt in node.body:
            compile_stmt(stmt, ctx)

        # If no exception, execute else block (if any)
        if has_else:
            ctx.emitter.comment("else block (no exception)")
            for stmt in node.orelse:
                compile_stmt(stmt, ctx)

        ctx.emitter.emit_null_eq()  # success result
        ctx.emitter.indent_dec()
        ctx.emitter.line(")")  # end try_table

        # No exception - jump to end
        ctx.emitter.line(f"br {try_end_label}")
        ctx.emitter.indent_dec()
        ctx.emitter.line(")")  # end catch block

        # Exception caught - exception ref is on stack
        ctx.emitter.emit_local_set(exc_local)

        # Generate handler dispatch
        _compile_except_handlers(node.handlers, exc_local, ctx, try_end_label, None)

        ctx.emitter.indent_dec()
        ctx.emitter.line(")")  # end try_end block

    else:
        # No except or finally, just compile body
        for stmt in node.body:
            compile_stmt(stmt, ctx)
        ctx.emitter.emit_null_eq()

    # Drop the result (try is a statement, not expression)
    ctx.emitter.emit_drop()


def _compile_except_handlers(
    handlers: list[ast.ExceptHandler],
    exc_local: str,
    ctx: CompilerContext,
    end_label: str,
    rethrow_label: str | None,
) -> None:
    """Compile except handler dispatch.

    Args:
        handlers: List of except handlers
        exc_local: Name of local variable holding the exception
        ctx: Compiler context
        end_label: Label to branch to after handler executes
        rethrow_label: Label for catch_all_ref handler (for finally rethrow), or None
    """
    for i, handler in enumerate(handlers):
        is_last = i == len(handlers) - 1

        if handler.type is None:
            # Bare 'except:' catches everything
            ctx.emitter.comment("except: (catch all)")
            if handler.name:
                # Bind exception to name
                ctx.emitter.emit_local_get(exc_local)
                ctx.emitter.emit_local_set(ctx.local_vars[handler.name])

            # Execute handler body
            for stmt in handler.body:
                compile_stmt(stmt, ctx)

            # Return None as result and branch to end
            ctx.emitter.emit_null_eq()
            ctx.emitter.line(f"br {end_label}")
        else:
            # Check if exception matches this handler's type
            exc_type_name = _get_exception_type_name(handler.type)
            ctx.emitter.comment(f"except {exc_type_name}:")

            # Check exception type (cast nullable to non-nullable)
            ctx.emitter.emit_local_get(exc_local)
            ctx.emitter.emit_ref_cast("$EXCEPTION")
            ctx.emitter.emit_string(exc_type_name)
            ctx.emitter.emit_call("$exception_matches")

            ctx.emitter.emit_if_start("(ref null eq)")

            # Match: bind exception if named
            if handler.name:
                ctx.emitter.emit_local_get(exc_local)
                ctx.emitter.emit_local_set(ctx.local_vars[handler.name])

            # Execute handler body
            for stmt in handler.body:
                compile_stmt(stmt, ctx)

            # Return None as result and branch to end
            ctx.emitter.emit_null_eq()
            ctx.emitter.line(f"br {end_label}")

            ctx.emitter.emit_if_else()

            if is_last:
                # No more handlers, re-raise
                ctx.emitter.comment("no handler matched, re-raise")
                ctx.emitter.emit_local_get(exc_local)
                ctx.emitter.emit_ref_cast("$EXCEPTION")
                ctx.emitter.emit_throw()
            # else: next handler will be compiled

    # Close all the if/else blocks
    for i, handler in enumerate(handlers):
        if handler.type is not None:
            ctx.emitter.emit_if_end()


def _get_exception_type_name(type_node: ast.expr) -> str:
    """Extract exception type name from AST node."""
    match type_node:
        case ast.Name(id=name):
            return name
        case ast.Tuple(elts=[ast.Name(id=first_name), *_]):
            # Multiple exception types in tuple - use first for now
            return first_name
        case _:
            return "Exception"
