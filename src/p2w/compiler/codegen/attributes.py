"""Attribute compilation."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from p2w.compiler.codegen.expressions import compile_expr

if TYPE_CHECKING:
    from p2w.compiler.context import CompilerContext


def _is_js_object(obj: ast.expr, ctx: CompilerContext) -> bool:
    """Check if an expression is known to be a JS handle."""
    match obj:
        case ast.Name(id=name) if name in ctx.js_handle_vars:
            return True
        case _:
            return False


def compile_attribute_assignment(
    target: ast.Attribute, value: ast.expr, ctx: CompilerContext
) -> None:
    """Compile attribute assignment: obj.attr = value."""
    # Check if this is a JS object property assignment
    if ctx.js_imported and _is_js_object(target.value, ctx):
        ctx.emitter.comment(f"JS: {target.value}.{target.attr} = ...")
        compile_expr(target.value, ctx)  # JS handle
        ctx.emitter.emit_string(target.attr)  # Property name
        compile_expr(value, ctx)  # Value
        ctx.emitter.emit_call("$js_set_property")
        ctx.emitter.emit_drop()
        return

    # Check if this is a slotted instance attribute assignment
    if isinstance(target.value, ast.Name):
        class_name = ctx.get_slotted_instance_class(target.value.id)
        if class_name:
            slot_idx = ctx.get_slot_index(class_name, target.attr)
            if slot_idx is not None:
                # Direct struct field assignment for slotted class
                type_name = ctx.get_slotted_type_name(class_name)
                # Field index: 0 is $class, slots start at 1
                field_idx = slot_idx + 1
                ctx.emitter.comment(f"slotted attr: self.{target.attr} = ...")
                compile_expr(target.value, ctx)
                ctx.emitter.emit_ref_cast(type_name)
                compile_expr(value, ctx)
                ctx.emitter.line(f"(struct.set {type_name} {field_idx})")
                return

    # Standard Python attribute assignment
    ctx.emitter.comment(f"{target.value}.{target.attr} = ...")
    compile_expr(target.value, ctx)
    ctx.emitter.emit_string(target.attr)
    compile_expr(value, ctx)
    ctx.emitter.emit_call("$object_setattr")
    ctx.emitter.emit_drop()


def compile_attribute_aug_assignment(
    target: ast.Attribute, op: ast.operator, value: ast.expr, ctx: CompilerContext
) -> None:
    """Compile augmented attribute assignment: obj.attr += value."""
    ctx.emitter.comment(f"{target.value}.{target.attr} {type(op).__name__}= ...")

    compile_expr(target.value, ctx)
    ctx.emitter.emit_string(target.attr)
    ctx.emitter.emit_call("$object_getattr")

    compile_expr(value, ctx)

    match op:
        case ast.Add():
            ctx.emitter.emit_call("$add_dispatch")
        case ast.Sub():
            ctx.emitter.emit_call("$sub_dispatch")
        case ast.Mult():
            ctx.emitter.emit_call("$mult_dispatch")
        case ast.FloorDiv():
            ctx.emitter.emit_call("$floordiv_dispatch")
        case ast.Mod():
            ctx.emitter.emit_call("$mod_dispatch")
        case _:
            msg = f"Aug assignment operator not implemented: {type(op).__name__}"
            raise NotImplementedError(msg)

    ctx.emitter.line("(local.set $tmp)  ;; save new_value")
    compile_expr(target.value, ctx)
    ctx.emitter.emit_string(target.attr)
    ctx.emitter.emit_local_get("$tmp")
    ctx.emitter.emit_call("$object_setattr")
    ctx.emitter.emit_drop()
