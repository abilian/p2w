"""Statement compilation handlers.

This module registers all handlers for compile_stmt.
Import this module to activate the handlers.
"""

from __future__ import annotations

import ast
from typing import Final

# Import handlers from new modules to register them
import p2w.compiler.codegen.context_managers  # noqa: F401
import p2w.compiler.codegen.exceptions  # noqa: F401
import p2w.compiler.codegen.pattern_matching  # noqa: F401
from p2w.compiler.codegen.attributes import (
    compile_attribute_assignment,
    compile_attribute_aug_assignment,
)
from p2w.compiler.codegen.classes import compile_class_def
from p2w.compiler.codegen.control import (
    compile_for_stmt,
    compile_for_tuple_stmt,
    compile_if_stmt,
    compile_while_stmt,
)
from p2w.compiler.codegen.expressions import compile_expr
from p2w.compiler.codegen.functions import compile_function_def
from p2w.compiler.codegen.statements import compile_stmt
from p2w.compiler.codegen.subscript import (
    compile_subscript_assignment,
    compile_subscript_delete,
)
from p2w.compiler.codegen.unpacking import compile_tuple_unpack
from p2w.compiler.codegen.variables import compile_assignment, compile_aug_assignment
from p2w.compiler.context import CompilerContext  # noqa: TC001
from p2w.compiler.types import NativeType

# Methods that mutate and return the modified collection
# Note: setdefault is handled specially in calls.py (multi-value return)
_MUTATING_METHODS: Final[set[str]] = {
    "add",
    "remove",
    "discard",  # set methods
    "append",
    "extend",
    "insert",
    "pop",
    "clear",  # list methods
    "update",  # dict methods
}


@compile_stmt.register
def _expr(node: ast.Expr, ctx: CompilerContext) -> None:
    """Compile expression statement."""
    expr = node.value

    # Check for mutating method calls
    match expr:
        case ast.Call(func=ast.Attribute(value=ast.Name(id=var_name), attr=attr)) if (
            attr in _MUTATING_METHODS and var_name in ctx.local_vars
        ):
            compile_expr(expr, ctx)
            # For module-level variables, update both local and global
            if var_name in ctx.global_vars and len(ctx.lexical_env.frames) <= 1:
                ctx.emitter.emit_local_tee(ctx.local_vars[var_name])
                ctx.emitter.line(f"(global.set $global_{var_name})")
            else:
                ctx.emitter.emit_local_set(ctx.local_vars[var_name])
        case _:
            compile_expr(expr, ctx)
            ctx.emitter.emit_drop()


@compile_stmt.register
def _assign(node: ast.Assign, ctx: CompilerContext) -> None:
    """Compile assignment statement."""
    targets = node.targets
    value = node.value

    # Single target assignment
    if len(targets) == 1:
        match targets[0]:
            case ast.Name(id=name):
                compile_assignment(name, value, ctx)
            case ast.Tuple() | ast.List():
                compile_tuple_unpack(targets[0], value, ctx)
            case ast.Subscript():
                compile_subscript_assignment(targets[0], value, ctx)
            case ast.Attribute():
                compile_attribute_assignment(targets[0], value, ctx)
        return

    # Chained assignment: a = b = c = value
    # Use $chain_val to avoid conflicts with $tmp used in subscript compilation
    ctx.emitter.comment("chained assignment")
    compile_expr(value, ctx)
    ctx.emitter.emit_local_set("$chain_val")

    for target in targets:
        ctx.emitter.emit_local_get("$chain_val")
        match target:
            case ast.Name(id=name):
                # For module-level variables, update both local and global
                if (
                    name in ctx.local_vars
                    and name in ctx.global_vars
                    and len(ctx.lexical_env.frames) <= 1
                ):
                    ctx.emitter.emit_local_tee(ctx.local_vars[name])
                    ctx.emitter.line(f"(global.set $global_{name})")
                elif name in ctx.local_vars:
                    ctx.emitter.emit_local_set(ctx.local_vars[name])
                elif name in ctx.global_vars:
                    ctx.emitter.line(f"(global.set $global_{name})")
                else:
                    msg = f"Variable '{name}' not declared"
                    raise NameError(msg)
            case ast.Subscript(value=container, slice=slice_expr):
                # Subscript assignment: arr[idx] = value
                ctx.emitter.emit_local_set("$tmp2")  # Save value
                compile_expr(container, ctx)  # Container
                compile_expr(slice_expr, ctx)  # Index
                ctx.emitter.emit_local_get("$tmp2")  # Value
                ctx.emitter.emit_call("$container_set")
                # Update container variable with returned (possibly new) container
                # For module-level variables (in both local and global), update both
                match container:
                    case ast.Name(id=var_name) if (
                        var_name in ctx.local_vars
                        and var_name in ctx.global_vars
                        and len(ctx.lexical_env.frames) <= 1
                    ):
                        # Module-level variable: update both local and global
                        ctx.emitter.emit_local_tee(ctx.local_vars[var_name])
                        ctx.emitter.line(f"(global.set $global_{var_name})")
                    case ast.Name(id=var_name) if var_name in ctx.local_vars:
                        ctx.emitter.emit_local_set(ctx.local_vars[var_name])
                    case ast.Name(id=var_name) if var_name in ctx.global_vars:
                        ctx.emitter.line(f"(global.set $global_{var_name})")
                    case _:
                        ctx.emitter.emit_drop()
            case ast.Attribute(value=obj, attr=attr):
                # Attribute assignment: obj.attr = value
                ctx.emitter.emit_local_set("$tmp2")  # Save value
                compile_expr(obj, ctx)  # Object
                ctx.emitter.emit_string(attr)
                ctx.emitter.emit_local_get("$tmp2")  # Value
                ctx.emitter.emit_call("$object_setattr")
                ctx.emitter.emit_drop()
            case _:
                msg = f"Assignment target not implemented: {type(target).__name__}"
                raise NotImplementedError(msg)


@compile_stmt.register
def _augassign(node: ast.AugAssign, ctx: CompilerContext) -> None:
    """Compile augmented assignment."""
    match node.target:
        case ast.Name(id=name):
            compile_aug_assignment(name, node.op, node.value, ctx)
        case ast.Attribute() as attr:
            compile_attribute_aug_assignment(attr, node.op, node.value, ctx)
        case _:
            msg = f"Aug assignment target not supported: {type(node.target).__name__}"
            raise NotImplementedError(msg)


@compile_stmt.register
def _annassign(node: ast.AnnAssign, ctx: CompilerContext) -> None:
    """Compile annotated assignment."""
    # Track slotted class type annotations
    match (node.target, node.annotation):
        case (ast.Name(id=var_name), ast.Name(id=class_name)) if (
            class_name in ctx.slotted_classes
        ):
            is_global = var_name in ctx.global_vars
            ctx.register_slotted_instance(var_name, class_name, is_global=is_global)

    match (node.target, node.value):
        case (ast.Name(id=name), value) if value is not None:
            compile_assignment(name, value, ctx)
        case (ast.Attribute() as attr, value) if value is not None:
            # Annotated attribute assignment: obj.attr: type = value
            compile_attribute_assignment(attr, value, ctx)


@compile_stmt.register
def _if(node: ast.If, ctx: CompilerContext) -> None:
    """Compile if statement."""
    compile_if_stmt(node.test, node.body, node.orelse, ctx)


@compile_stmt.register
def _while(node: ast.While, ctx: CompilerContext) -> None:
    """Compile while statement."""
    compile_while_stmt(node.test, node.body, ctx)


@compile_stmt.register
def _for(node: ast.For, ctx: CompilerContext) -> None:
    """Compile for statement."""
    match node.target:
        case ast.Name(id=name):
            compile_for_stmt(name, node.iter, node.body, node.orelse, ctx)
        case ast.Tuple(elts=targets) | ast.List(elts=targets):
            compile_for_tuple_stmt(targets, node.iter, node.body, node.orelse, ctx)
        case _:
            msg = f"Loop variable type not supported: {type(node.target).__name__}"
            raise NotImplementedError(msg)


@compile_stmt.register
def _break(node: ast.Break, ctx: CompilerContext) -> None:
    """Compile break statement."""
    ctx.emitter.emit_br("$break")


@compile_stmt.register
def _continue(node: ast.Continue, ctx: CompilerContext) -> None:
    """Compile continue statement."""
    ctx.emitter.emit_br("$continue")


@compile_stmt.register
def _functiondef(node: ast.FunctionDef, ctx: CompilerContext) -> None:
    """Compile function definition, including decorator application."""
    # First compile the function itself
    # Pass has_decorators=True if there are decorators, to prevent direct call registration
    has_decorators = bool(node.decorator_list)
    compile_function_def(
        node.name, node.args, node.body, ctx, node.returns, has_decorators
    )

    # If there are decorators, apply them in reverse order
    # @dec1 @dec2 def f(): ... becomes f = dec1(dec2(f))
    if node.decorator_list:
        ctx.emitter.comment(f"apply decorators to '{node.name}'")
        # Get the function value to start the chain
        ctx.emitter.emit_local_get(ctx.local_vars[node.name])
        # Apply each decorator (from bottom to top means we iterate in reverse)
        for decorator in reversed(node.decorator_list):
            # Current function value is on stack
            # Wrap it in args list: (func, null) -> PAIR
            ctx.emitter.emit_null_eq()  # terminator for args list
            ctx.emitter.emit_struct_new("$PAIR")  # wrap function in args list
            # Store args temporarily
            ctx.emitter.line("(local.set $tmp)")
            # call_or_instantiate(callable, init_name, args, env)
            compile_expr(decorator, ctx)  # callable
            ctx.emitter.emit_null_eq()  # init_name (null for functions)
            ctx.emitter.line("(local.get $tmp)")  # args
            ctx.emitter.line("(ref.null $ENV)")  # env override
            ctx.emitter.emit_call("$call_or_instantiate")
            # Result is the decorated function, leave it on stack for next decorator
        # Store the fully decorated function back
        ctx.emitter.emit_local_set(ctx.local_vars[node.name])
        # Also update global if it's a module-level function
        if node.name in ctx.global_vars:
            ctx.emitter.emit_local_get(ctx.local_vars[node.name])
            ctx.emitter.emit_global_set(f"$global_{node.name}")


@compile_stmt.register
def _classdef(node: ast.ClassDef, ctx: CompilerContext) -> None:
    """Compile class definition."""
    compile_class_def(node.name, node.bases, node.body, ctx)


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


@compile_stmt.register
def _return(node: ast.Return, ctx: CompilerContext) -> None:
    """Compile return statement."""
    if node.value:
        compile_expr(node.value, ctx)
        # Box native values - function returns (ref null eq)
        _box_if_native(ctx)
    else:
        ctx.emitter.emit_null_eq()
    ctx.emitter.emit_return()


@compile_stmt.register
def _pass(node: ast.Pass, ctx: CompilerContext) -> None:
    """Compile pass statement (no-op)."""


@compile_stmt.register
def _global(node: ast.Global, ctx: CompilerContext) -> None:
    """Compile global declaration (declarative only)."""


@compile_stmt.register
def _nonlocal(node: ast.Nonlocal, ctx: CompilerContext) -> None:
    """Compile nonlocal declaration (declarative only)."""


@compile_stmt.register
def _importfrom(node: ast.ImportFrom, ctx: CompilerContext) -> None:
    """Compile import from statement."""
    if node.module == "__future__":
        pass  # Ignore __future__ imports
    else:
        msg = f"Import not supported: {node.module}"
        raise NotImplementedError(msg)


@compile_stmt.register
def _import(node: ast.Import, ctx: CompilerContext) -> None:
    """Compile import statement."""
    for alias in node.names:
        if alias.name == "js":
            # Special handling for JavaScript interop module
            ctx.js_imported = True
            ctx.emitter.comment("import js (JavaScript interop enabled)")
        else:
            msg = f"Import not supported: {alias.name}"
            raise NotImplementedError(msg)


@compile_stmt.register
def _assert(node: ast.Assert, ctx: CompilerContext) -> None:
    """Compile assert statement - raises AssertionError if condition is false."""
    ctx.emitter.comment("assert statement")

    # Evaluate the condition
    compile_expr(node.test, ctx)
    ctx.emitter.emit_call("$is_false")

    # If false, raise AssertionError
    ctx.emitter.emit_if_start()

    # Create AssertionError exception
    ctx.emitter.comment("raise AssertionError")

    # Get the message (or None)
    if node.msg:
        compile_expr(node.msg, ctx)
    else:
        ctx.emitter.emit_null_eq()

    # Create and throw exception
    ctx.emitter.emit_call("$make_assertion_error")
    ctx.emitter.emit_throw()

    ctx.emitter.emit_if_end()


@compile_stmt.register
def _delete(node: ast.Delete, ctx: CompilerContext) -> None:
    """Compile delete statement."""
    for target in node.targets:
        match target:
            case ast.Subscript(value=container):
                # del obj[key] or del obj[slice]
                compile_subscript_delete(target, ctx)
                # Update the variable if it's a simple name
                match container:
                    case ast.Name(id=name) if name in ctx.local_vars:
                        ctx.emitter.emit_local_set(ctx.local_vars[name])
                    case _:
                        ctx.emitter.emit_drop()
            case ast.Attribute(value=obj, attr=attr):
                # del obj.attr - call deleter if property, or delete instance attr
                ctx.emitter.comment(f"del {obj}.{attr}")
                compile_expr(obj, ctx)
                ctx.emitter.emit_string(attr)
                ctx.emitter.emit_call("$object_delattr")
                ctx.emitter.emit_drop()
            case ast.Name(id=name):
                # del x - set to null
                ctx.emitter.comment(f"del {name}")
                if name in ctx.local_vars:
                    ctx.emitter.emit_null_eq()
                    ctx.emitter.emit_local_set(ctx.local_vars[name])
                else:
                    msg = f"Cannot delete undefined variable: {name}"
                    raise NameError(msg)
            case _:
                msg = f"Delete target not implemented: {type(target).__name__}"
                raise NotImplementedError(msg)
