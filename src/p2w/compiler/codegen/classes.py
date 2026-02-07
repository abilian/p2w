"""Class compilation."""

from __future__ import annotations

import ast
from io import StringIO
from typing import TYPE_CHECKING

from p2w.compiler.analysis import (
    collect_comprehension_locals,
    collect_iter_locals,
    collect_local_vars,
    collect_with_locals,
    has_try_except,
    has_try_finally,
)
from p2w.compiler.builtins import BUILTINS
from p2w.compiler.codegen.expressions import compile_expr
from p2w.compiler.codegen.statements import compile_stmt

if TYPE_CHECKING:
    from p2w.compiler.context import CompilerContext


def _get_method_decorator_info(
    stmt: ast.FunctionDef,
) -> tuple[str | None, str | None]:
    """Extract decorator type and property name from a method.

    Returns:
        (decorator_type, property_name) where decorator_type is one of
        "staticmethod", "classmethod", "property", "setter", "deleter", or None.
        property_name is set for setter/deleter to indicate which property they belong to.
    """
    decorator_type = None
    property_name = None
    for dec in stmt.decorator_list:
        match dec:
            case ast.Name(id=name) if name in {
                "staticmethod",
                "classmethod",
                "property",
            }:
                decorator_type = name
            case ast.Attribute(value=ast.Name(id=prop_name), attr=attr) if attr in {
                "setter",
                "deleter",
            }:
                # @name.setter or @name.deleter
                property_name = prop_name
                decorator_type = attr
    return decorator_type, property_name


def compile_class_def(
    name: str,
    bases: list[ast.expr],
    body: list[ast.stmt],
    ctx: CompilerContext,
) -> None:
    """Compile class definition."""
    ctx.emitter.comment(f"class {name}")

    # Collect methods and class attributes
    # methods list: (name, FunctionDef, decorator_type, property_name)
    # decorator_type is "staticmethod", "classmethod", "property", "setter", "deleter", or None
    # property_name is set for setter/deleter to indicate which property they belong to
    methods: list[tuple[str, ast.FunctionDef, str | None, str | None]] = []
    class_attrs: list[tuple[str, ast.expr]] = []
    for stmt in body:
        match stmt:
            case ast.FunctionDef():
                decorator_type, property_name = _get_method_decorator_info(stmt)
                methods.append((stmt.name, stmt, decorator_type, property_name))

            case ast.Assign(targets=targets, value=value):
                # Class-level attribute assignment: x = value
                for target in targets:
                    match target:
                        case ast.Name(id=attr_name):
                            class_attrs.append((attr_name, value))

            case ast.AnnAssign(target=ast.Name() as target, value=value) if (
                value is not None
            ):
                # Annotated assignment: x: int = value
                class_attrs.append((target.id, value))

            case ast.Pass() | ast.Expr(value=ast.Constant()):
                pass

            case _:
                msg = f"Class body element not supported: {type(stmt).__name__}"
                raise NotImplementedError(msg)

    # Pre-declare the class name so methods can reference it (e.g., Counter.count)
    # Treat class names as globals so they're accessible from method bodies
    ctx.global_vars.add(name)
    if name not in ctx.local_vars:
        local_wasm_name = f"$var_{name}"
        ctx.local_vars[name] = local_wasm_name

    # Emit each method
    # method_indices: (name, func_idx, decorator_type, property_name)
    method_indices: list[tuple[str, int, str | None, str | None]] = []
    saved_current_class = ctx.current_class
    ctx.current_class = name  # Track class for super(Class, self) support

    for method_name, method_def, decorator_type, property_name in methods:
        saved_stream = ctx.emitter.stream
        saved_indent = ctx.emitter.indent
        saved_locals = ctx.local_vars

        ctx.emitter.stream = StringIO()
        ctx.emitter.indent = 0
        ctx.local_vars = {}
        func_idx = len(ctx.user_funcs)
        ctx.user_funcs.append(ctx.emitter.stream)

        method_indices.append((method_name, func_idx, decorator_type, property_name))

        ctx.emitter.line(
            f"(func $user_func_{func_idx} "
            "(param $args (ref null eq)) (param $env (ref null $ENV)) "
            "(result (ref null eq))"
        )
        ctx.emitter.indent += 2

        ctx.emitter.line("(local $tmp (ref null eq))")
        ctx.emitter.line("(local $tmp2 (ref null eq))")
        ctx.emitter.line("(local $chain_val (ref null eq))")
        # Locals for direct array iteration optimization
        ctx.emitter.line("(local $iter_source (ref null eq))")
        ctx.emitter.line("(local $list_ref (ref null $LIST))")
        ctx.emitter.line("(local $tuple_ref (ref null $TUPLE))")
        ctx.emitter.line("(local $iter_len i32)")
        ctx.emitter.line("(local $iter_idx i32)")
        # Locals for inline list access optimization
        ctx.emitter.line("(local $subscript_list_ref (ref null $LIST))")
        ctx.emitter.line(
            "(local $subscript_list_ref2 (ref null $LIST))"
        )  # For nested access
        ctx.emitter.line("(local $idx_tmp i32)")
        ctx.emitter.line("(local $len_tmp i32)")

        param_names = [arg.arg for arg in method_def.args.args]
        local_names = collect_local_vars(method_def.body) - set(param_names)
        iter_locals = collect_iter_locals(method_def.body)
        comp_locals, _ = collect_comprehension_locals(method_def.body)

        for param_name in param_names:
            local_wasm_name = f"$var_{param_name}"
            ctx.local_vars[param_name] = local_wasm_name
            ctx.emitter.line(f"(local {local_wasm_name} (ref null eq))")

        for local_name in sorted(local_names):
            local_wasm_name = f"$var_{local_name}"
            ctx.local_vars[local_name] = local_wasm_name
            ctx.emitter.line(f"(local {local_wasm_name} (ref null eq))")

        for iter_local in sorted(iter_locals):
            ctx.emitter.line(f"(local {iter_local} (ref null eq))")

        for comp_local in sorted(comp_locals):
            ctx.emitter.line(f"(local {comp_local} (ref null eq))")

        # Declare locals for with statements
        with_locals = collect_with_locals(method_def.body)
        for with_local in sorted(with_locals):
            ctx.emitter.line(f"(local {with_local} (ref null eq))")

        # Declare $exc local if there are try/except statements
        if has_try_except(method_def.body):
            ctx.emitter.line("(local $exc (ref null $EXCEPTION))")

        # Declare $exnref local if there are try/finally statements
        if has_try_finally(method_def.body):
            ctx.emitter.line("(local $exnref exnref)")

        ctx.lexical_env.push_frame(param_names)

        # For slotted classes, register 'self' as a slotted instance
        # so attribute access uses struct.get/set instead of hash table
        saved_slotted_instances = ctx.slotted_instances.copy()
        if name in ctx.slotted_classes and param_names and param_names[0] == "self":
            ctx.register_slotted_instance("self", name)

        ctx.emitter.comment("method prologue")
        ctx.emitter.line(
            "(local.set $env (struct.new $ENV (local.get $env) (local.get $args)))"
        )

        ctx.emitter.comment("extract self and params from args")
        ctx.emitter.line("(local.set $tmp (local.get $args))")
        for i, param_name in enumerate(param_names):
            if i > 0:
                ctx.emitter.line(
                    "(local.set $tmp (struct.get $PAIR 1 "
                    "(ref.cast (ref $PAIR) (local.get $tmp))))"
                )
            ctx.emitter.line(
                f"(local.set {ctx.local_vars[param_name]} "
                "(struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $tmp))))"
            )

        for stmt in method_def.body:
            compile_stmt(stmt, ctx)

        ctx.emitter.emit_null_eq()

        ctx.lexical_env.pop_frame()
        ctx.slotted_instances = saved_slotted_instances  # Restore

        ctx.emitter.indent -= 2
        ctx.emitter.line(")")

        ctx.emitter.stream = saved_stream
        ctx.emitter.indent = saved_indent
        ctx.local_vars = saved_locals

    ctx.current_class = saved_current_class  # Restore after compiling methods

    # Build method dictionary (includes both methods and class attributes)
    ctx.emitter.comment(f"build class {name}")

    # Collect properties and their getter/setter/deleter indices
    # property_info: {prop_name: {"getter": func_idx, "setter": func_idx, "deleter": func_idx}}
    property_info: dict[str, dict[str, int]] = {}
    for method_name, func_idx, decorator_type, property_name in method_indices:
        if decorator_type == "property":
            if method_name not in property_info:
                property_info[method_name] = {}
            property_info[method_name]["getter"] = func_idx
        elif decorator_type == "setter" and property_name:
            if property_name not in property_info:
                property_info[property_name] = {}
            property_info[property_name]["setter"] = func_idx
        elif decorator_type == "deleter" and property_name:
            if property_name not in property_info:
                property_info[property_name] = {}
            property_info[property_name]["deleter"] = func_idx

    # Track which methods are part of properties (to skip them in regular method emission)
    property_methods: set[str] = set()
    property_methods.update(property_info)

    # Add regular methods (excluding properties)
    for method_name, func_idx, decorator_type, property_name in method_indices:
        # Skip property-related methods
        if decorator_type in {"property", "setter", "deleter"}:
            continue

        ctx.emitter.emit_string(method_name)
        table_idx = len(BUILTINS) + func_idx
        if decorator_type == "staticmethod":
            # STATICMETHOD: (closure, padding) - closure is field 0
            ctx.emitter.line(
                f"(struct.new $CLOSURE (ref.null $ENV) (i32.const {table_idx}))"
            )
            ctx.emitter.line("(i32.const 0)  ;; padding")
            ctx.emitter.line("(struct.new $STATICMETHOD)  ;; wrap as staticmethod")
        elif decorator_type == "classmethod":
            # CLASSMETHOD: (padding, closure) - closure is field 1
            ctx.emitter.line("(i32.const 0)  ;; padding")
            ctx.emitter.line(
                f"(struct.new $CLOSURE (ref.null $ENV) (i32.const {table_idx}))"
            )
            ctx.emitter.line("(struct.new $CLASSMETHOD)  ;; wrap as classmethod")
        else:
            ctx.emitter.line(
                f"(struct.new $CLOSURE (ref.null $ENV) (i32.const {table_idx}))"
            )
        ctx.emitter.line("(struct.new $PAIR)  ;; method name-closure pair")

    # Add properties
    for prop_name, info in property_info.items():
        ctx.emitter.emit_string(prop_name)
        # PROPERTY: (getter, setter, deleter)
        if "getter" in info:
            table_idx = len(BUILTINS) + info["getter"]
            ctx.emitter.line(
                f"(struct.new $CLOSURE (ref.null $ENV) (i32.const {table_idx}))  "
                ";; property getter"
            )
        else:
            ctx.emitter.line("(ref.null $CLOSURE)  ;; no getter")
        if "setter" in info:
            table_idx = len(BUILTINS) + info["setter"]
            ctx.emitter.line(
                f"(struct.new $CLOSURE (ref.null $ENV) (i32.const {table_idx}))  "
                ";; property setter"
            )
        else:
            ctx.emitter.line("(ref.null $CLOSURE)  ;; no setter")
        if "deleter" in info:
            table_idx = len(BUILTINS) + info["deleter"]
            ctx.emitter.line(
                f"(struct.new $CLOSURE (ref.null $ENV) (i32.const {table_idx}))  "
                ";; property deleter"
            )
        else:
            ctx.emitter.line("(ref.null $CLOSURE)  ;; no deleter")
        ctx.emitter.line("(struct.new $PROPERTY)  ;; wrap as property")
        ctx.emitter.line("(struct.new $PAIR)  ;; property name-descriptor pair")

    # Add class attributes
    for attr_name, attr_value in class_attrs:
        ctx.emitter.emit_string(attr_name)
        compile_expr(attr_value, ctx)
        ctx.emitter.line("(struct.new $PAIR)  ;; class attr name-value pair")

    ctx.emitter.line("(ref.null eq)  ;; methods dict terminator")
    # Count regular methods (excluding property-related ones)
    regular_method_count = sum(
        1
        for _, _, dt, _ in method_indices
        if dt not in {"property", "setter", "deleter"}
    )
    for _ in range(regular_method_count):
        ctx.emitter.line("(struct.new $PAIR)  ;; methods dict entry")
    # Count properties
    for _ in property_info:
        ctx.emitter.line("(struct.new $PAIR)  ;; property entry")
    for _ in class_attrs:
        ctx.emitter.line("(struct.new $PAIR)  ;; class attr entry")

    ctx.emitter.line("(local.set $tmp)  ;; save methods dict")
    ctx.emitter.emit_string(name)
    ctx.emitter.line("(local.get $tmp)  ;; methods dict")
    # Handle base class
    if bases and len(bases) > 0:
        base = bases[0]
        # Check if base is Exception or BaseException (special case for exception classes)
        match base:
            case ast.Name(id=base_name) if base_name in {"Exception", "BaseException"}:
                # Exception classes use null base - they are $EXCEPTION structs, not $OBJECT
                ctx.emitter.line(
                    "(ref.null $CLASS)  ;; exception base class (handled specially)"
                )
            case _:
                compile_expr(base, ctx)
                ctx.emitter.line("(ref.cast (ref null $CLASS))  ;; base class")
    else:
        ctx.emitter.line("(ref.null $CLASS)  ;; no base class")
    ctx.emitter.line(f"(struct.new $CLASS)  ;; class {name}")

    # Store to local variable
    if name in ctx.local_vars:
        ctx.emitter.emit_local_tee(ctx.local_vars[name])
    else:
        local_wasm_name = f"$var_{name}"
        ctx.local_vars[name] = local_wasm_name
        ctx.emitter.emit_local_tee(local_wasm_name)

    # Also store to global so methods can access the class by name
    if name in ctx.global_vars:
        ctx.emitter.emit_global_set(f"$global_{name}")
