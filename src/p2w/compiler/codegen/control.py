"""Control flow compilation - if, while, for."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from p2w.compiler.codegen.expressions import compile_expr
from p2w.compiler.codegen.statements import compile_stmt
from p2w.compiler.types import NativeType

if TYPE_CHECKING:
    from p2w.compiler.context import CompilerContext


def _sync_native_from_boxed(name: str, ctx: CompilerContext) -> None:
    """Sync native local from boxed local if variable is native."""
    if name not in ctx.native_locals:
        return

    native_type = ctx.native_locals[name]
    native_local = ctx.get_native_local_name(name)
    boxed_local = ctx.local_vars[name]

    match native_type:
        case NativeType.F64:
            ctx.emitter.line(
                f"(local.set {native_local} "
                f"(struct.get $FLOAT 0 (ref.cast (ref $FLOAT) "
                f"(local.get {boxed_local}))))"
            )
        case NativeType.I32:
            ctx.emitter.line(
                f"(local.set {native_local} "
                f"(i31.get_s (ref.cast (ref i31) "
                f"(local.get {boxed_local}))))"
            )
        case NativeType.I64:
            ctx.emitter.line(
                f"(local.set {native_local} "
                f"(struct.get $INT64 0 (ref.cast (ref $INT64) "
                f"(local.get {boxed_local}))))"
            )


# Enable direct array iteration optimization for LIST/TUPLE
# This avoids PAIR chain allocation for list/tuple iteration
ENABLE_DIRECT_ARRAY_ITERATION = True


def _detect_isinstance_narrowing(
    test: ast.expr, body: list[ast.stmt], ctx: CompilerContext
) -> dict | None:
    """Detect isinstance-based type narrowing patterns.

    Patterns detected:
    1. if isinstance(x, C): ... → x is C in body
    2. if not isinstance(x, C): return → x is C after if block

    Returns dict with narrowing info or None if no narrowing detected.
    """
    # Check for "not isinstance(...)" or "isinstance(...)"
    match test:
        case ast.UnaryOp(op=ast.Not(), operand=inner):
            is_negated = True
        case _:
            inner = test
            is_negated = False

    # Check for isinstance(var, Class)
    match inner:
        case ast.Call(
            func=ast.Name(id="isinstance"),
            args=[ast.Name(id=var_name), ast.Name(id=class_name)],
        ):
            pass
        case _:
            return None

    # Only narrow to slotted classes (where we can optimize)
    if class_name not in ctx.slotted_classes:
        return None

    # Determine where narrowing applies
    if is_negated:
        # "if not isinstance(x, C): return" → x is C after the if
        # Check if body is just a return statement
        match body:
            case [ast.Return()]:
                is_early_return = True
            case _:
                is_early_return = False
        return {
            "var_name": var_name,
            "class_name": class_name,
            "in_body": False,
            "after_if": is_early_return,
        }
    # "if isinstance(x, C): ..." → x is C in body
    return {
        "var_name": var_name,
        "class_name": class_name,
        "in_body": True,
        "after_if": False,
    }


def _apply_type_narrowing(narrowing: dict, ctx: CompilerContext) -> None:
    """Apply type narrowing - register variable as slotted instance."""
    var_name = narrowing["var_name"]
    class_name = narrowing["class_name"]
    ctx.slotted_instances[var_name] = class_name


def _remove_type_narrowing(narrowing: dict, ctx: CompilerContext) -> None:
    """Remove type narrowing after leaving scope."""
    var_name = narrowing["var_name"]
    if var_name in ctx.slotted_instances:
        del ctx.slotted_instances[var_name]


def compile_if_stmt(
    test: ast.expr,
    body: list[ast.stmt],
    orelse: list[ast.stmt],
    ctx: CompilerContext,
) -> None:
    """Compile if statement."""

    # Detect isinstance type narrowing patterns
    narrowing = _detect_isinstance_narrowing(test, body, ctx)

    compile_expr(test, ctx)
    ctx.emitter.emit_call("$is_false")
    ctx.emitter.emit_if_start()

    # else branch (is_false returns true when condition is false)
    # For "if isinstance(x, C):", orelse runs when x is NOT C
    for stmt in orelse:
        compile_stmt(stmt, ctx)

    ctx.emitter.emit_if_else()

    # then branch
    # For "if isinstance(x, C):", body runs when x IS C
    if narrowing and narrowing["in_body"]:
        _apply_type_narrowing(narrowing, ctx)

    for stmt in body:
        compile_stmt(stmt, ctx)

    if narrowing and narrowing["in_body"]:
        _remove_type_narrowing(narrowing, ctx)

    ctx.emitter.emit_if_end()

    # After early-return pattern: "if not isinstance(x, C): return"
    # The code after the if knows x IS C
    if narrowing and narrowing["after_if"]:
        _apply_type_narrowing(narrowing, ctx)


def compile_while_stmt(
    test: ast.expr, body: list[ast.stmt], ctx: CompilerContext
) -> None:
    """Compile while loop."""

    ctx.emitter.emit_block_start("$break")
    ctx.emitter.emit_loop_start("$continue")

    compile_expr(test, ctx)
    ctx.emitter.emit_call("$is_false")
    ctx.emitter.emit_br_if("$break")

    for stmt in body:
        compile_stmt(stmt, ctx)

    ctx.emitter.emit_br("$continue")

    ctx.emitter.emit_loop_end()
    ctx.emitter.emit_block_end()


def compile_for_stmt(
    name: str,
    iter_expr: ast.expr,
    body: list[ast.stmt],
    orelse: list[ast.stmt] | None,
    ctx: CompilerContext,
) -> None:
    """Compile for loop."""

    # Check for range()
    match iter_expr:
        case ast.Call(func=ast.Name(id="range"), args=range_args):
            _compile_for_range(name, range_args, body, orelse, ctx)
            return

    # Use direct array iteration for LIST/TUPLE if enabled
    if ENABLE_DIRECT_ARRAY_ITERATION:
        _compile_for_with_dispatch(name, iter_expr, body, orelse, ctx)
        return

    # Legacy: PAIR chain iteration
    _compile_for_pair_chain(name, iter_expr, body, orelse, ctx)


def _compile_for_with_dispatch(
    name: str,
    iter_expr: ast.expr,
    body: list[ast.stmt],
    orelse: list[ast.stmt] | None,
    ctx: CompilerContext,
) -> None:
    """Compile for loop with runtime dispatch for LIST/TUPLE vs PAIR chain."""
    ctx.emitter.comment("for loop with type dispatch")

    # Compile the iterable and store for type checking
    compile_expr(iter_expr, ctx)
    ctx.emitter.line("(local.set $iter_source)")

    # Get loop variable local
    if name not in ctx.local_vars:
        msg = f"Loop variable '{name}' not declared"
        raise NameError(msg)
    loop_var = ctx.local_vars[name]

    # Outer blocks for break/for-else
    if orelse:
        ctx.emitter.emit_block_start("$break")
        ctx.emitter.emit_block_start("$loop_done")
    else:
        ctx.emitter.emit_block_start("$break")

    # Check if it's a $LIST for direct array iteration
    ctx.emitter.line("(if (ref.test (ref $LIST) (local.get $iter_source))")
    ctx.emitter.line("  (then")
    ctx.emitter.comment("direct LIST iteration (fast path)")

    # ===== LIST iteration path =====
    # Get array length and data
    ctx.emitter.line(
        "    (local.set $list_ref (ref.cast (ref $LIST) (local.get $iter_source)))"
    )
    ctx.emitter.line(
        "    (local.set $iter_len (struct.get $LIST $len (local.get $list_ref)))"
    )
    ctx.emitter.line("    (local.set $iter_idx (i32.const 0))")

    # Loop
    ctx.emitter.line("    (block $list_done")
    ctx.emitter.line("      (loop $list_loop")
    # Check if idx >= len
    ctx.emitter.line(
        "        (br_if $list_done (i32.ge_s (local.get $iter_idx) (local.get $iter_len)))"
    )
    # Get current element: list.data[idx]
    ctx.emitter.line("        (local.set " + loop_var + " (array.get $ARRAY_ANY")
    ctx.emitter.line("          (struct.get $LIST $data (local.get $list_ref))")
    ctx.emitter.line("          (local.get $iter_idx)))")
    # Sync native local if loop variable is native
    _sync_native_from_boxed(name, ctx)

    # Continue block for body
    ctx.emitter.emit_block_start("$continue")
    for stmt in body:
        compile_stmt(stmt, ctx)
    ctx.emitter.emit_block_end()

    # Increment index
    ctx.emitter.line(
        "        (local.set $iter_idx (i32.add (local.get $iter_idx) (i32.const 1)))"
    )
    ctx.emitter.line("        (br $list_loop)")
    ctx.emitter.line("      )")
    ctx.emitter.line("    )")

    ctx.emitter.line("  )")

    # Check if it's a $TUPLE
    ctx.emitter.line("  (else (if (ref.test (ref $TUPLE) (local.get $iter_source))")
    ctx.emitter.line("    (then")
    ctx.emitter.comment("direct TUPLE iteration (fast path)")

    # ===== TUPLE iteration path =====
    ctx.emitter.line(
        "      (local.set $tuple_ref (ref.cast (ref $TUPLE) (local.get $iter_source)))"
    )
    ctx.emitter.line(
        "      (local.set $iter_len (struct.get $TUPLE $len (local.get $tuple_ref)))"
    )
    ctx.emitter.line("      (local.set $iter_idx (i32.const 0))")

    ctx.emitter.line("      (block $tuple_done")
    ctx.emitter.line("        (loop $tuple_loop")
    ctx.emitter.line(
        "          (br_if $tuple_done (i32.ge_s (local.get $iter_idx) (local.get $iter_len)))"
    )
    ctx.emitter.line("          (local.set " + loop_var + " (array.get $ARRAY_ANY")
    ctx.emitter.line("            (struct.get $TUPLE $data (local.get $tuple_ref))")
    ctx.emitter.line("            (local.get $iter_idx)))")
    # Sync native local if loop variable is native
    _sync_native_from_boxed(name, ctx)

    ctx.emitter.emit_block_start("$continue")
    for stmt in body:
        compile_stmt(stmt, ctx)
    ctx.emitter.emit_block_end()

    ctx.emitter.line(
        "          (local.set $iter_idx (i32.add (local.get $iter_idx) (i32.const 1)))"
    )
    ctx.emitter.line("          (br $tuple_loop)")
    ctx.emitter.line("        )")
    ctx.emitter.line("      )")

    ctx.emitter.line("    )")

    # Fallback: PAIR chain iteration
    ctx.emitter.line("    (else")
    ctx.emitter.comment("PAIR chain iteration (fallback)")

    # ===== PAIR chain iteration path =====
    iter_local = f"$iter_{name}"
    ctx.emitter.line(
        f"      (local.set {iter_local} (call $iter_prepare (local.get $iter_source)))"
    )

    ctx.emitter.line("      (block $pair_done")
    ctx.emitter.line("        (loop $pair_loop")
    ctx.emitter.line(
        f"          (br_if $pair_done (ref.is_null (local.get {iter_local})))"
    )
    ctx.emitter.line(
        f"          (local.set {loop_var} (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get {iter_local}))))"
    )
    # Sync native local if loop variable is native
    _sync_native_from_boxed(name, ctx)

    ctx.emitter.emit_block_start("$continue")
    for stmt in body:
        compile_stmt(stmt, ctx)
    ctx.emitter.emit_block_end()

    ctx.emitter.line(
        f"          (local.set {iter_local} (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get {iter_local}))))"
    )
    ctx.emitter.line("          (br $pair_loop)")
    ctx.emitter.line("        )")
    ctx.emitter.line("      )")

    ctx.emitter.line("    )")
    ctx.emitter.line("  ))")  # close TUPLE if-else
    ctx.emitter.line(")")  # close LIST if

    # Handle for-else
    if orelse:
        ctx.emitter.emit_block_end()  # $loop_done
        ctx.emitter.comment("for-else clause")
        for stmt in orelse:
            compile_stmt(stmt, ctx)

    ctx.emitter.emit_block_end()  # $break


def _compile_for_pair_chain(
    name: str,
    iter_expr: ast.expr,
    body: list[ast.stmt],
    orelse: list[ast.stmt] | None,
    ctx: CompilerContext,
) -> None:
    """Compile for loop using PAIR chain iteration (legacy path)."""
    ctx.emitter.comment("for loop over list (PAIR chain)")
    iter_local = f"$iter_{name}"

    compile_expr(iter_expr, ctx)
    ctx.emitter.emit_call("$iter_prepare")
    ctx.emitter.emit_local_set(iter_local)

    if orelse:
        ctx.emitter.emit_block_start("$break")
        ctx.emitter.emit_block_start("$loop_done")
    else:
        ctx.emitter.emit_block_start("$break")

    ctx.emitter.emit_loop_start("$loop")

    ctx.emitter.emit_local_get(iter_local)
    ctx.emitter.emit_ref_is_null()
    if orelse:
        ctx.emitter.emit_br_if("$loop_done")
    else:
        ctx.emitter.emit_br_if("$break")

    ctx.emitter.emit_local_get(iter_local)
    ctx.emitter.emit_ref_cast("$PAIR")
    ctx.emitter.emit_struct_get("$PAIR", 0)
    if name in ctx.local_vars:
        ctx.emitter.emit_local_set(ctx.local_vars[name])
        # Sync native local if loop variable is native
        _sync_native_from_boxed(name, ctx)
    else:
        msg = f"Loop variable '{name}' not declared"
        raise NameError(msg)

    ctx.emitter.emit_block_start("$continue")

    for stmt in body:
        compile_stmt(stmt, ctx)

    ctx.emitter.emit_block_end()

    ctx.emitter.emit_local_get(iter_local)
    ctx.emitter.emit_ref_cast("$PAIR")
    ctx.emitter.emit_struct_get("$PAIR", 1)
    ctx.emitter.emit_local_set(iter_local)

    ctx.emitter.emit_br("$loop")

    ctx.emitter.emit_loop_end()

    if orelse:
        ctx.emitter.emit_block_end()
        ctx.emitter.comment("for-else clause")
        for stmt in orelse:
            compile_stmt(stmt, ctx)

    ctx.emitter.emit_block_end()


def compile_for_tuple_stmt(
    targets: list[ast.expr],
    iter_expr: ast.expr,
    body: list[ast.stmt],
    orelse: list[ast.stmt] | None,
    ctx: CompilerContext,
) -> None:
    """Compile for loop with tuple unpacking like: for a, b in pairs."""
    if ENABLE_DIRECT_ARRAY_ITERATION:
        _compile_for_tuple_with_dispatch(targets, iter_expr, body, orelse, ctx)
        return

    _compile_for_tuple_pair_chain(targets, iter_expr, body, orelse, ctx)


def _emit_tuple_unpack(
    targets: list[ast.expr],
    ctx: CompilerContext,
    source_var: str = "$tmp",
    depth: int = 0,
) -> None:
    """Emit code to unpack source_var into target variables.

    Handles nested tuple unpacking like: for i, (a, b) in items
    """
    for i, target in enumerate(targets):
        match target:
            case ast.Name(id=name):
                if name in ctx.local_vars:
                    ctx.emitter.emit_local_get(source_var)
                    ctx.emitter.emit_int(i)
                    ctx.emitter.emit_call("$subscript_get")
                    ctx.emitter.emit_local_set(ctx.local_vars[name])
                else:
                    msg = f"Loop variable '{name}' not declared"
                    raise NameError(msg)
            case ast.Tuple(elts=nested_targets) | ast.List(elts=nested_targets):
                # Nested tuple unpacking: (a, b) or [a, b]
                # Extract element at position i into a temp, then recursively unpack
                # Use $tmp2 for first level nesting, $tmp3 for second, etc.
                ctx.emitter.comment(f"nested unpack at index {i}")
                ctx.emitter.emit_local_get(source_var)
                ctx.emitter.emit_int(i)
                ctx.emitter.emit_call("$subscript_get")
                # Use $tmp2 for depth 0 nesting, $tmp3 for depth 1, etc.
                nested_var = f"$tmp{depth + 2}"
                ctx.emitter.emit_local_set(nested_var)
                _emit_tuple_unpack(nested_targets, ctx, nested_var, depth + 1)
            case _:
                msg = f"Tuple unpack target not implemented: {type(target).__name__}"
                raise NotImplementedError(msg)


def _compile_for_tuple_with_dispatch(
    targets: list[ast.expr],
    iter_expr: ast.expr,
    body: list[ast.stmt],
    orelse: list[ast.stmt] | None,
    ctx: CompilerContext,
) -> None:
    """Compile for loop with tuple unpacking using runtime dispatch."""
    ctx.emitter.comment("for loop with tuple unpacking (with dispatch)")

    # Compile the iterable and store for type checking
    compile_expr(iter_expr, ctx)
    ctx.emitter.line("(local.set $iter_source)")

    # Outer blocks for break/for-else
    if orelse:
        ctx.emitter.emit_block_start("$break")
        ctx.emitter.emit_block_start("$loop_done")
    else:
        ctx.emitter.emit_block_start("$break")

    # Check if it's a $LIST for direct array iteration
    ctx.emitter.line("(if (ref.test (ref $LIST) (local.get $iter_source))")
    ctx.emitter.line("  (then")
    ctx.emitter.comment("direct LIST iteration (fast path)")

    # ===== LIST iteration path =====
    ctx.emitter.line(
        "    (local.set $list_ref (ref.cast (ref $LIST) (local.get $iter_source)))"
    )
    ctx.emitter.line(
        "    (local.set $iter_len (struct.get $LIST $len (local.get $list_ref)))"
    )
    ctx.emitter.line("    (local.set $iter_idx (i32.const 0))")

    ctx.emitter.line("    (block $list_done")
    ctx.emitter.line("      (loop $list_loop")
    ctx.emitter.line(
        "        (br_if $list_done (i32.ge_s (local.get $iter_idx) (local.get $iter_len)))"
    )
    # Get current element and store in $tmp for unpacking
    ctx.emitter.line("        (local.set $tmp (array.get $ARRAY_ANY")
    ctx.emitter.line("          (struct.get $LIST $data (local.get $list_ref))")
    ctx.emitter.line("          (local.get $iter_idx)))")

    # Unpack tuple into target variables
    _emit_tuple_unpack(targets, ctx)

    ctx.emitter.emit_block_start("$continue")
    for stmt in body:
        compile_stmt(stmt, ctx)
    ctx.emitter.emit_block_end()

    ctx.emitter.line(
        "        (local.set $iter_idx (i32.add (local.get $iter_idx) (i32.const 1)))"
    )
    ctx.emitter.line("        (br $list_loop)")
    ctx.emitter.line("      )")
    ctx.emitter.line("    )")

    ctx.emitter.line("  )")

    # Check if it's a $TUPLE
    ctx.emitter.line("  (else (if (ref.test (ref $TUPLE) (local.get $iter_source))")
    ctx.emitter.line("    (then")
    ctx.emitter.comment("direct TUPLE iteration (fast path)")

    # ===== TUPLE iteration path =====
    ctx.emitter.line(
        "      (local.set $tuple_ref (ref.cast (ref $TUPLE) (local.get $iter_source)))"
    )
    ctx.emitter.line(
        "      (local.set $iter_len (struct.get $TUPLE $len (local.get $tuple_ref)))"
    )
    ctx.emitter.line("      (local.set $iter_idx (i32.const 0))")

    ctx.emitter.line("      (block $tuple_done")
    ctx.emitter.line("        (loop $tuple_loop")
    ctx.emitter.line(
        "          (br_if $tuple_done (i32.ge_s (local.get $iter_idx) (local.get $iter_len)))"
    )
    ctx.emitter.line("          (local.set $tmp (array.get $ARRAY_ANY")
    ctx.emitter.line("            (struct.get $TUPLE $data (local.get $tuple_ref))")
    ctx.emitter.line("            (local.get $iter_idx)))")

    _emit_tuple_unpack(targets, ctx)

    ctx.emitter.emit_block_start("$continue")
    for stmt in body:
        compile_stmt(stmt, ctx)
    ctx.emitter.emit_block_end()

    ctx.emitter.line(
        "          (local.set $iter_idx (i32.add (local.get $iter_idx) (i32.const 1)))"
    )
    ctx.emitter.line("          (br $tuple_loop)")
    ctx.emitter.line("        )")
    ctx.emitter.line("      )")

    ctx.emitter.line("    )")

    # Fallback: PAIR chain iteration
    ctx.emitter.line("    (else")
    ctx.emitter.comment("PAIR chain iteration (fallback)")

    # ===== PAIR chain iteration path =====
    iter_local = "$iter_tuple"
    ctx.emitter.line(
        f"      (local.set {iter_local} (call $iter_prepare (local.get $iter_source)))"
    )

    ctx.emitter.line("      (block $pair_done")
    ctx.emitter.line("        (loop $pair_loop")
    ctx.emitter.line(
        f"          (br_if $pair_done (ref.is_null (local.get {iter_local})))"
    )
    ctx.emitter.line(
        f"          (local.set $tmp (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get {iter_local}))))"
    )

    _emit_tuple_unpack(targets, ctx)

    ctx.emitter.emit_block_start("$continue")
    for stmt in body:
        compile_stmt(stmt, ctx)
    ctx.emitter.emit_block_end()

    ctx.emitter.line(
        f"          (local.set {iter_local} (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get {iter_local}))))"
    )
    ctx.emitter.line("          (br $pair_loop)")
    ctx.emitter.line("        )")
    ctx.emitter.line("      )")

    ctx.emitter.line("    )")
    ctx.emitter.line("  ))")  # close TUPLE if-else
    ctx.emitter.line(")")  # close LIST if

    # Handle for-else
    if orelse:
        ctx.emitter.emit_block_end()  # $loop_done
        ctx.emitter.comment("for-else clause")
        for stmt in orelse:
            compile_stmt(stmt, ctx)

    ctx.emitter.emit_block_end()  # $break


def _compile_for_tuple_pair_chain(
    targets: list[ast.expr],
    iter_expr: ast.expr,
    body: list[ast.stmt],
    orelse: list[ast.stmt] | None,
    ctx: CompilerContext,
) -> None:
    """Compile for loop with tuple unpacking using PAIR chain (legacy)."""
    ctx.emitter.comment("for loop with tuple unpacking (PAIR chain)")
    iter_local = "$iter_tuple"

    compile_expr(iter_expr, ctx)
    ctx.emitter.emit_call("$iter_prepare")
    ctx.emitter.emit_local_set(iter_local)

    if orelse:
        ctx.emitter.emit_block_start("$break")
        ctx.emitter.emit_block_start("$loop_done")
    else:
        ctx.emitter.emit_block_start("$break")

    ctx.emitter.emit_loop_start("$loop")

    ctx.emitter.emit_local_get(iter_local)
    ctx.emitter.emit_ref_is_null()
    if orelse:
        ctx.emitter.emit_br_if("$loop_done")
    else:
        ctx.emitter.emit_br_if("$break")

    # Get the current item (a tuple)
    ctx.emitter.emit_local_get(iter_local)
    ctx.emitter.emit_ref_cast("$PAIR")
    ctx.emitter.emit_struct_get("$PAIR", 0)
    ctx.emitter.emit_local_set("$tmp")

    # Unpack the tuple into target variables
    _emit_tuple_unpack(targets, ctx)

    ctx.emitter.emit_block_start("$continue")

    for stmt in body:
        compile_stmt(stmt, ctx)

    ctx.emitter.emit_block_end()

    ctx.emitter.emit_local_get(iter_local)
    ctx.emitter.emit_ref_cast("$PAIR")
    ctx.emitter.emit_struct_get("$PAIR", 1)
    ctx.emitter.emit_local_set(iter_local)

    ctx.emitter.emit_br("$loop")

    ctx.emitter.emit_loop_end()

    if orelse:
        ctx.emitter.emit_block_end()
        ctx.emitter.comment("for-else clause")
        for stmt in orelse:
            compile_stmt(stmt, ctx)

    ctx.emitter.emit_block_end()


def _detect_len_pattern(stop: ast.expr) -> str | None:
    """Detect if stop expression is len(container) and return container name."""
    match stop:
        case ast.Call(func=ast.Name(id="len"), args=[ast.Name(id=container_name)]):
            return container_name
    return None


def _compile_for_range(
    name: str,
    args: list[ast.expr],
    body: list[ast.stmt],
    orelse: list[ast.stmt] | None,
    ctx: CompilerContext,
) -> None:
    """Compile for loop with range()."""

    ctx.emitter.comment("for loop over range")

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
    elif len(args) == 3:
        start = args[0]
        stop = args[1]
        step = args[2]
    else:
        msg = f"range() takes 1-3 arguments, got {len(args)}"
        raise ValueError(msg)

    # Detect safe bounds pattern: for i in range(len(lst)) or for i in range(0, len(lst))
    safe_container: str | None = None
    match (start, step):
        case (ast.Constant(value=0), ast.Constant(value=1)):
            safe_container = _detect_len_pattern(stop)
            if safe_container and safe_container in ctx.local_vars:
                # Record safe bounds relationship for the loop body
                ctx.safe_bounds[name] = (safe_container, ctx.local_vars[safe_container])

    if name not in ctx.local_vars:
        msg = f"Loop variable '{name}' not declared"
        raise NameError(msg)
    counter_local = ctx.local_vars[name]

    # Check if loop variable is native i32
    use_native_counter = (
        name in ctx.native_locals and ctx.native_locals[name] == NativeType.I32
    )
    native_counter_local = (
        ctx.get_native_local_name(name) if use_native_counter else None
    )

    compile_expr(start, ctx)
    if use_native_counter and ctx.has_native_value:
        # Start value is native, store directly to native local
        ctx.emitter.line(f"(local.set {native_counter_local})")
        # Also store boxed version for compatibility
        ctx.emitter.line(
            f"(local.set {counter_local} (ref.i31 (local.get {native_counter_local})))"
        )
        ctx.clear_native_value()
    else:
        ctx.emitter.emit_local_set(counter_local)
        # Sync native local if loop variable is native
        _sync_native_from_boxed(name, ctx)

    if orelse:
        ctx.emitter.emit_block_start("$break")
        ctx.emitter.emit_block_start("$loop_done")
    else:
        ctx.emitter.emit_block_start("$break")

    # Add comment if safe bounds optimization is active
    if safe_container:
        ctx.emitter.comment(f"safe bounds: {name} in range(len({safe_container}))")

    ctx.emitter.emit_loop_start("$loop")

    # Loop condition: counter >= stop?
    if use_native_counter:
        ctx.emitter.line(f"(local.get {native_counter_local})")
    else:
        ctx.emitter.emit_local_get(counter_local)
        ctx.emitter.emit_i31_get_s()
    compile_expr(stop, ctx)
    # Only unbox if not already a native value
    if ctx.has_native_value:
        ctx.clear_native_value()
    else:
        ctx.emitter.emit_i31_get_s()
    ctx.emitter.line("i32.ge_s")
    if orelse:
        ctx.emitter.emit_br_if("$loop_done")
    else:
        ctx.emitter.emit_br_if("$break")

    ctx.emitter.emit_block_start("$continue")

    for stmt in body:
        compile_stmt(stmt, ctx)

    ctx.emitter.emit_block_end()

    # Loop increment
    if use_native_counter:
        ctx.emitter.line(f"(local.get {native_counter_local})")
        compile_expr(step, ctx)
        if ctx.has_native_value:
            ctx.clear_native_value()
        else:
            ctx.emitter.emit_i31_get_s()
        ctx.emitter.line("i32.add")
        ctx.emitter.line(f"(local.set {native_counter_local})")
        # Also update boxed version for any code that reads it
        ctx.emitter.line(
            f"(local.set {counter_local} (ref.i31 (local.get {native_counter_local})))"
        )
    else:
        ctx.emitter.emit_local_get(counter_local)
        ctx.emitter.emit_i31_get_s()
        compile_expr(step, ctx)
        # Only unbox if not already a native value
        if ctx.has_native_value:
            ctx.clear_native_value()
        else:
            ctx.emitter.emit_i31_get_s()
        ctx.emitter.line("i32.add")
        ctx.emitter.emit_ref_i31()
        ctx.emitter.emit_local_set(counter_local)
        # Sync native local if loop variable is native
        _sync_native_from_boxed(name, ctx)

    ctx.emitter.emit_br("$loop")

    ctx.emitter.emit_loop_end()

    if orelse:
        ctx.emitter.emit_block_end()
        ctx.emitter.comment("for-else clause")
        for stmt in orelse:
            compile_stmt(stmt, ctx)

    ctx.emitter.emit_block_end()

    # Clear safe bounds after loop ends
    if safe_container:
        del ctx.safe_bounds[name]
