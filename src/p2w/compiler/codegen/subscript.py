"""Subscript compilation."""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from p2w.compiler.codegen.expressions import compile_expr
from p2w.compiler.types import (
    I32Type,
    I64Type,
    IntType,
    ListType,
    NativeType,
)

if TYPE_CHECKING:
    from p2w.compiler.context import CompilerContext


def compile_index_value(index: ast.expr, ctx: CompilerContext) -> None:
    """Emit raw i32 value for use as array index.

    Optimizes native i32 variables by loading directly without boxing/unboxing.
    """
    # Fast path: native i32 variable - load directly
    if isinstance(index, ast.Name):
        name = index.id
        if name in ctx.native_locals and ctx.native_locals[name] == NativeType.I32:
            native_local = ctx.get_native_local_name(name)
            ctx.emitter.line(f"(local.get {native_local})  ;; native i32 index")
            return

    # General case: compile expression and unbox if needed
    compile_expr(index, ctx)
    if ctx.has_native_value:
        ctx.clear_native_value()
    else:
        ctx.emitter.emit_i31_get_s()


def _compile_const_index_list_get(
    container: ast.Name, index: int, ctx: CompilerContext
) -> None:
    """Optimized list access for constant non-negative index.

    For patterns like x[0], x[1], x[2] where:
    - Container is a local variable
    - Index is a compile-time constant
    - Index is non-negative

    Optimizations vs general _compile_inline_list_get:
    - No negative index handling (index is known non-negative)
    - No index computation (constant i32)
    - Simpler bounds check (only idx < len)
    """
    container_local = ctx.local_vars[container.id]
    ctx.emitter.comment(f"const-index list get: {container.id}[{index}]")

    # Check if container is a LIST
    ctx.emitter.line(
        f"(if (result (ref null eq)) (ref.test (ref $LIST) (local.get {container_local}))"
    )
    ctx.emitter.indent += 2
    ctx.emitter.line("(then")
    ctx.emitter.indent += 2

    # Cast to LIST and get length
    ctx.emitter.line(
        f"(local.set $subscript_list_ref (ref.cast (ref $LIST) (local.get {container_local})))"
    )

    # Bounds check: just check index < len (no negative check needed)
    ctx.emitter.line(
        f"(if (result (ref null eq)) (i32.gt_s (struct.get $LIST $len (local.get $subscript_list_ref)) (i32.const {index}))"
    )
    ctx.emitter.line("  (then")
    ctx.emitter.line("    (array.get $ARRAY_ANY")
    ctx.emitter.line("      (struct.get $LIST $data (local.get $subscript_list_ref))")
    ctx.emitter.line(f"      (i32.const {index})))")
    ctx.emitter.line("  (else (ref.null eq))")
    ctx.emitter.line(")")

    ctx.emitter.indent -= 2
    ctx.emitter.line(")")
    ctx.emitter.line("(else")
    ctx.emitter.indent += 2
    # Fallback to PAIR chain
    ctx.emitter.comment("fallback: PAIR chain")
    compile_expr(container, ctx)
    ctx.emitter.emit_i32_const(index)
    ctx.emitter.emit_call("$list_get")
    ctx.emitter.indent -= 2
    ctx.emitter.line(")")
    ctx.emitter.indent -= 2
    ctx.emitter.line(")")


def _compile_nested_list_get(
    outer_container: ast.Name,
    outer_index: ast.expr,
    inner_index: ast.expr,
    ctx: CompilerContext,
) -> bool:
    """Inline nested list access like a[i][j], avoiding two function calls.

    Pattern: outer_container[outer_index][inner_index]
    Example: a[i][k] where a is a 2D list

    Returns True if successfully inlined, False to fall back to generic path.

    IMPORTANT: Uses $subscript_list_ref for outer list and $subscript_list_ref2 for inner.
    """
    if outer_container.id not in ctx.local_vars:
        return False

    container_local = ctx.local_vars[outer_container.id]
    ctx.emitter.comment(f"inline nested list get: {outer_container.id}[...][...]")

    # Check outer container is $LIST
    ctx.emitter.line(
        f"(if (result (ref null eq)) (ref.test (ref $LIST) (local.get {container_local}))"
    )
    ctx.emitter.indent += 2
    ctx.emitter.line("(then")
    ctx.emitter.indent += 2

    # --- Outer access: get row from a[i] ---
    ctx.emitter.line(
        f"(local.set $subscript_list_ref (ref.cast (ref $LIST) (local.get {container_local})))"
    )

    # Get outer index
    compile_index_value(outer_index, ctx)
    ctx.emitter.line("(local.set $idx_tmp)")

    # Get outer length
    ctx.emitter.line(
        "(local.set $len_tmp (struct.get $LIST $len (local.get $subscript_list_ref)))"
    )

    # Handle negative outer index
    ctx.emitter.line("(if (i32.lt_s (local.get $idx_tmp) (i32.const 0))")
    ctx.emitter.line(
        "  (then (local.set $idx_tmp (i32.add (local.get $len_tmp) (local.get $idx_tmp))))"
    )
    ctx.emitter.line(")")

    # Outer bounds check
    ctx.emitter.line("(if (result (ref null eq)) (i32.or")
    ctx.emitter.line("      (i32.lt_s (local.get $idx_tmp) (i32.const 0))")
    ctx.emitter.line("      (i32.ge_s (local.get $idx_tmp) (local.get $len_tmp)))")
    ctx.emitter.line("  (then (ref.null eq))")  # Out of bounds
    ctx.emitter.line("  (else")
    ctx.emitter.indent += 2

    # Get the row (inner list)
    ctx.emitter.line("(local.set $tmp")
    ctx.emitter.line("  (array.get $ARRAY_ANY")
    ctx.emitter.line("    (struct.get $LIST $data (local.get $subscript_list_ref))")
    ctx.emitter.line("    (local.get $idx_tmp)))")

    # Check row is also a $LIST
    ctx.emitter.line(
        "(if (result (ref null eq)) (ref.test (ref $LIST) (local.get $tmp))"
    )
    ctx.emitter.line("  (then")
    ctx.emitter.indent += 2

    # --- Inner access: get element from row[j] ---
    ctx.emitter.line(
        "(local.set $subscript_list_ref2 (ref.cast (ref $LIST) (local.get $tmp)))"
    )

    # Get inner index
    compile_index_value(inner_index, ctx)
    ctx.emitter.line("(local.set $idx_tmp)")

    # Get inner length
    ctx.emitter.line(
        "(local.set $len_tmp (struct.get $LIST $len (local.get $subscript_list_ref2)))"
    )

    # Handle negative inner index
    ctx.emitter.line("(if (i32.lt_s (local.get $idx_tmp) (i32.const 0))")
    ctx.emitter.line(
        "  (then (local.set $idx_tmp (i32.add (local.get $len_tmp) (local.get $idx_tmp))))"
    )
    ctx.emitter.line(")")

    # Inner bounds check and access
    ctx.emitter.line("(if (result (ref null eq)) (i32.or")
    ctx.emitter.line("      (i32.lt_s (local.get $idx_tmp) (i32.const 0))")
    ctx.emitter.line("      (i32.ge_s (local.get $idx_tmp) (local.get $len_tmp)))")
    ctx.emitter.line("  (then (ref.null eq))")
    ctx.emitter.line("  (else")
    ctx.emitter.line("    (array.get $ARRAY_ANY")
    ctx.emitter.line("      (struct.get $LIST $data (local.get $subscript_list_ref2))")
    ctx.emitter.line("      (local.get $idx_tmp))")
    ctx.emitter.line("  )")
    ctx.emitter.line(")")

    ctx.emitter.indent -= 2
    ctx.emitter.line("  )")
    ctx.emitter.line("  (else")
    # Row is not a LIST - fallback: call list_get_unified on row
    ctx.emitter.line("    (local.get $tmp)")
    compile_index_value(inner_index, ctx)
    ctx.emitter.line("    (call $list_get_unified)")
    ctx.emitter.line("  )")
    ctx.emitter.line(")")

    ctx.emitter.indent -= 2
    ctx.emitter.line("  )")
    ctx.emitter.line(")")

    ctx.emitter.indent -= 2
    ctx.emitter.line(")")
    ctx.emitter.line("(else")
    ctx.emitter.indent += 2
    # Outer container is not $LIST - full fallback
    ctx.emitter.comment("fallback: outer container not LIST")
    compile_expr(outer_container, ctx)
    compile_index_value(outer_index, ctx)
    ctx.emitter.emit_call("$list_get_unified")
    compile_index_value(inner_index, ctx)
    ctx.emitter.emit_call("$list_get_unified")
    ctx.emitter.indent -= 2
    ctx.emitter.line(")")
    ctx.emitter.indent -= 2
    ctx.emitter.line(")")

    return True


def _compile_inline_list_get(
    container: ast.Name, index: ast.expr, ctx: CompilerContext
) -> None:
    """Inline list element access, avoiding function call overhead.

    This inlines the $list_v2_get logic directly:
    1. Load list from local variable
    2. Handle negative index
    3. Bounds check
    4. Direct array access

    Saves: 2 function calls ($list_get_unified, $list_v2_get), type check overhead

    IMPORTANT: Uses $subscript_list_ref instead of $list_ref to avoid clobbering
    the loop iteration variable when inline access is used inside for loops.
    """
    container_local = ctx.local_vars[container.id]
    ctx.emitter.comment(f"inline list get: {container.id}[...]")

    # First check if it's actually a LIST (vs PAIR chain for backwards compat)
    ctx.emitter.line(
        f"(if (result (ref null eq)) (ref.test (ref $LIST) (local.get {container_local}))"
    )
    ctx.emitter.indent += 2
    ctx.emitter.line("(then")
    ctx.emitter.indent += 2

    # Inline $list_v2_get logic
    # Use $subscript_list_ref (not $list_ref) to avoid clobbering loop variables
    ctx.emitter.line(
        f"(local.set $subscript_list_ref (ref.cast (ref $LIST) (local.get {container_local})))"
    )

    # Get index value
    compile_index_value(index, ctx)
    ctx.emitter.line("(local.set $idx_tmp)")

    # Get length
    ctx.emitter.line(
        "(local.set $len_tmp (struct.get $LIST $len (local.get $subscript_list_ref)))"
    )

    # Handle negative index: if idx < 0, idx = len + idx
    ctx.emitter.line("(if (i32.lt_s (local.get $idx_tmp) (i32.const 0))")
    ctx.emitter.line(
        "  (then (local.set $idx_tmp (i32.add (local.get $len_tmp) (local.get $idx_tmp))))"
    )
    ctx.emitter.line(")")

    # Bounds check: if idx < 0 || idx >= len, return null
    ctx.emitter.line("(if (result (ref null eq)) (i32.or")
    ctx.emitter.line("      (i32.lt_s (local.get $idx_tmp) (i32.const 0))")
    ctx.emitter.line("      (i32.ge_s (local.get $idx_tmp) (local.get $len_tmp)))")
    ctx.emitter.line("  (then (ref.null eq))")
    ctx.emitter.line("  (else")
    ctx.emitter.line("    (array.get $ARRAY_ANY")
    ctx.emitter.line("      (struct.get $LIST $data (local.get $subscript_list_ref))")
    ctx.emitter.line("      (local.get $idx_tmp))")
    ctx.emitter.line("  )")
    ctx.emitter.line(")")

    ctx.emitter.indent -= 2
    ctx.emitter.line(")")
    ctx.emitter.line("(else")
    ctx.emitter.indent += 2
    # Fallback to PAIR chain
    ctx.emitter.comment("fallback: PAIR chain")
    compile_expr(container, ctx)
    compile_index_value(index, ctx)
    ctx.emitter.emit_call("$list_get")
    ctx.emitter.indent -= 2
    ctx.emitter.line(")")
    ctx.emitter.indent -= 2
    ctx.emitter.line(")")


def _compile_inline_list_set(
    container: ast.Name, index: ast.expr, value: ast.expr, ctx: CompilerContext
) -> bool:
    """Inline list element assignment, avoiding function call overhead.

    This inlines the $list_set_unified logic directly:
    1. Check container is LIST (fallback to function call if not)
    2. Handle negative index
    3. Bounds check
    4. Direct array set

    Returns True if inlined, False if fallback is needed.

    IMPORTANT: Uses $subscript_list_ref instead of $list_ref to avoid clobbering
    the loop iteration variable when inline access is used inside for loops.
    """
    container_local = ctx.local_vars[container.id]
    ctx.emitter.comment(f"inline list set: {container.id}[...] = ...")

    # Compile value BEFORE the type check (needed by both branches)
    compile_expr(value, ctx)
    if ctx.has_native_value:
        ctx.emitter.emit_ref_i31()
        ctx.clear_native_value()
    ctx.emitter.line("(local.set $tmp2)")

    # First check if it's actually a LIST
    ctx.emitter.line(f"(if (ref.test (ref $LIST) (local.get {container_local}))")
    ctx.emitter.indent += 2
    ctx.emitter.line("(then")
    ctx.emitter.indent += 2

    # Inline list set logic
    # Use $subscript_list_ref (not $list_ref) to avoid clobbering loop variables
    ctx.emitter.line(
        f"(local.set $subscript_list_ref (ref.cast (ref $LIST) (local.get {container_local})))"
    )

    # Get index value
    compile_index_value(index, ctx)
    ctx.emitter.line("(local.set $idx_tmp)")

    # Get length
    ctx.emitter.line(
        "(local.set $len_tmp (struct.get $LIST $len (local.get $subscript_list_ref)))"
    )

    # Handle negative index: if idx < 0, idx = len + idx
    ctx.emitter.line("(if (i32.lt_s (local.get $idx_tmp) (i32.const 0))")
    ctx.emitter.line(
        "  (then (local.set $idx_tmp (i32.add (local.get $len_tmp) (local.get $idx_tmp))))"
    )
    ctx.emitter.line(")")

    # Bounds check: if idx >= 0 && idx < len, do the set
    ctx.emitter.line("(if (i32.and")
    ctx.emitter.line("      (i32.ge_s (local.get $idx_tmp) (i32.const 0))")
    ctx.emitter.line("      (i32.lt_s (local.get $idx_tmp) (local.get $len_tmp)))")
    ctx.emitter.line("  (then")
    ctx.emitter.line("    (array.set $ARRAY_ANY")
    ctx.emitter.line("      (struct.get $LIST $data (local.get $subscript_list_ref))")
    ctx.emitter.line("      (local.get $idx_tmp)")
    ctx.emitter.line("      (local.get $tmp2))")
    ctx.emitter.line("  )")
    ctx.emitter.line(")")

    ctx.emitter.indent -= 2
    ctx.emitter.line(")")
    ctx.emitter.line("(else")
    ctx.emitter.indent += 2

    # Fallback for non-LIST containers (PAIR chains)
    ctx.emitter.comment("fallback: use list_set_unified")
    ctx.emitter.line(f"(local.get {container_local})")
    # Need to compute index again for the fallback (uses $idx_tmp from inline path)
    compile_index_value(index, ctx)
    ctx.emitter.line("(local.get $tmp2)")  # Value was pre-computed
    ctx.emitter.emit_call("$list_set_unified")
    # Note: $list_set_unified has no return value

    ctx.emitter.indent -= 2
    ctx.emitter.line(")")
    ctx.emitter.indent -= 2
    ctx.emitter.line(")")

    # Return the container reference (for variable update)
    ctx.emitter.line(f"(local.get {container_local})")
    return True


def compile_subscript(
    container: ast.expr, index: ast.expr, ctx: CompilerContext
) -> None:
    """Compile subscript access."""

    # Check for slice
    if isinstance(index, ast.Slice):
        compile_slice(container, index, ctx)
        return

    # Try type-specialized access for known container types
    container_type = ctx.get_expr_type(container)
    index_type = ctx.get_expr_type(index)

    # Nested list access pattern: a[i][k] where a is a local variable
    # This inlines two list accesses into a single optimized block
    # Only applies when outer container is known to be a list type
    if (
        isinstance(container, ast.Subscript)
        and isinstance(container.value, ast.Name)
        and container.value.id in ctx.local_vars
        and not isinstance(container.slice, ast.Slice)  # Not a slice
        and isinstance(ctx.get_expr_type(container.value), ListType)  # Outer is list
    ):
        if _compile_nested_list_get(container.value, container.slice, index, ctx):
            return

    # Constant small-index optimization for patterns like x[0], x[1], x[2]
    # This is very common in nbody (47 occurrences) and other benchmarks
    # Only applies when container is known to be a list
    if (
        isinstance(container_type, ListType)
        and isinstance(container, ast.Name)
        and container.id in ctx.local_vars
        and isinstance(index, ast.Constant)
        and isinstance(index.value, int)
        and 0 <= index.value <= 15  # Small positive indices only
    ):
        _compile_const_index_list_get(container, index.value, ctx)
        return

    # Check for safe bounds optimization (loop variable known to be in bounds)
    if (
        isinstance(container, ast.Name)
        and isinstance(index, ast.Name)
        and index.id in ctx.safe_bounds
    ):
        safe_container_name, safe_container_local = ctx.safe_bounds[index.id]
        if container.id == safe_container_name:
            # Safe bounds: skip bounds check, direct array access
            ctx.emitter.comment(
                f"subscript (safe bounds: {index.id} in {container.id})"
            )
            ctx.emitter.line(
                f"(if (ref.test (ref $LIST) (local.get {safe_container_local}))"
            )
            ctx.emitter.line("  (then")
            ctx.emitter.comment("direct array access (no bounds check)")
            ctx.emitter.line(
                f"    (local.set $list_ref (ref.cast (ref $LIST) (local.get {safe_container_local})))"
            )
            compile_index_value(index, ctx)
            ctx.emitter.line(
                "    (array.get $ARRAY_ANY (struct.get $LIST $data (local.get $list_ref)))"
            )
            ctx.emitter.line("  )")
            ctx.emitter.line("  (else")
            ctx.emitter.comment("fallback to standard get")
            compile_expr(container, ctx)
            compile_index_value(index, ctx)
            ctx.emitter.emit_call("$list_get_unified")
            ctx.emitter.line("  )")
            ctx.emitter.line(")")
            return

    # Optimized paths for list access
    match (container_type, index_type):
        case (ListType(), IntType() | I32Type() | I64Type()):
            # Check if we can inline the array access (container is a local variable)
            if isinstance(container, ast.Name) and container.id in ctx.local_vars:
                _compile_inline_list_get(container, index, ctx)
                return
            # Fallback to function call
            ctx.emitter.comment("subscript (optimized: list[int])")
            compile_expr(container, ctx)
            compile_index_value(index, ctx)
            ctx.emitter.emit_call("$list_get_unified")
            return

        case (ListType(), _):
            # Check if we can inline the array access
            if isinstance(container, ast.Name) and container.id in ctx.local_vars:
                _compile_inline_list_get(container, index, ctx)
                return
            ctx.emitter.comment("subscript (optimized: list)")
            compile_expr(container, ctx)
            compile_index_value(index, ctx)
            ctx.emitter.emit_call("$list_get_unified")
            return

    # Generic path: runtime dispatch
    ctx.emitter.comment("subscript")
    compile_expr(container, ctx)
    ctx.emitter.line("(local.set $tmp)  ;; save container")

    # Check if container is OBJECT with __getitem__
    ctx.emitter.line(
        "(if (result (ref null eq)) (ref.test (ref $OBJECT) (local.get $tmp))"
    )
    ctx.emitter.line("  (then")
    ctx.emitter.comment("OBJECT: call __getitem__(self, key)")
    ctx.emitter.line("    (local.get $tmp)  ;; self")
    compile_expr(index, ctx)
    # Box native value if needed (runtime expects boxed)
    if ctx.has_native_value:
        ctx.emitter.emit_ref_i31()
        ctx.clear_native_value()
    ctx.emitter.emit_null_eq()
    ctx.emitter.emit_struct_new("$PAIR")
    ctx.emitter.line("    (struct.new $PAIR)  ;; PAIR(self, PAIR(key, null))")
    ctx.emitter.line("    (local.get $tmp)")
    ctx.emitter.emit_string("__getitem__")
    ctx.emitter.emit_call("$object_getattr")
    ctx.emitter.emit_ref_cast("$CLOSURE")
    ctx.emitter.line("    (local.tee $tmp2)")
    ctx.emitter.emit_ref_cast("$CLOSURE")
    ctx.emitter.line("    (struct.get $CLOSURE 0)  ;; env")
    ctx.emitter.emit_local_get("$tmp2")
    ctx.emitter.emit_ref_cast("$CLOSURE")
    ctx.emitter.line("    (struct.get $CLOSURE 1)  ;; func index")
    ctx.emitter.line("    (call_indirect (type $FUNC))")
    ctx.emitter.line("  )")
    ctx.emitter.line("  (else")
    ctx.emitter.comment("Not OBJECT: use subscript_get")
    ctx.emitter.emit_local_get("$tmp")
    compile_expr(index, ctx)
    # Box native value if needed (runtime expects boxed)
    if ctx.has_native_value:
        ctx.emitter.emit_ref_i31()
        ctx.clear_native_value()
    ctx.emitter.emit_call("$subscript_get")
    ctx.emitter.line("  )")
    ctx.emitter.line(")")


def _compile_slice_index(index: ast.expr | None, default: int, ctx: CompilerContext) -> None:
    """Compile a slice index expression to i32.

    Handles both boxed (ref i31) and native (i32) values correctly.
    """
    if index is None:
        ctx.emitter.emit_i32_const(default)
    else:
        compile_expr(index, ctx)
        if ctx.has_native_value:
            # Value is already a native i32, no need to unbox
            ctx.clear_native_value()
        else:
            # Value is boxed, unbox it
            ctx.emitter.emit_i31_get_s()


def compile_slice(container: ast.expr, slc: ast.Slice, ctx: CompilerContext) -> None:
    """Compile slice access.

    Uses -999999 as sentinel for "use default" values.
    The helper function handles the defaults differently based on step sign.
    """

    ctx.emitter.comment("slice")
    compile_expr(container, ctx)

    # Use -999999 as sentinel for "use default" - helper handles positive/negative step
    _compile_slice_index(slc.lower, -999999, ctx)
    _compile_slice_index(slc.upper, -999999, ctx)
    _compile_slice_index(slc.step, 1, ctx)

    ctx.emitter.emit_call("$slice")


def compile_subscript_assignment(
    target: ast.Subscript, value: ast.expr, ctx: CompilerContext
) -> None:
    """Compile subscript assignment."""

    if isinstance(target.slice, ast.Slice):
        _compile_slice_assignment(target, value, ctx)
        return

    # Try type-specialized assignment for known container types
    container_type = ctx.get_expr_type(target.value)
    index_type = ctx.get_expr_type(target.slice)

    # Optimized paths for list assignment (no early return - must fall through to post-processing)
    match (container_type, index_type):
        case (ListType(), IntType() | I32Type() | I64Type()):
            # Try inline list set for local variables
            if isinstance(target.value, ast.Name) and target.value.id in ctx.local_vars:
                _compile_inline_list_set(target.value, target.slice, value, ctx)
            else:
                # Fallback to function call for non-local containers
                ctx.emitter.comment("subscript assignment (optimized: list[int])")
                compile_expr(target.value, ctx)
                ctx.emitter.line("(local.tee $tmp)")
                compile_index_value(target.slice, ctx)
                compile_expr(value, ctx)
                if ctx.has_native_value:
                    ctx.emitter.emit_ref_i31()
                    ctx.clear_native_value()
                ctx.emitter.emit_call("$list_set_unified")
                ctx.emitter.emit_local_get("$tmp")

        case (ListType(), _):
            # Try inline list set for local variables
            if isinstance(target.value, ast.Name) and target.value.id in ctx.local_vars:
                _compile_inline_list_set(target.value, target.slice, value, ctx)
            else:
                ctx.emitter.comment("subscript assignment (optimized: list)")
                compile_expr(target.value, ctx)
                ctx.emitter.line("(local.tee $tmp)")
                compile_index_value(target.slice, ctx)
                compile_expr(value, ctx)
                if ctx.has_native_value:
                    ctx.emitter.emit_ref_i31()
                    ctx.clear_native_value()
                ctx.emitter.emit_call("$list_set_unified")
                ctx.emitter.emit_local_get("$tmp")

        case _:
            # Generic path: runtime dispatch
            ctx.emitter.comment("subscript assignment")

            compile_expr(target.value, ctx)
            ctx.emitter.line("(local.set $tmp)  ;; save container")

            ctx.emitter.line(
                "(if (result (ref null eq)) (ref.test (ref $OBJECT) (local.get $tmp))"
            )
            ctx.emitter.line("  (then")
            ctx.emitter.comment("OBJECT: call __setitem__(self, key, value)")
            ctx.emitter.line("    (local.get $tmp)  ;; self")
            compile_expr(target.slice, ctx)
            # Box native slice if needed
            if ctx.has_native_value:
                ctx.emitter.emit_ref_i31()
                ctx.clear_native_value()
            compile_expr(value, ctx)
            # Box native value if needed
            if ctx.has_native_value:
                ctx.emitter.emit_ref_i31()
                ctx.clear_native_value()
            ctx.emitter.emit_null_eq()
            ctx.emitter.emit_struct_new("$PAIR")
            ctx.emitter.emit_struct_new("$PAIR")
            ctx.emitter.line("    (struct.new $PAIR)  ;; PAIR(self, ...)")
            ctx.emitter.line("    (local.get $tmp)")
            ctx.emitter.emit_string("__setitem__")
            ctx.emitter.emit_call("$object_getattr")
            ctx.emitter.emit_ref_cast("$CLOSURE")
            ctx.emitter.line("    (local.tee $tmp2)")
            ctx.emitter.emit_ref_cast("$CLOSURE")
            ctx.emitter.line("    (struct.get $CLOSURE 0)  ;; env")
            ctx.emitter.emit_local_get("$tmp2")
            ctx.emitter.emit_ref_cast("$CLOSURE")
            ctx.emitter.line("    (struct.get $CLOSURE 1)  ;; func index")
            ctx.emitter.line("    (call_indirect (type $FUNC))")
            ctx.emitter.line("    drop  ;; __setitem__ returns None typically")
            ctx.emitter.line("    (local.get $tmp)  ;; return original object")
            ctx.emitter.line("  )")
            ctx.emitter.line("  (else")
            ctx.emitter.comment("Not OBJECT: use container_set")
            ctx.emitter.emit_local_get("$tmp")
            compile_expr(target.slice, ctx)
            # Box native slice if needed
            if ctx.has_native_value:
                ctx.emitter.emit_ref_i31()
                ctx.clear_native_value()
            compile_expr(value, ctx)
            # Box native value if needed
            if ctx.has_native_value:
                ctx.emitter.emit_ref_i31()
                ctx.clear_native_value()
            ctx.emitter.emit_call("$container_set")
            ctx.emitter.line("  )")
            ctx.emitter.line(")")

    match target.value:
        case ast.Name(id=name) if name in ctx.local_vars:
            # For module-level variables, update both local and global
            if name in ctx.global_vars and len(ctx.lexical_env.frames) <= 1:
                ctx.emitter.line(
                    f"(local.tee {ctx.local_vars[name]})  ;; update container"
                )
                ctx.emitter.line(f"(global.set $global_{name})")
            else:
                ctx.emitter.line(
                    f"(local.set {ctx.local_vars[name]})  ;; update container"
                )
        case ast.Attribute(value=obj, attr=attr):
            ctx.emitter.line("(local.set $tmp)  ;; save updated container")
            compile_expr(obj, ctx)
            ctx.emitter.emit_string(attr)
            ctx.emitter.emit_local_get("$tmp")
            ctx.emitter.emit_call("$object_setattr")
            ctx.emitter.emit_drop()
        case _:
            ctx.emitter.emit_drop()


def _compile_slice_assignment(
    target: ast.Subscript, value: ast.expr, ctx: CompilerContext
) -> None:
    """Compile slice assignment."""

    ctx.emitter.comment("slice assignment")
    slc = target.slice
    assert isinstance(slc, ast.Slice)

    compile_expr(target.value, ctx)

    if slc.lower:
        compile_expr(slc.lower, ctx)
        ctx.emitter.emit_i31_get_s()
    else:
        ctx.emitter.emit_i32_const(0)

    if slc.upper:
        compile_expr(slc.upper, ctx)
        ctx.emitter.emit_i31_get_s()
    else:
        ctx.emitter.emit_i32_const(-999999)

    compile_expr(value, ctx)
    ctx.emitter.emit_call("$list_slice_set")


def compile_subscript_delete(target: ast.Subscript, ctx: CompilerContext) -> None:
    """Compile subscript deletion (del obj[key] or del obj[slice])."""

    if isinstance(target.slice, ast.Slice):
        _compile_slice_delete(target, ctx)
    else:
        # Simple index deletion
        ctx.emitter.comment("del subscript")
        compile_expr(target.value, ctx)
        compile_expr(target.slice, ctx)
        ctx.emitter.emit_call("$subscript_delete")


def _compile_slice_delete(target: ast.Subscript, ctx: CompilerContext) -> None:
    """Compile slice deletion (del lst[start:stop])."""

    ctx.emitter.comment("slice delete")
    slc = target.slice
    assert isinstance(slc, ast.Slice)

    compile_expr(target.value, ctx)

    if slc.lower:
        compile_expr(slc.lower, ctx)
        ctx.emitter.emit_i31_get_s()
    else:
        ctx.emitter.emit_i32_const(0)

    if slc.upper:
        compile_expr(slc.upper, ctx)
        ctx.emitter.emit_i31_get_s()
    else:
        ctx.emitter.emit_i32_const(-999999)

    ctx.emitter.emit_call("$list_slice_delete")
