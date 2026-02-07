"""List and dict comprehension compilation."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from p2w.compiler.codegen.expressions import compile_expr

if TYPE_CHECKING:
    from p2w.compiler.context import CompilerContext


def compile_listcomp(
    elt: ast.expr, generators: list[ast.comprehension], ctx: CompilerContext
) -> None:
    """Compile list comprehension with multiple generators."""

    comp_id = ctx.comp_counter
    ctx.comp_counter += 1

    result_local = f"$comp_{comp_id}_result"

    ctx.emitter.comment(f"list comprehension {comp_id}")

    # Initialize result to empty list
    ctx.emitter.emit_null_eq()
    ctx.emitter.emit_local_set(result_local)

    # Save original variable bindings
    saved_vars: dict[str, str | None] = {}

    # Compile nested generators recursively
    _compile_listcomp_generators(
        elt, generators, 0, comp_id, result_local, saved_vars, ctx
    )

    # Restore original variable bindings
    for var_name, saved_local in saved_vars.items():
        if saved_local is not None:
            ctx.local_vars[var_name] = saved_local
        elif var_name in ctx.local_vars:
            del ctx.local_vars[var_name]

    ctx.emitter.emit_local_get(result_local)
    ctx.emitter.emit_list_reverse()
    # Convert PAIR chain to $LIST for O(1) indexed access
    ctx.emitter.emit_call("$pair_to_list_v2")


def _compile_listcomp_generators(
    elt: ast.expr,
    generators: list[ast.comprehension],
    gen_idx: int,
    comp_id: int,
    result_local: str,
    saved_vars: dict[str, str | None],
    ctx: CompilerContext,
) -> None:
    """Recursively compile nested generators for list comprehension."""
    if gen_idx >= len(generators):
        # Base case: all generators processed, emit the element
        compile_expr(elt, ctx)
        ctx.emitter.emit_local_get(result_local)
        ctx.emitter.emit_struct_new("$PAIR", "list entry")
        ctx.emitter.emit_local_set(result_local)
        return

    gen = generators[gen_idx]
    var_local = f"$comp_{comp_id}_var_{gen_idx}"
    iter_local = f"$comp_{comp_id}_iter_{gen_idx}"

    # Handle different target types
    match gen.target:
        case ast.Name(id=name):
            var_names = [name]
        case ast.Tuple(elts=elts) | ast.List(elts=elts):
            var_names = []
            for t in elts:
                match t:
                    case ast.Name(id=name):
                        var_names.append(name)
                    case _:
                        msg = f"Unsupported target in comprehension: {type(t).__name__}"
                        raise NotImplementedError(msg)
        case _:
            msg = (
                f"Unsupported target type in comprehension: {type(gen.target).__name__}"
            )
            raise NotImplementedError(msg)

    # Save current bindings
    for var_name in var_names:
        if var_name not in saved_vars:
            saved_vars[var_name] = ctx.local_vars.get(var_name)

    match gen.iter:
        case ast.Call(func=ast.Name(id="range"), args=range_args):
            _compile_listcomp_range_multi(
                elt,
                generators,
                gen_idx,
                var_names,
                range_args,
                gen.ifs,
                comp_id,
                result_local,
                var_local,
                saved_vars,
                ctx,
            )
        case _:
            _compile_listcomp_iter_multi(
                elt,
                generators,
                gen_idx,
                var_names,
                gen.iter,
                gen.ifs,
                comp_id,
                result_local,
                var_local,
                iter_local,
                saved_vars,
                ctx,
            )


def _compile_listcomp_range_multi(
    elt: ast.expr,
    generators: list[ast.comprehension],
    gen_idx: int,
    var_names: list[str],
    args: list[ast.expr],
    ifs: list[ast.expr],
    comp_id: int,
    result_local: str,
    var_local: str,
    saved_vars: dict[str, str | None],
    ctx: CompilerContext,
) -> None:
    """Compile one range-based generator in a multi-generator comprehension."""
    # Range loops only support single variable
    if len(var_names) != 1:
        msg = "Tuple unpacking not supported in range-based comprehension"
        raise NotImplementedError(msg)
    var_name = var_names[0]

    ctx.emitter.comment(f"generator {gen_idx}: range loop")

    # Parse range arguments
    start: ast.expr
    stop: ast.expr
    step: ast.expr
    if len(args) == 1:
        start = ast.Constant(value=0)
        stop = args[0]
        step = ast.Constant(value=1)
    elif len(args) == 2:
        start = args[0]
        stop = args[1]
        step = ast.Constant(value=1)
    else:
        start = args[0]
        stop = args[1]
        step = args[2]

    compile_expr(start, ctx)
    ctx.emitter.emit_local_set(var_local)

    ctx.emitter.emit_block_start(f"$break_{gen_idx}")
    ctx.emitter.emit_loop_start(f"$loop_{gen_idx}")

    ctx.emitter.emit_local_get(var_local)
    ctx.emitter.emit_i31_get_s()
    compile_expr(stop, ctx)
    ctx.emitter.emit_i31_get_s()
    ctx.emitter.line("i32.ge_s")
    ctx.emitter.emit_br_if(f"$break_{gen_idx}")

    # Bind var_name to var_local
    ctx.local_vars[var_name] = var_local

    # Handle filter conditions
    has_filters = len(ifs) > 0
    if has_filters:
        _compile_listcomp_filters(ifs, ctx)

    # Recurse to next generator (or emit element)
    _compile_listcomp_generators(
        elt, generators, gen_idx + 1, comp_id, result_local, saved_vars, ctx
    )

    if has_filters:
        ctx.emitter.emit_if_end()

    # Increment counter
    ctx.emitter.emit_local_get(var_local)
    ctx.emitter.emit_i31_get_s()
    compile_expr(step, ctx)
    ctx.emitter.emit_i31_get_s()
    ctx.emitter.line("i32.add")
    ctx.emitter.emit_ref_i31()
    ctx.emitter.emit_local_set(var_local)

    ctx.emitter.emit_br(f"$loop_{gen_idx}")

    ctx.emitter.emit_loop_end()
    ctx.emitter.emit_block_end()


def _compile_listcomp_iter_multi(
    elt: ast.expr,
    generators: list[ast.comprehension],
    gen_idx: int,
    var_names: list[str],
    iter_expr: ast.expr,
    ifs: list[ast.expr],
    comp_id: int,
    result_local: str,
    var_local: str,
    iter_local: str,
    saved_vars: dict[str, str | None],
    ctx: CompilerContext,
) -> None:
    """Compile one iter-based generator in a multi-generator comprehension."""
    ctx.emitter.comment(f"generator {gen_idx}: iter loop")

    compile_expr(iter_expr, ctx)
    # Convert $LIST/TUPLE/etc to PAIR chain for iteration
    ctx.emitter.emit_call("$iter_prepare")
    ctx.emitter.emit_local_set(iter_local)

    ctx.emitter.emit_block_start(f"$break_{gen_idx}")
    ctx.emitter.emit_loop_start(f"$loop_{gen_idx}")

    ctx.emitter.emit_local_get(iter_local)
    ctx.emitter.emit_ref_is_null()
    ctx.emitter.emit_br_if(f"$break_{gen_idx}")

    # Get current item
    ctx.emitter.emit_local_get(iter_local)
    ctx.emitter.emit_ref_cast("$PAIR")
    ctx.emitter.emit_struct_get("$PAIR", 0)
    ctx.emitter.emit_local_set(var_local)

    if len(var_names) == 1:
        # Simple case: single variable
        ctx.local_vars[var_names[0]] = var_local
    else:
        # Tuple unpacking: extract elements from the iteration item
        for i, var_name in enumerate(var_names):
            ctx.emitter.emit_local_get(var_local)
            ctx.emitter.emit_int(i)
            ctx.emitter.emit_call("$subscript_get")
            # Store in a temp local for this variable
            temp_local = f"$comp_{comp_id}_unpack_{gen_idx}_{i}"
            ctx.emitter.emit_local_set(temp_local)
            ctx.local_vars[var_name] = temp_local

    # Handle filter conditions
    has_filters = len(ifs) > 0
    if has_filters:
        _compile_listcomp_filters(ifs, ctx)

    # Recurse to next generator (or emit element)
    _compile_listcomp_generators(
        elt, generators, gen_idx + 1, comp_id, result_local, saved_vars, ctx
    )

    if has_filters:
        ctx.emitter.emit_if_end()

    # Move to next element
    ctx.emitter.emit_local_get(iter_local)
    ctx.emitter.emit_ref_cast("$PAIR")
    ctx.emitter.emit_struct_get("$PAIR", 1)
    ctx.emitter.emit_local_set(iter_local)

    ctx.emitter.emit_br(f"$loop_{gen_idx}")

    ctx.emitter.emit_loop_end()
    ctx.emitter.emit_block_end()


def _compile_listcomp_range(
    elt: ast.expr,
    var_name: str,
    args: list[ast.expr],
    ifs: list[ast.expr],
    comp_id: int,
    result_local: str,
    var_local: str,
    ctx: CompilerContext,
) -> None:
    """Compile list comprehension over range()."""

    ctx.emitter.comment("list comprehension over range")

    start: ast.expr
    stop: ast.expr
    step: ast.expr
    if len(args) == 1:
        start = ast.Constant(value=0)
        stop = args[0]
        step = ast.Constant(value=1)
    elif len(args) == 2:
        start = args[0]
        stop = args[1]
        step = ast.Constant(value=1)
    else:
        start = args[0]
        stop = args[1]
        step = args[2]

    compile_expr(start, ctx)
    ctx.emitter.emit_local_set(var_local)

    ctx.emitter.emit_block_start("$break")
    ctx.emitter.emit_loop_start("$loop")

    ctx.emitter.emit_local_get(var_local)
    ctx.emitter.emit_i31_get_s()
    compile_expr(stop, ctx)
    ctx.emitter.emit_i31_get_s()
    ctx.emitter.line("i32.ge_s")
    ctx.emitter.emit_br_if("$break")

    # Bind var_name to var_local
    saved_local = ctx.local_vars.get(var_name)
    ctx.local_vars[var_name] = var_local

    if ifs:
        _compile_listcomp_filters(ifs, ctx)

    compile_expr(elt, ctx)

    if saved_local is not None:
        ctx.local_vars[var_name] = saved_local
    else:
        del ctx.local_vars[var_name]

    ctx.emitter.emit_local_get(result_local)
    ctx.emitter.emit_struct_new("$PAIR", "list entry")
    ctx.emitter.emit_local_set(result_local)

    if ifs:
        ctx.emitter.emit_if_end()

    ctx.emitter.emit_local_get(var_local)
    ctx.emitter.emit_i31_get_s()
    compile_expr(step, ctx)
    ctx.emitter.emit_i31_get_s()
    ctx.emitter.line("i32.add")
    ctx.emitter.emit_ref_i31()
    ctx.emitter.emit_local_set(var_local)

    ctx.emitter.emit_br("$loop")

    ctx.emitter.emit_loop_end()
    ctx.emitter.emit_block_end()


def _compile_listcomp_iter(
    elt: ast.expr,
    var_name: str,
    iter_expr: ast.expr,
    ifs: list[ast.expr],
    comp_id: int,
    result_local: str,
    var_local: str,
    iter_local: str,
    ctx: CompilerContext,
) -> None:
    """Compile list comprehension over iterable."""

    ctx.emitter.comment("list comprehension over iterable")

    compile_expr(iter_expr, ctx)
    ctx.emitter.emit_local_set(iter_local)

    ctx.emitter.emit_block_start("$break")
    ctx.emitter.emit_loop_start("$loop")

    ctx.emitter.emit_local_get(iter_local)
    ctx.emitter.emit_ref_is_null()
    ctx.emitter.emit_br_if("$break")

    ctx.emitter.emit_local_get(iter_local)
    ctx.emitter.emit_ref_cast("$PAIR")
    ctx.emitter.emit_struct_get("$PAIR", 0)
    ctx.emitter.emit_local_set(var_local)

    saved_local = ctx.local_vars.get(var_name)
    ctx.local_vars[var_name] = var_local

    if ifs:
        _compile_listcomp_filters(ifs, ctx)

    compile_expr(elt, ctx)

    if saved_local is not None:
        ctx.local_vars[var_name] = saved_local
    else:
        del ctx.local_vars[var_name]

    ctx.emitter.emit_local_get(result_local)
    ctx.emitter.emit_struct_new("$PAIR", "list entry")
    ctx.emitter.emit_local_set(result_local)

    if ifs:
        ctx.emitter.emit_if_end()

    ctx.emitter.emit_local_get(iter_local)
    ctx.emitter.emit_ref_cast("$PAIR")
    ctx.emitter.emit_struct_get("$PAIR", 1)
    ctx.emitter.emit_local_set(iter_local)

    ctx.emitter.emit_br("$loop")

    ctx.emitter.emit_loop_end()
    ctx.emitter.emit_block_end()


def _compile_listcomp_filters(ifs: list[ast.expr], ctx: CompilerContext) -> None:
    """Compile filter conditions for list comprehension.

    Multiple conditions are ANDed together using short-circuit evaluation.
    Uses the same pattern as BoolOp(ast.And).
    """
    # Compile first condition
    compile_expr(ifs[0], ctx)

    # AND with remaining conditions (short-circuit)
    for if_clause in ifs[1:]:
        ctx.emitter.emit_local_tee("$tmp")
        ctx.emitter.emit_call("$is_false")
        ctx.emitter.line("if (result (ref null eq))")
        ctx.emitter.indent_inc()
        ctx.emitter.emit_local_get("$tmp")  # First was false, return it
        ctx.emitter.indent_dec()
        ctx.emitter.line("else")
        ctx.emitter.indent_inc()
        compile_expr(if_clause, ctx)  # First was true, evaluate next
        ctx.emitter.indent_dec()
        ctx.emitter.line("end")

    # Check if combined result is truthy
    ctx.emitter.emit_call("$is_false")
    ctx.emitter.line("i32.eqz")
    ctx.emitter.emit_if_start()


def compile_dictcomp(
    key: ast.expr,
    value: ast.expr,
    generators: list[ast.comprehension],
    ctx: CompilerContext,
) -> None:
    """Compile dict comprehension."""
    comp_id = ctx.comp_counter
    ctx.comp_counter += 1

    result_local = f"$comp_{comp_id}_result"
    var_local = f"$comp_{comp_id}_var_0"
    iter_local = f"$comp_{comp_id}_iter_0"

    ctx.emitter.comment(f"dict comprehension {comp_id} (hash table)")

    ctx.emitter.line("(call $dict_new)  ;; empty hash table dict")
    ctx.emitter.emit_local_set(result_local)

    if len(generators) != 1:
        msg = f"Only single generator supported, got {len(generators)}"
        raise NotImplementedError(msg)

    gen = generators[0]
    match gen.target:
        case ast.Name(id=var_name):
            pass
        case _:
            msg = "Only simple variable targets supported in comprehensions"
            raise NotImplementedError(msg)

    match gen.iter:
        case ast.Call(func=ast.Name(id="range"), args=range_args):
            _compile_dictcomp_range(
                key,
                value,
                var_name,
                range_args,
                gen.ifs,
                comp_id,
                result_local,
                var_local,
                ctx,
            )
        case _:
            _compile_dictcomp_iter(
                key,
                value,
                var_name,
                gen.iter,
                gen.ifs,
                comp_id,
                result_local,
                var_local,
                iter_local,
                ctx,
            )

    ctx.emitter.emit_local_get(result_local)
    # No reverse needed - hash table dict is already correctly built


def _compile_dictcomp_range(
    key_expr: ast.expr,
    value_expr: ast.expr,
    var_name: str,
    args: list[ast.expr],
    ifs: list[ast.expr],
    comp_id: int,
    result_local: str,
    var_local: str,
    ctx: CompilerContext,
) -> None:
    """Compile dict comprehension over range()."""

    ctx.emitter.comment("dict comprehension over range")

    start: ast.expr
    stop: ast.expr
    step: ast.expr
    if len(args) == 1:
        start = ast.Constant(value=0)
        stop = args[0]
        step = ast.Constant(value=1)
    elif len(args) == 2:
        start = args[0]
        stop = args[1]
        step = ast.Constant(value=1)
    else:
        start = args[0]
        stop = args[1]
        step = args[2]

    compile_expr(start, ctx)
    ctx.emitter.emit_local_set(var_local)

    ctx.emitter.emit_block_start("$break")
    ctx.emitter.emit_loop_start("$loop")

    ctx.emitter.emit_local_get(var_local)
    ctx.emitter.emit_i31_get_s()
    compile_expr(stop, ctx)
    ctx.emitter.emit_i31_get_s()
    ctx.emitter.line("i32.ge_s")
    ctx.emitter.emit_br_if("$break")

    saved_local = ctx.local_vars.get(var_name)
    ctx.local_vars[var_name] = var_local

    if ifs:
        _compile_dictcomp_filters(ifs, ctx)

    # Add key-value to hash table dict
    ctx.emitter.emit_local_get(result_local)
    compile_expr(key_expr, ctx)
    compile_expr(value_expr, ctx)
    ctx.emitter.line("call $dict_set_wrapped  ;; add entry to dict")
    ctx.emitter.emit_local_set(result_local)

    if saved_local is not None:
        ctx.local_vars[var_name] = saved_local
    else:
        del ctx.local_vars[var_name]

    if ifs:
        ctx.emitter.emit_if_end()

    ctx.emitter.emit_local_get(var_local)
    ctx.emitter.emit_i31_get_s()
    compile_expr(step, ctx)
    ctx.emitter.emit_i31_get_s()
    ctx.emitter.line("i32.add")
    ctx.emitter.emit_ref_i31()
    ctx.emitter.emit_local_set(var_local)

    ctx.emitter.emit_br("$loop")

    ctx.emitter.emit_loop_end()
    ctx.emitter.emit_block_end()


def _compile_dictcomp_iter(
    key_expr: ast.expr,
    value_expr: ast.expr,
    var_name: str,
    iter_expr: ast.expr,
    ifs: list[ast.expr],
    comp_id: int,
    result_local: str,
    var_local: str,
    iter_local: str,
    ctx: CompilerContext,
) -> None:
    """Compile dict comprehension over iterable."""

    ctx.emitter.comment("dict comprehension over iterable")

    compile_expr(iter_expr, ctx)
    ctx.emitter.emit_local_set(iter_local)

    ctx.emitter.emit_block_start("$break")
    ctx.emitter.emit_loop_start("$loop")

    ctx.emitter.emit_local_get(iter_local)
    ctx.emitter.emit_ref_is_null()
    ctx.emitter.emit_br_if("$break")

    ctx.emitter.emit_local_get(iter_local)
    ctx.emitter.emit_ref_cast("$PAIR")
    ctx.emitter.emit_struct_get("$PAIR", 0)
    ctx.emitter.emit_local_set(var_local)

    saved_local = ctx.local_vars.get(var_name)
    ctx.local_vars[var_name] = var_local

    if ifs:
        _compile_dictcomp_filters(ifs, ctx)

    # Add key-value to hash table dict
    ctx.emitter.emit_local_get(result_local)
    compile_expr(key_expr, ctx)
    compile_expr(value_expr, ctx)
    ctx.emitter.line("call $dict_set_wrapped  ;; add entry to dict")
    ctx.emitter.emit_local_set(result_local)

    if saved_local is not None:
        ctx.local_vars[var_name] = saved_local
    else:
        del ctx.local_vars[var_name]

    if ifs:
        ctx.emitter.emit_if_end()

    ctx.emitter.emit_local_get(iter_local)
    ctx.emitter.emit_ref_cast("$PAIR")
    ctx.emitter.emit_struct_get("$PAIR", 1)
    ctx.emitter.emit_local_set(iter_local)

    ctx.emitter.emit_br("$loop")

    ctx.emitter.emit_loop_end()
    ctx.emitter.emit_block_end()


def _compile_dictcomp_filters(ifs: list[ast.expr], ctx: CompilerContext) -> None:
    """Compile filter conditions for dict comprehension."""

    for i, if_clause in enumerate(ifs):
        if i == 0:
            compile_expr(if_clause, ctx)
        else:
            compile_expr(if_clause, ctx)
            ctx.emitter.emit_call("$is_false")
            ctx.emitter.emit_if_start()
            ctx.emitter.emit_drop()
            ctx.emitter.emit_bool(False)
            ctx.emitter.emit_if_end()

    ctx.emitter.emit_call("$is_false")
    ctx.emitter.line("i32.eqz")
    ctx.emitter.emit_if_start()
