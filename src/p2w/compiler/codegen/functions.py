"""Function compilation."""

from __future__ import annotations

import ast
from io import StringIO
from typing import TYPE_CHECKING

from p2w.compiler.analysis import (
    collect_comprehension_locals,
    collect_global_decls,
    collect_iter_locals,
    collect_local_vars,
    collect_namedexpr_vars,
    collect_nonlocal_decls,
    collect_with_locals,
    find_free_vars_in_func,
    has_try_except,
    has_try_finally,
    is_generator_function,
)
from p2w.compiler.builtins import BUILTINS
from p2w.compiler.codegen.closures import (
    emit_captured_var,
    find_all_nested_nonlocals,
    find_nested_nonlocals,
)
from p2w.compiler.codegen.expressions import compile_expr
from p2w.compiler.codegen.generators import compile_generator_function
from p2w.compiler.codegen.statements import compile_stmt
from p2w.compiler.context import FunctionSignature
from p2w.compiler.inference import TypeInferencer
from p2w.compiler.types import NativeType

if TYPE_CHECKING:
    from p2w.compiler.context import CompilerContext

# Re-export for backwards compatibility
from p2w.compiler.codegen.closures import (  # noqa: F401
    emit_captured_var as _emit_captured_var,
    find_all_nested_nonlocals as _find_all_nested_nonlocals,
    find_nested_nonlocals as _find_nested_nonlocals,
)
from p2w.compiler.codegen.generators import (  # noqa: F401
    GeneratorContext,
    collect_yieldfrom_iter_locals as _collect_yieldfrom_iter_locals,
    compile_generator_function as _compile_generator_function,
    transform_yield_from as _transform_yield_from,
)
from p2w.compiler.codegen.lambdas import compile_lambda  # noqa: F401


def _compile_specialized_function(
    name: str,
    args: ast.arguments,
    body: list[ast.stmt],
    ctx: CompilerContext,
    orig_func_idx: int,
    arity: int,
    nested_nonlocals: set[str],
    returns: ast.expr | None = None,
) -> None:
    """Compile a specialized version of function with direct parameters.

    This is Phase 4.1 optimization - bypasses PAIR chain for function arguments.
    The specialized function takes parameters directly on the stack instead of
    unpacking from a PAIR chain.

    Args:
        name: Function name
        args: Function arguments
        body: Function body statements
        ctx: Compiler context
        orig_func_idx: Original function's index in user_funcs
        arity: Number of parameters
        nested_nonlocals: Variables accessed by nested functions
        returns: Return type annotation (if any)
    """
    # Skip functions with nested functions that use nonlocal/global
    # These require complex environment handling
    if nested_nonlocals:
        return

    # Also skip if body has nested functions (to keep things simple)
    for stmt in body:
        match stmt:
            case ast.FunctionDef():
                return

    param_names = [arg.arg for arg in args.args]

    # Save current state
    saved_stream = ctx.emitter.stream
    saved_indent = ctx.emitter.indent
    saved_locals = ctx.local_vars
    saved_inferencer = ctx.type_inferencer
    saved_native_locals = ctx.native_locals
    saved_global_decls = ctx.current_global_decls
    saved_nonlocal_decls = ctx.current_nonlocal_decls
    saved_cell_vars = ctx.cell_vars

    # Create type inferencer for this function
    inferencer = TypeInferencer()
    if saved_inferencer:
        inferencer.func_return_types = saved_inferencer.func_return_types.copy()
    func_node = ast.FunctionDef(
        name=name,
        args=args,
        body=body,
        decorator_list=[],
        returns=returns,
        type_comment=None,
        type_params=[],
    )
    inferencer.analyze_function(func_node)
    ctx.type_inferencer = inferencer
    ctx.native_locals = inferencer.native_vars.copy()

    # Set up global declarations for the specialized function
    # This is needed for global variable access to work correctly
    global_decls = collect_global_decls(body)
    ctx.current_global_decls = global_decls
    ctx.current_nonlocal_decls = set()
    ctx.cell_vars = set()

    # Create new specialized function (not in the function table)
    ctx.emitter.stream = StringIO()
    ctx.emitter.indent = 0
    ctx.local_vars = {}
    len(ctx.spec_func_code)
    ctx.spec_func_code.append(ctx.emitter.stream)

    spec_func_name = f"$spec_{name}"

    # Build parameter declarations
    param_decls = " ".join(f"(param $p{i} (ref null eq))" for i in range(arity))
    ctx.emitter.line(
        f"(func {spec_func_name} {param_decls} "
        "(param $env (ref null $ENV)) (result (ref null eq))"
    )
    ctx.emitter.indent += 2

    # Standard temporary locals
    ctx.emitter.line("(local $tmp (ref null eq))")
    ctx.emitter.line("(local $tmp2 (ref null eq))")
    ctx.emitter.line("(local $chain_val (ref null eq))")
    ctx.emitter.line("(local $ftmp1 f64)")
    ctx.emitter.line("(local $ftmp2 f64)")
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

    # Parameter locals
    ctx.lexical_env.push_frame(param_names)

    for param_name in param_names:
        local_wasm_name = f"$var_{param_name}"
        ctx.local_vars[param_name] = local_wasm_name
        ctx.emitter.line(f"(local {local_wasm_name} (ref null eq))")

    # Other locals (same as original function)
    local_names = collect_local_vars(body) - set(param_names)
    for var_name in sorted(local_names):
        local_wasm_name = f"$var_{var_name}"
        ctx.local_vars[var_name] = local_wasm_name
        ctx.emitter.line(f"(local {local_wasm_name} (ref null eq))")

    iter_locals = collect_iter_locals(body)
    for iter_local in sorted(iter_locals):
        ctx.emitter.line(f"(local {iter_local} (ref null eq))")

    comp_locals, _ = collect_comprehension_locals(body)
    for comp_local in sorted(comp_locals):
        ctx.emitter.line(f"(local {comp_local} (ref null eq))")

    with_locals = collect_with_locals(body)
    for with_local in sorted(with_locals):
        ctx.emitter.line(f"(local {with_local} (ref null eq))")

    namedexpr_vars = collect_namedexpr_vars(body)
    for var_name in sorted(namedexpr_vars):
        if var_name not in ctx.local_vars:
            local_wasm_name = f"$var_{var_name}"
            ctx.local_vars[var_name] = local_wasm_name
            ctx.emitter.line(f"(local {local_wasm_name} (ref null eq))")

    if has_try_except(body):
        ctx.emitter.line("(local $exc (ref null $EXCEPTION))")

    if has_try_finally(body):
        ctx.emitter.line("(local $exnref exnref)")

    # Native locals
    if ctx.native_locals:
        ctx.emitter.comment("native locals (unboxed)")
        for var_name, native_type in sorted(ctx.native_locals.items()):
            native_local = ctx.get_native_local_name(var_name)
            match native_type:
                case NativeType.F64:
                    ctx.emitter.line(f"(local {native_local} f64)")
                case NativeType.I32:
                    ctx.emitter.line(f"(local {native_local} i32)")
                case NativeType.I64:
                    ctx.emitter.line(f"(local {native_local} i64)")

    # Simplified prologue: copy params directly (no PAIR unpacking!)
    ctx.emitter.comment("spec prologue: copy params directly")
    for i, param_name in enumerate(param_names):
        ctx.emitter.line(f"(local.set {ctx.local_vars[param_name]} (local.get $p{i}))")

        # Unbox to native local if applicable
        if param_name in ctx.native_locals:
            native_type = ctx.native_locals[param_name]
            native_local = ctx.get_native_local_name(param_name)
            match native_type:
                case NativeType.F64:
                    ctx.emitter.line(
                        f"(local.set {native_local} "
                        f"(struct.get $FLOAT 0 (ref.cast (ref $FLOAT) "
                        f"(local.get {ctx.local_vars[param_name]}))))"
                    )
                case NativeType.I32:
                    ctx.emitter.line(
                        f"(local.set {native_local} "
                        f"(i31.get_s (ref.cast (ref i31) "
                        f"(local.get {ctx.local_vars[param_name]}))))"
                    )
                case NativeType.I64:
                    ctx.emitter.line(
                        f"(local.set {native_local} "
                        f"(struct.get $INT64 0 (ref.cast (ref $INT64) "
                        f"(local.get {ctx.local_vars[param_name]}))))"
                    )

    # Note: Cell variable initialization is skipped because we don't generate
    # specialized versions for functions with nested functions that use
    # nonlocal variables (we return early at the top of this function)

    # Compile body (same as original)
    for stmt in body:
        compile_stmt(stmt, ctx)

    ctx.emitter.emit_null_eq()
    ctx.lexical_env.pop_frame()

    ctx.emitter.indent -= 2
    ctx.emitter.line(")")

    # Restore state
    ctx.emitter.stream = saved_stream
    ctx.emitter.indent = saved_indent
    ctx.local_vars = saved_locals
    ctx.type_inferencer = saved_inferencer
    ctx.native_locals = saved_native_locals
    ctx.current_global_decls = saved_global_decls
    ctx.current_nonlocal_decls = saved_nonlocal_decls
    ctx.cell_vars = saved_cell_vars

    # Register the specialized function
    ctx.register_spec_function(name, spec_func_name, arity)


def compile_function_def(
    name: str,
    args: ast.arguments,
    body: list[ast.stmt],
    ctx: CompilerContext,
    returns: ast.expr | None = None,
    has_decorators: bool = False,
) -> None:
    """Compile function definition.

    Args:
        name: Function name
        args: Function arguments
        body: Function body statements
        ctx: Compiler context
        returns: Return type annotation (if any)
        has_decorators: True if function has decorators (prevents direct call registration)
    """

    # Check if this is a generator function (contains yield)
    if is_generator_function(body):
        compile_generator_function(name, args, body, ctx)
        return

    # Collect global and nonlocal declarations
    global_decls = collect_global_decls(body)
    nonlocal_decls = collect_nonlocal_decls(body)

    param_names = [arg.arg for arg in args.args]
    vararg_name = args.vararg.arg if args.vararg else None
    all_local_names = collect_local_vars(body) | set(param_names)
    if vararg_name:
        all_local_names.add(vararg_name)
    nested_nonlocals = find_nested_nonlocals(body, all_local_names)

    # Record function signature for **kwargs support
    num_defaults = len(args.defaults)
    first_default_idx = len(param_names) - num_defaults
    ctx.func_signatures[name] = FunctionSignature(
        param_names=param_names,
        defaults=list(args.defaults),
        first_default_idx=first_default_idx,
    )

    # Save current state
    saved_stream = ctx.emitter.stream
    saved_indent = ctx.emitter.indent
    saved_locals = ctx.local_vars
    saved_global_decls = ctx.current_global_decls
    saved_nonlocal_decls = ctx.current_nonlocal_decls
    saved_cell_vars = ctx.cell_vars
    saved_inferencer = ctx.type_inferencer
    saved_native_locals = ctx.native_locals

    # Create type inferencer for this function
    inferencer = TypeInferencer()
    # Copy function return types from parent inferencer (module-level)
    # so we know return types of other functions when compiling calls
    if saved_inferencer:
        inferencer.func_return_types = saved_inferencer.func_return_types.copy()
    # Create temporary FunctionDef node for analysis
    func_node = ast.FunctionDef(
        name=name,
        args=args,
        body=body,
        decorator_list=[],
        returns=returns,
        type_comment=None,
        type_params=[],
    )
    inferencer.analyze_function(func_node)
    ctx.type_inferencer = inferencer

    # Copy native variable info from inferencer to context
    ctx.native_locals = inferencer.native_vars.copy()

    # Set current function's tracking
    ctx.current_global_decls = global_decls
    pass_through = find_all_nested_nonlocals(body) - all_local_names
    valid_pass_through = {
        v for v in pass_through if v in saved_cell_vars or v in saved_nonlocal_decls
    }
    ctx.current_nonlocal_decls = nonlocal_decls | valid_pass_through
    ctx.cell_vars = nested_nonlocals

    # Create new function
    ctx.emitter.stream = StringIO()
    ctx.emitter.indent = 0
    ctx.local_vars = {}
    func_idx = len(ctx.user_funcs)
    ctx.user_funcs.append(ctx.emitter.stream)

    ctx.emitter.line(
        f"(func $user_func_{func_idx} "
        "(param $args (ref null eq)) (param $env (ref null $ENV)) "
        "(result (ref null eq))"
    )
    ctx.emitter.indent += 2

    ctx.emitter.line("(local $tmp (ref null eq))")
    ctx.emitter.line("(local $tmp2 (ref null eq))")
    ctx.emitter.line("(local $chain_val (ref null eq))")
    ctx.emitter.line("(local $ftmp1 f64)")
    ctx.emitter.line("(local $ftmp2 f64)")
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

    # Determine captures
    captured_cells_from_outer = [
        v
        for v in sorted(nonlocal_decls)
        if v in saved_cell_vars or v in saved_nonlocal_decls
    ]
    nested_need = find_all_nested_nonlocals(body)
    for var in sorted(nested_need):
        if var not in all_local_names and var not in nonlocal_decls:
            if var in saved_cell_vars or var in saved_nonlocal_decls:
                if var not in captured_cells_from_outer:
                    captured_cells_from_outer.append(var)

    free_vars = find_free_vars_in_func(body, set(param_names))
    captured_for_read = [
        v
        for v in sorted(free_vars)
        if v in saved_locals and v not in nonlocal_decls and v not in saved_cell_vars
    ]
    all_captured_from_outer = captured_cells_from_outer + captured_for_read

    if all_captured_from_outer:
        ctx.lexical_env.push_frame(all_captured_from_outer)

    ctx.lexical_env.push_frame(param_names)

    # Declare locals
    for param_name in param_names:
        local_wasm_name = f"$var_{param_name}"
        ctx.local_vars[param_name] = local_wasm_name
        ctx.emitter.line(f"(local {local_wasm_name} (ref null eq))")

    # Track slotted class type annotations for parameters
    for arg in args.args:
        match arg.annotation:
            case ast.Name(id=class_name) if class_name in ctx.slotted_classes:
                ctx.register_slotted_instance(arg.arg, class_name)

    # Declare vararg local if present
    if vararg_name:
        local_wasm_name = f"$var_{vararg_name}"
        ctx.local_vars[vararg_name] = local_wasm_name
        ctx.emitter.line(f"(local {local_wasm_name} (ref null eq))")

    local_names = (
        collect_local_vars(body) - set(param_names) - global_decls - nonlocal_decls
    )
    for var_name in sorted(local_names):
        local_wasm_name = f"$var_{var_name}"
        ctx.local_vars[var_name] = local_wasm_name
        ctx.emitter.line(f"(local {local_wasm_name} (ref null eq))")

    iter_locals = collect_iter_locals(body)
    for iter_local in sorted(iter_locals):
        ctx.emitter.line(f"(local {iter_local} (ref null eq))")

    comp_locals, _ = collect_comprehension_locals(body)
    for comp_local in sorted(comp_locals):
        ctx.emitter.line(f"(local {comp_local} (ref null eq))")

    # Declare locals for with statements
    with_locals = collect_with_locals(body)
    for with_local in sorted(with_locals):
        ctx.emitter.line(f"(local {with_local} (ref null eq))")

    # Declare locals for NamedExpr (walrus operator)
    # These are created by function inlining optimization
    namedexpr_vars = collect_namedexpr_vars(body)
    for var_name in sorted(namedexpr_vars):
        if var_name not in ctx.local_vars:
            local_wasm_name = f"$var_{var_name}"
            ctx.local_vars[var_name] = local_wasm_name
            ctx.emitter.line(f"(local {local_wasm_name} (ref null eq))")

    # Declare $exc local if there are try/except statements
    if has_try_except(body):
        ctx.emitter.line("(local $exc (ref null $EXCEPTION))")

    # Declare $exnref local if there are try/finally statements
    if has_try_finally(body):
        ctx.emitter.line("(local $exnref exnref)")

    # Declare native locals for unboxed variables (f64/i32)
    if ctx.native_locals:
        ctx.emitter.comment("native locals (unboxed)")
        for var_name, native_type in sorted(ctx.native_locals.items()):
            native_local = ctx.get_native_local_name(var_name)
            match native_type:
                case NativeType.F64:
                    ctx.emitter.line(f"(local {native_local} f64)")
                case NativeType.I32:
                    ctx.emitter.line(f"(local {native_local} i32)")
                case NativeType.I64:
                    ctx.emitter.line(f"(local {native_local} i64)")

    # Prologue
    ctx.emitter.comment("prologue: bind args")

    # Convert $LIST args to PAIR chain if needed
    ctx.emitter.line("(if (ref.test (ref $LIST) (local.get $args))")
    ctx.emitter.line(
        "  (then (local.set $args (call $list_v2_to_pair (ref.cast (ref $LIST) (local.get $args))))))"
    )

    ctx.emitter.line(
        "(local.set $env (struct.new $ENV (local.get $env) (local.get $args)))"
    )

    # Copy parameters
    num_defaults = len(args.defaults)
    first_default_idx = len(param_names) - num_defaults

    ctx.emitter.line("(local.set $tmp (local.get $args))  ;; start of args list")

    for i, param_name in enumerate(param_names):
        ctx.emitter.comment(f"copy param '{param_name}' to local")

        if i >= first_default_idx:
            default_idx = i - first_default_idx
            ctx.emitter.line("(if (ref.is_null (local.get $tmp))")
            ctx.emitter.line("  (then")
            compile_expr(args.defaults[default_idx], ctx)
            ctx.emitter.line(f"    (local.set {ctx.local_vars[param_name]})")
            ctx.emitter.line("  )")
            ctx.emitter.line("  (else")
            ctx.emitter.line(
                f"    (local.set {ctx.local_vars[param_name]} "
                "(struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $tmp))))"
            )
            ctx.emitter.line(
                "    (local.set $tmp "
                "(struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $tmp))))"
            )
            ctx.emitter.line("  )")
            ctx.emitter.line(")")
        else:
            ctx.emitter.line(
                f"(local.set {ctx.local_vars[param_name]} "
                "(struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $tmp))))"
            )
            ctx.emitter.line(
                "(local.set $tmp "
                "(struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $tmp))))"
            )

        # If parameter is native, also unbox to native local
        if param_name in ctx.native_locals:
            native_type = ctx.native_locals[param_name]
            native_local = ctx.get_native_local_name(param_name)
            match native_type:
                case NativeType.F64:
                    ctx.emitter.line(
                        f"(local.set {native_local} "
                        f"(struct.get $FLOAT 0 (ref.cast (ref $FLOAT) "
                        f"(local.get {ctx.local_vars[param_name]}))))"
                    )
                case NativeType.I32:
                    ctx.emitter.line(
                        f"(local.set {native_local} "
                        f"(i31.get_s (ref.cast (ref i31) "
                        f"(local.get {ctx.local_vars[param_name]}))))"
                    )
                case NativeType.I64:
                    ctx.emitter.line(
                        f"(local.set {native_local} "
                        f"(struct.get $INT64 0 (ref.cast (ref $INT64) "
                        f"(local.get {ctx.local_vars[param_name]}))))"
                    )

    # Handle *args: remaining args go to vararg
    if vararg_name:
        ctx.emitter.comment(f"*args: remaining args -> '{vararg_name}'")
        # Convert remaining PAIR chain to tuple (which is also a PAIR chain in our impl)
        ctx.emitter.line(f"(local.set {ctx.local_vars[vararg_name]} (local.get $tmp))")

    # Initialize cell variables
    for param_name in param_names:
        if param_name in nested_nonlocals:
            ctx.emitter.comment(f"wrap param '{param_name}' in cell")
            ctx.emitter.emit_local_get(ctx.local_vars[param_name])
            ctx.emitter.emit_null_eq()
            ctx.emitter.emit_struct_new("$PAIR")
            ctx.emitter.emit_local_set(ctx.local_vars[param_name])

    for var_name in sorted(nested_nonlocals - set(param_names)):
        if var_name in ctx.local_vars:
            ctx.emitter.comment(f"init cell for '{var_name}'")
            ctx.emitter.emit_null_eq()
            ctx.emitter.emit_null_eq()
            ctx.emitter.emit_struct_new("$PAIR")
            ctx.emitter.emit_local_set(ctx.local_vars[var_name])

    # Compile body
    for stmt in body:
        compile_stmt(stmt, ctx)

    ctx.emitter.emit_null_eq()

    ctx.lexical_env.pop_frame()
    if all_captured_from_outer:
        ctx.lexical_env.pop_frame()

    ctx.emitter.indent -= 2
    ctx.emitter.line(")")

    # Restore state
    ctx.emitter.stream = saved_stream
    ctx.emitter.indent = saved_indent
    ctx.local_vars = saved_locals
    ctx.current_global_decls = saved_global_decls
    ctx.current_nonlocal_decls = saved_nonlocal_decls
    ctx.cell_vars = saved_cell_vars
    ctx.type_inferencer = saved_inferencer
    ctx.native_locals = saved_native_locals

    # Store function as closure
    table_idx = len(BUILTINS) + func_idx

    func_nonlocals = collect_nonlocal_decls(body)
    func_param_names = [arg.arg for arg in args.args]
    all_local_names = collect_local_vars(body) | set(func_param_names)

    pass_through_nonlocals = set()
    for var in find_all_nested_nonlocals(body):
        if var not in all_local_names:
            pass_through_nonlocals.add(var)

    all_nonlocals_needed = func_nonlocals | pass_through_nonlocals
    captured_cells = [
        v
        for v in sorted(all_nonlocals_needed)
        if v in ctx.cell_vars or v in ctx.current_nonlocal_decls
    ]

    free_vars = find_free_vars_in_func(body, set(func_param_names))
    captured_for_read = [
        v
        for v in sorted(free_vars)
        if v in ctx.local_vars and v not in func_nonlocals and v not in ctx.cell_vars
    ]

    all_captures = captured_cells + captured_for_read

    # Register module-level functions for direct calling (Phase 2 optimization)
    # Only register if:
    # 1. It's a module-level function (in global_vars)
    # 2. Has no decorators (decorated functions point to wrapper, not original)
    # 3. Has no captures (functions with captures need their closure environment)
    if name in ctx.global_vars and not has_decorators and not all_captures:
        ctx.register_function(name, table_idx)

        # Phase 4.1: Generate specialized function with direct parameters
        # Disabled by default - benchmarks show it adds overhead without significant benefit
        # because hot functions are already inlined by Phase 3
        ENABLE_SPEC_FUNCTIONS = False
        if ENABLE_SPEC_FUNCTIONS:
            arity = len(param_names)
            if (
                not args.vararg
                and not args.kwonlyargs
                and not args.kwarg
                and not args.defaults  # No default args for simplicity
                and arity <= 5  # Types exist for 0-5 params
            ):
                _compile_specialized_function(
                    name, args, body, ctx, func_idx, arity, nested_nonlocals, returns
                )

    if name not in ctx.local_vars:
        ctx.lexical_env.add_name(name)
        ctx.emitter.comment(f"define function '{name}' (unused)")
        ctx.local_vars[name] = f"$var_{name}"
        return

    ctx.emitter.comment(f"define function '{name}'")
    if not all_captures:
        ctx.emitter.line(
            f"(local.set {ctx.local_vars[name]} "
            f"(struct.new $CLOSURE (local.get $env) (i32.const {table_idx})))"
        )
        # Also set global if this is a module-level function (for forward refs)
        if name in ctx.global_vars:
            ctx.emitter.emit_local_get(ctx.local_vars[name])
            ctx.emitter.emit_global_set(f"$global_{name}")
        return

    ctx.emitter.line("(local.get $env)  ;; parent env")
    for var in all_captures:
        emit_captured_var(var, ctx)
    ctx.emitter.emit_null_eq()
    for _ in range(len(all_captures)):
        ctx.emitter.emit_struct_new("$PAIR")
    ctx.emitter.line("(struct.new $ENV)  ;; env with captures")
    ctx.emitter.emit_i32_const(table_idx)
    ctx.emitter.emit_struct_new("$CLOSURE")
    ctx.emitter.emit_local_set(ctx.local_vars[name])
    # Also set global if this is a module-level function (for forward refs)
    if name in ctx.global_vars:
        ctx.emitter.emit_local_get(ctx.local_vars[name])
        ctx.emitter.emit_global_set(f"$global_{name}")
