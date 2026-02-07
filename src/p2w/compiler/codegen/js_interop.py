"""JavaScript interop method calls compilation."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from p2w.compiler.codegen.expressions import compile_expr

if TYPE_CHECKING:
    from p2w.compiler.context import CompilerContext


def is_js_method_call(obj: ast.expr, ctx: CompilerContext) -> bool:
    """Check if this is a method call on a JS object."""
    if not ctx.js_imported:
        return False

    match obj:
        # js.document.method(), js.window.method(), js.console.method()
        case ast.Attribute(value=ast.Name(id="js"), attr=attr) if attr in {
            "document",
            "window",
            "console",
        }:
            return True
        # variable.method() where variable holds JS handle
        case ast.Name(id=name) if name in ctx.js_handle_vars:
            return True
        # Chained: js.document.body.method()
        case ast.Attribute(value=inner):
            return is_js_method_call(inner, ctx)
        case _:
            return False


def compile_js_method_call(
    obj: ast.expr,
    method: str,
    args: list[ast.expr],
    ctx: CompilerContext,
) -> None:
    """Compile JavaScript method call."""
    ctx.emitter.comment(f"js method call: .{method}()")

    # Detect the JS object type for specialized handling
    js_obj_type = _get_js_object_type(obj)

    # console.log() -> js_console_log
    if js_obj_type == "console" and method == "log":
        if args:
            compile_expr(args[0], ctx)
            ctx.emitter.emit_call("$js_console_log_value")
        return

    # document.getElementById() -> js_get_element_by_id
    if js_obj_type == "document" and method == "getElementById":
        if args:
            compile_expr(args[0], ctx)
            # Convert string to (offset, len) and call import
            ctx.emitter.emit_call("$js_document_get_element_by_id")
        return

    # document.createElement()
    if js_obj_type == "document" and method == "createElement":
        if args:
            compile_expr(args[0], ctx)
            ctx.emitter.emit_call("$js_document_create_element")
        return

    # element.appendChild()
    if method == "appendChild":
        compile_expr(obj, ctx)
        compile_expr(args[0], ctx)
        ctx.emitter.emit_call("$js_element_append_child")
        return

    # canvas.getContext()
    if method == "getContext":
        compile_expr(obj, ctx)
        if args:
            compile_expr(args[0], ctx)
        else:
            ctx.emitter.emit_string("2d")  # default to "2d"
        ctx.emitter.emit_call("$js_canvas_get_context")
        return

    # Canvas 2D context methods
    if method == "fillRect" and len(args) == 4:
        compile_expr(obj, ctx)
        for arg in args:
            compile_expr(arg, ctx)
        ctx.emitter.emit_call("$js_canvas_fill_rect")
        return

    if method == "fillText" and len(args) >= 2:
        compile_expr(obj, ctx)
        compile_expr(args[0], ctx)  # text
        compile_expr(args[1], ctx)  # x
        if len(args) >= 3:
            compile_expr(args[2], ctx)  # y
        else:
            ctx.emitter.line("(ref.i31 (i32.const 0))")  # default y=0
        ctx.emitter.emit_call("$js_canvas_fill_text")
        return

    if method == "beginPath":
        compile_expr(obj, ctx)
        ctx.emitter.emit_call("$js_canvas_begin_path")
        return

    if method == "moveTo" and len(args) == 2:
        compile_expr(obj, ctx)
        compile_expr(args[0], ctx)
        compile_expr(args[1], ctx)
        ctx.emitter.emit_call("$js_canvas_move_to")
        return

    if method == "lineTo" and len(args) == 2:
        compile_expr(obj, ctx)
        compile_expr(args[0], ctx)
        compile_expr(args[1], ctx)
        ctx.emitter.emit_call("$js_canvas_line_to")
        return

    if method == "stroke":
        compile_expr(obj, ctx)
        ctx.emitter.emit_call("$js_canvas_stroke")
        return

    # element.addEventListener()
    if method == "addEventListener":
        compile_expr(obj, ctx)  # element handle
        compile_expr(args[0], ctx)  # event type string
        compile_expr(args[1], ctx)  # handler function
        ctx.emitter.emit_call("$js_element_add_event_listener")
        return

    # event.preventDefault()
    if method == "preventDefault":
        compile_expr(obj, ctx)
        ctx.emitter.emit_call("$js_event_prevent_default")
        return

    # Generic property/method access
    # Fall back to getting property (which might be a function)
    ctx.emitter.comment(f"js generic method: {method}")
    compile_expr(obj, ctx)
    ctx.emitter.emit_string(method)

    # Build args as PAIR chain
    if args:
        for arg in args:
            compile_expr(arg, ctx)
        ctx.emitter.emit_null_eq()
        for _ in args:
            ctx.emitter.emit_struct_new("$PAIR")
    else:
        ctx.emitter.emit_null_eq()

    ctx.emitter.emit_call("$js_call_method")


def _get_js_object_type(obj: ast.expr) -> str | None:
    """Get the type of JS object (document, window, console, or None)."""
    match obj:
        case ast.Attribute(value=ast.Name(id="js"), attr=attr):
            return attr  # "document", "window", "console"
        case _:
            return None
