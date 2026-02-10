"""Variable loading and assignment compilation."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from p2w.compiler.builtins import BUILTINS
from p2w.compiler.codegen.expressions import compile_expr
from p2w.compiler.types import (
    F64Type,
    FloatType,
    I32Type,
    I64Type,
    IntType,
    NativeType,
)

if TYPE_CHECKING:
    from p2w.compiler.context import CompilerContext


def _box_if_native(ctx: CompilerContext) -> None:
    """Box the value on stack if it's a native (unboxed) type.

    After compile_expr, if the result is a native type (i32/i64/f64),
    we need to box it before using it in contexts that expect eqref.
    """
    if ctx.has_native_value:
        native_type = ctx.current_native_type
        match native_type:
            case NativeType.I32:
                ctx.emitter.comment("box i32 -> i31")
                ctx.emitter.emit_ref_i31()
            case NativeType.I64:
                ctx.emitter.comment("box i64 -> INT64")
                ctx.emitter.emit_struct_new("$INT64")
            case NativeType.F64:
                ctx.emitter.comment("box f64 -> FLOAT")
                ctx.emitter.emit_struct_new("$FLOAT")
        ctx.clear_native_value()


def compile_var_load(name: str, ctx: CompilerContext) -> None:
    """Emit code to load a variable's value."""
    # Check if declared global in current function
    if name in ctx.current_global_decls:
        ctx.emitter.comment(f"load global '{name}'")
        ctx.emitter.emit_global_get(f"$global_{name}")
        return

    # Check if declared nonlocal in current function
    if name in ctx.current_nonlocal_decls:
        try:
            depth, slot = ctx.lexical_env.lookup(name)
            ctx.emitter.comment(f"load nonlocal '{name}'")
            ctx.emitter.emit_local_get("$env")
            for _ in range(depth):
                ctx.emitter.line("(struct.get $ENV 0)  ;; parent")
            ctx.emitter.line("(struct.get $ENV 1)  ;; values")
            for _ in range(slot):
                ctx.emitter.line("(struct.get $PAIR 1 (ref.cast (ref $PAIR)))  ;; cdr")
            ctx.emitter.line(
                "(struct.get $PAIR 0 (ref.cast (ref $PAIR)))  ;; car (cell)"
            )
            ctx.emitter.line(
                "(struct.get $PAIR 0 (ref.cast (ref $PAIR)))  ;; cell value"
            )
            return
        except NameError:
            msg = f"Nonlocal variable '{name}' not found in enclosing scope"
            raise NameError(msg) from None

    # Check local variables first
    if name in ctx.local_vars:
        if name in ctx.cell_vars:
            ctx.emitter.comment(f"load cell var '{name}'")
            ctx.emitter.emit_local_get(ctx.local_vars[name])
            ctx.emitter.line("(struct.get $PAIR 0 (ref.cast (ref $PAIR)))")
        elif name in ctx.global_vars and len(ctx.lexical_env.frames) <= 1:
            ctx.emitter.comment(f"load module-level global '{name}'")
            ctx.emitter.emit_global_get(f"$global_{name}")
        elif name in ctx.native_locals:
            # Load from native local and box
            native_type = ctx.native_locals[name]
            native_local = ctx.get_native_local_name(name)
            ctx.emitter.comment(f"load native '{name}' (box)")
            match native_type:
                case NativeType.F64:
                    ctx.emitter.line(f"(struct.new $FLOAT (local.get {native_local}))")
                case NativeType.I32:
                    ctx.emitter.line(f"(ref.i31 (local.get {native_local}))")
                case NativeType.I64:
                    # Box as INT64
                    ctx.emitter.line(f"(struct.new $INT64 (local.get {native_local}))")
        else:
            ctx.emitter.comment(f"load local '{name}'")
            ctx.emitter.emit_local_get(ctx.local_vars[name])
        return

    # Special builtin classes
    if name == "object":
        ctx.emitter.comment("builtin object class")
        ctx.emitter.line(
            "(struct.new $CLASS "
            "(struct.new $STRING (i32.const 0) (i32.const 0)) "
            "(ref.null eq) (ref.null $CLASS))"
        )
        return

    # Ellipsis builtin
    if name == "Ellipsis":
        ctx.emitter.comment("builtin Ellipsis")
        ctx.emitter.emit_ellipsis()
        return

    # Check if it's a builtin first (before environment lookup)
    for i, b in enumerate(BUILTINS):
        if b.name == name:
            ctx.emitter.comment(f"builtin {name}")
            ctx.emitter.line(f"(struct.new $CLOSURE (ref.null $ENV) (i32.const {i}))")
            return

    # Check if it's a module-level global (e.g., class names)
    if name in ctx.global_vars:
        ctx.emitter.comment(f"load global '{name}'")
        ctx.emitter.emit_global_get(f"$global_{name}")
        return

    # Look up in lexical environment
    depth, slot = ctx.lexical_env.lookup(name)
    ctx.emitter.comment(f"load variable '{name}'")
    ctx.emitter.emit_local_get("$env")

    for _ in range(depth):
        ctx.emitter.line("(struct.get $ENV 0)  ;; parent")

    ctx.emitter.line("(struct.get $ENV 1)  ;; values")
    for _ in range(slot):
        ctx.emitter.line("(struct.get $PAIR 1 (ref.cast (ref $PAIR)))  ;; cdr")
    ctx.emitter.line("(struct.get $PAIR 0 (ref.cast (ref $PAIR)))  ;; car")


def _is_js_call(value: ast.expr, ctx: CompilerContext) -> bool:
    """Check if an expression is a JS method call that returns a handle."""
    if not ctx.js_imported:
        return False
    match value:
        # js.document.X(), js.window.X(), js.console.X()
        case ast.Call(
            func=ast.Attribute(value=ast.Attribute(value=ast.Name(id="js"), attr=attr))
        ) if attr in {"document", "window", "console"}:
            return True
        # element.method(...) where element is a JS handle
        case ast.Call(func=ast.Attribute(value=ast.Name(id=name))) if (
            name in ctx.js_handle_vars
        ):
            return True
        case _:
            return False


def compile_assignment(name: str, value: ast.expr, ctx: CompilerContext) -> None:
    """Emit variable assignment."""
    # Track JS handle variables
    if _is_js_call(value, ctx):
        ctx.js_handle_vars.add(name)

    # Track slotted class instances for optimized attribute access
    is_global_var = name in ctx.current_global_decls or name in ctx.global_vars
    match value:
        case ast.Call(func=ast.Name(id=class_name)) if (
            class_name in ctx.slotted_classes
        ):
            # Direct constructor call: x = Record(...)
            ctx.register_slotted_instance(name, class_name, is_global=is_global_var)
        case ast.Call(func=ast.Attribute(value=ast.Name(id=obj_name), attr=attr)) if (
            attr
            in {
                "clone",
                "copy",
            }
        ):
            # Method call: x = obj.clone() / obj.copy()
            obj_class = ctx.get_slotted_instance_class(obj_name)
            if obj_class:
                ctx.register_slotted_instance(name, obj_class, is_global=is_global_var)

    # Check if declared global in current function
    if name in ctx.current_global_decls:
        ctx.emitter.comment(f"assign global '{name}'")
        compile_expr(value, ctx)
        _box_if_native(ctx)  # Box native values for global
        ctx.emitter.emit_global_set(f"$global_{name}")
        return

    # Check if declared nonlocal in current function
    if name in ctx.current_nonlocal_decls:
        compile_nonlocal_assignment(name, value, ctx)
        return

    ctx.emitter.comment(f"assign '{name}'")

    # Check if this is a cell variable first
    if name in ctx.cell_vars and name in ctx.local_vars:
        ctx.emitter.line(f"(local.get {ctx.local_vars[name]})  ;; get cell")
        ctx.emitter.line("(ref.cast (ref $PAIR))")
        compile_expr(value, ctx)
        _box_if_native(ctx)  # Box native values for cell
        ctx.emitter.line("(struct.set $PAIR 0)  ;; set cell value")
    elif (
        name in ctx.global_vars
        and name in ctx.local_vars
        and len(ctx.lexical_env.frames) <= 1
    ):
        compile_expr(value, ctx)
        _box_if_native(ctx)  # Box native values for module-level
        ctx.emitter.emit_local_tee(ctx.local_vars[name])
        ctx.emitter.emit_global_set(f"$global_{name}")
    elif name in ctx.native_locals:
        # Store to native local - try to emit raw value directly
        native_type = ctx.native_locals[name]
        native_local = ctx.get_native_local_name(name)

        # For module-level code, also store boxed value so nested functions can access it
        # via the lexical environment
        is_module_level = len(ctx.lexical_env.frames) <= 1

        match native_type:
            case NativeType.F64:
                ctx.emitter.comment(f"assign native f64 '{name}'")
                _emit_raw_f64_value(value, ctx)
                if is_module_level and name in ctx.local_vars:
                    # Store raw value to native local, then box for lexical env
                    ctx.emitter.line(f"(local.tee {native_local})")
                    ctx.emitter.line("(struct.new $FLOAT)")
                    ctx.emitter.emit_local_set(ctx.local_vars[name])
                else:
                    ctx.emitter.line(f"(local.set {native_local})")
            case NativeType.I32:
                ctx.emitter.comment(f"assign native i32 '{name}'")
                _emit_raw_i32_value(value, ctx)
                if is_module_level and name in ctx.local_vars:
                    # Store raw value to native local, then box for lexical env
                    ctx.emitter.line(f"(local.tee {native_local})")
                    ctx.emitter.emit_ref_i31()
                    ctx.emitter.emit_local_set(ctx.local_vars[name])
                else:
                    ctx.emitter.line(f"(local.set {native_local})")
            case NativeType.I64:
                # Fallback to compile + unbox for i64
                ctx.emitter.comment(f"assign native i64 '{name}'")
                compile_expr(value, ctx)
                if is_module_level and name in ctx.local_vars:
                    # Store boxed value and also extract to native local
                    ctx.emitter.emit_local_tee(ctx.local_vars[name])
                    ctx.emitter.line(
                        f"(local.set {native_local} "
                        "(struct.get $INT64 0 (ref.cast (ref $INT64))))"
                    )
                else:
                    ctx.emitter.line(
                        f"(local.set {native_local} "
                        "(struct.get $INT64 0 (ref.cast (ref $INT64))))"
                    )
    elif name in ctx.local_vars:
        compile_expr(value, ctx)
        _box_if_native(ctx)  # Box native values for boxed local
        ctx.emitter.emit_local_set(ctx.local_vars[name])
    else:
        local_name = f"$var_{name}"
        ctx.local_vars[name] = local_name
        compile_expr(value, ctx)
        _box_if_native(ctx)  # Box native values for boxed local
        ctx.emitter.emit_local_set(local_name)


def _emit_raw_f64_value(value: ast.expr, ctx: CompilerContext) -> None:
    """Emit raw f64 value on stack, avoiding boxing when possible."""
    value_type = ctx.get_expr_type(value)

    match (value, value_type):
        # Float constant
        case (ast.Constant(value=float() as val), _):
            ctx.emitter.line(f"(f64.const {val})")
        # Int constant (convert to float)
        case (ast.Constant(value=int() as val), _):
            ctx.emitter.line(f"(f64.const {float(val)})")
        # Native f64 type variable - load directly
        case (ast.Name(id=var_name), F64Type()) if var_name in ctx.native_locals:
            native_local = ctx.get_native_local_name(var_name)
            ctx.emitter.line(f"(local.get {native_local})  ;; native f64")
        # Native i32 type variable - load and convert
        case (ast.Name(id=var_name), I32Type()) if var_name in ctx.native_locals:
            native_local = ctx.get_native_local_name(var_name)
            ctx.emitter.line(
                f"(f64.convert_i32_s (local.get {native_local}))  ;; native i32 to f64"
            )
        # Native i64 type variable - load and convert
        case (ast.Name(id=var_name), I64Type()) if var_name in ctx.native_locals:
            native_local = ctx.get_native_local_name(var_name)
            ctx.emitter.line(
                f"(f64.convert_i64_s (local.get {native_local}))  ;; native i64 to f64"
            )
        # Native float variable (inferred) - load directly
        case (ast.Name(id=var_name), FloatType()) if (
            var_name in ctx.native_locals
            and ctx.native_locals[var_name] == NativeType.F64
        ):
            native_local = ctx.get_native_local_name(var_name)
            ctx.emitter.line(f"(local.get {native_local})  ;; native f64")
        # Native int variable (inferred) - load and convert
        case (ast.Name(id=var_name), IntType()) if (
            var_name in ctx.native_locals
            and ctx.native_locals[var_name] == NativeType.I32
        ):
            native_local = ctx.get_native_local_name(var_name)
            ctx.emitter.line(
                f"(f64.convert_i32_s (local.get {native_local}))  ;; native i32 to f64"
            )
        # BinOp producing native f64 - emit native binop
        case (ast.BinOp(), F64Type()):
            from p2w.compiler.codegen.expr_handlers import (  # noqa: PLC0415
                _compile_native_binop,
            )

            _compile_native_binop(
                value,
                ctx.get_expr_type(value.left),
                ctx.get_expr_type(value.right),
                ctx,
            )
            ctx.clear_native_value()
        # BinOp producing float - recursively emit raw
        case (ast.BinOp() as binop, FloatType()):
            # Late import to avoid circular import
            from p2w.compiler.codegen.expr_handlers import (  # noqa: PLC0415
                _compile_float_binop_raw,
            )

            _compile_float_binop_raw(binop, ctx)
        # Float expression - compile and unbox if needed
        case (_, FloatType()):
            compile_expr(value, ctx)
            if ctx.has_native_value:
                ctx.clear_native_value()
            else:
                ctx.emitter.line(
                    "(struct.get $FLOAT 0 (ref.cast (ref $FLOAT)))  ;; unbox float"
                )
        # Int expression - compile and convert
        case (_, IntType()):
            compile_expr(value, ctx)
            if ctx.has_native_value:
                # Native i32, just convert to f64
                ctx.emitter.line("f64.convert_i32_s  ;; native i32 to f64")
                ctx.clear_native_value()
            else:
                ctx.emitter.line(
                    "(f64.convert_i32_s (i31.get_s (ref.cast (ref i31))))  ;; int to f64"
                )
        # Unknown type - assume float since we're assigning to f64
        # (user annotated with : float, so they expect a float value)
        case _:
            compile_expr(value, ctx)
            if ctx.has_native_value:
                ctx.clear_native_value()
            else:
                ctx.emitter.line(
                    "(struct.get $FLOAT 0 (ref.cast (ref $FLOAT)))  ;; unbox float (unknown type)"
                )


def _emit_raw_i32_value(value: ast.expr, ctx: CompilerContext) -> None:
    """Emit raw i32 value on stack, avoiding boxing when possible."""
    value_type = ctx.get_expr_type(value)

    match (value, value_type):
        # Int constant
        case (ast.Constant(value=int() as val), _):
            ctx.emitter.line(f"(i32.const {val})")
        # Native i32 type variable - load directly
        case (ast.Name(id=var_name), I32Type()) if var_name in ctx.native_locals:
            native_local = ctx.get_native_local_name(var_name)
            ctx.emitter.line(f"(local.get {native_local})  ;; native i32")
        # Native i64 type variable - load and truncate
        case (ast.Name(id=var_name), I64Type()) if var_name in ctx.native_locals:
            native_local = ctx.get_native_local_name(var_name)
            ctx.emitter.line(
                f"(i32.wrap_i64 (local.get {native_local}))  ;; native i64 to i32"
            )
        # Native int variable (inferred) - load directly
        case (ast.Name(id=var_name), IntType()) if (
            var_name in ctx.native_locals
            and ctx.native_locals[var_name] == NativeType.I32
        ):
            native_local = ctx.get_native_local_name(var_name)
            ctx.emitter.line(f"(local.get {native_local})  ;; native i32")
        # BinOp producing native i32 - emit native binop
        case (ast.BinOp(), I32Type()):
            from p2w.compiler.codegen.expr_handlers import (  # noqa: PLC0415
                _compile_native_binop,
            )

            _compile_native_binop(
                value,
                ctx.get_expr_type(value.left),
                ctx.get_expr_type(value.right),
                ctx,
            )
            ctx.clear_native_value()
        # Int expression - compile and unbox if needed
        case _:
            compile_expr(value, ctx)
            # Only unbox if not already a native value
            if ctx.has_native_value:
                ctx.clear_native_value()
            else:
                ctx.emitter.line("(i31.get_s (ref.cast (ref i31)))  ;; unbox i31")


def compile_nonlocal_assignment(
    name: str, value: ast.expr, ctx: CompilerContext
) -> None:
    """Emit assignment to a nonlocal variable."""

    try:
        depth, slot = ctx.lexical_env.lookup(name)
    except NameError:
        msg = f"Nonlocal variable '{name}' not found in enclosing scope"
        raise NameError(msg) from None

    ctx.emitter.comment(f"assign nonlocal '{name}'")

    ctx.emitter.emit_local_get("$env")
    for _ in range(depth):
        ctx.emitter.line("(struct.get $ENV 0)  ;; parent")
    ctx.emitter.line("(struct.get $ENV 1)  ;; values")
    for _ in range(slot):
        ctx.emitter.line("(struct.get $PAIR 1 (ref.cast (ref $PAIR)))  ;; cdr")
    ctx.emitter.line("(struct.get $PAIR 0 (ref.cast (ref $PAIR)))  ;; car (cell)")

    ctx.emitter.line("(ref.cast (ref $PAIR))  ;; cell ref")
    compile_expr(value, ctx)
    _box_if_native(ctx)  # Box native values for nonlocal

    ctx.emitter.line("(struct.set $PAIR 0)  ;; update cell value")


def compile_aug_assignment(
    name: str, op: ast.operator, value: ast.expr, ctx: CompilerContext
) -> None:
    """Emit augmented assignment (+=, -=, etc.)."""
    new_value = ast.BinOp(
        left=ast.Name(id=name, ctx=ast.Load()),
        op=op,
        right=value,
    )
    compile_assignment(name, new_value, ctx)
