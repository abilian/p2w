"""Function and method call compilation."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import TYPE_CHECKING

from p2w.compiler.codegen.expressions import compile_expr
from p2w.compiler.codegen.js_interop import (
    compile_js_method_call,
    is_js_method_call,
)
from p2w.wat.builtins import DIRECT_BUILTINS

if TYPE_CHECKING:
    from p2w.compiler.context import CompilerContext


# Enable direct builtin calls optimization
# This avoids PAIR chain allocation for common single-arg builtins
ENABLE_DIRECT_BUILTIN_CALLS = True

# Enable direct user function calls optimization
# This bypasses $call_or_instantiate for statically-known function targets
ENABLE_DIRECT_USER_CALLS = True


# =============================================================================
# Call Target Analysis
# =============================================================================


@dataclass
class CallTarget:
    """Base class for call target analysis."""


@dataclass
class DirectUserCall(CallTarget):
    """Direct call to a user-defined function."""

    func_name: str
    table_idx: int  # Index in WASM function table


@dataclass
class DirectBuiltinCall(CallTarget):
    """Direct call to a builtin function."""

    func_name: str
    wat_func: str  # WAT function name (e.g., "$len_direct")
    arity: int


@dataclass
class DynamicCall(CallTarget):
    """Dynamic call via $call_or_instantiate."""


@dataclass
class SlottedClassInstantiation(CallTarget):
    """Direct instantiation of a slotted class."""

    class_name: str
    slots: list[str]


def analyze_call_target(func: ast.expr, ctx: CompilerContext) -> CallTarget:
    """Analyze a call target to determine the best call strategy.

    Returns:
        CallTarget indicating how to compile the call.
    """
    match func:
        case ast.Name(id=name):
            pass
        case _:
            # Method calls, attribute access, etc. - use dynamic dispatch
            return DynamicCall()

    # Check for direct builtin calls first
    if ENABLE_DIRECT_BUILTIN_CALLS and name in DIRECT_BUILTINS:
        wat_func, arity = DIRECT_BUILTINS[name]
        return DirectBuiltinCall(name, wat_func, arity)

    # Check for user-defined functions
    if ENABLE_DIRECT_USER_CALLS and name in ctx.func_table:
        table_idx = ctx.func_table[name]
        return DirectUserCall(name, table_idx)

    # Check for slotted class instantiation
    if name in ctx.slotted_classes:
        slots = ctx.slotted_classes[name]
        return SlottedClassInstantiation(name, slots)

    # Check if it's a known global (function reference stored in global)
    # This catches functions that were defined but maybe not in func_table yet
    if name in ctx.global_vars and name not in ctx.local_vars:
        # It's a global variable - could be a function, but we don't know
        # the table index, so fall back to dynamic call
        pass

    return DynamicCall()


def _compile_direct_user_call(
    func_name: str,
    table_idx: int,
    args: list[ast.expr],
    ctx: CompilerContext,
) -> None:
    """Compile a direct call to a user-defined function.

    This bypasses $call_or_instantiate dispatch for statically-known targets.
    Benefits:
    - No need to load the closure and check if it's a class
    - No "__init__" string allocation
    - Direct call_indirect with known table index

    Phase 4.1 enhancement: If a specialized version exists, use direct call
    with arguments on the stack (no PAIR chain).

    Args:
        func_name: Name of the function being called
        table_idx: WASM function table index
        args: List of argument expressions
        ctx: Compiler context
    """
    # Phase 4.1: Check for specialized function with direct parameters
    if func_name in ctx.spec_functions:
        spec_name, arity = ctx.spec_functions[func_name]
        if len(args) == arity:
            ctx.emitter.comment(f"spec call to '{func_name}' (direct params)")

            # Compile arguments directly on the stack (no PAIR chain!)
            for arg in args:
                compile_expr(arg, ctx)

            # Pass null environment
            ctx.emitter.line("(ref.null $ENV)")

            # Direct call to specialized function
            ctx.emitter.line(f"(call {spec_name})")
            return

    # Fallback: PAIR chain based call
    ctx.emitter.comment(f"direct call to '{func_name}'")

    # Build PAIR chain for arguments (same as dynamic call)
    if not args:
        ctx.emitter.emit_null_eq()
    else:
        for arg in args:
            compile_expr(arg, ctx)
        ctx.emitter.emit_null_eq()
        for _ in range(len(args)):
            ctx.emitter.emit_struct_new("$PAIR")

    # Pass null environment (module-level functions don't need captured env)
    ctx.emitter.line("(ref.null $ENV)")

    # Direct call via function table
    ctx.emitter.line(f"(i32.const {table_idx})")
    ctx.emitter.line("(call_indirect (type $FUNC))")


# String methods
STRING_METHODS = {
    "upper": "$string_upper",
    "lower": "$string_lower",
    "capitalize": "$string_capitalize",
    "title": "$string_title",
    "swapcase": "$string_swapcase",
    "strip": "$string_strip",
    "lstrip": "$string_lstrip",
    "rstrip": "$string_rstrip",
    "startswith": "$string_startswith",
    "endswith": "$string_endswith",
    "find": "$string_find",
    "replace": "$string_replace",
    "split": "$string_split",
    "join": "$string_join",
    "count": "$string_count",
    "isdigit": "$string_isdigit",
    "isalpha": "$string_isalpha",
    "isalnum": "$string_isalnum",
    "isspace": "$string_isspace",
    "islower": "$string_islower",
    "isupper": "$string_isupper",
    "rfind": "$string_rfind",
    "ljust": "$string_ljust",
    "rjust": "$string_rjust",
    "center": "$string_center",
    "zfill": "$string_zfill",
}

# List methods
LIST_METHODS = {
    "append": "$list_append",
    "pop": "$list_pop",
    "insert": "$list_insert",
    "remove": "$list_remove",
    "index": "$list_index",
    "count": "$list_count",
    "reverse": "$list_reverse_inplace",
    "sort": "$list_sort_inplace",
    "copy": "$list_copy",
    "clear": "$list_clear",
    "extend": "$list_extend",
}

# Dict methods
DICT_METHODS = {
    "keys": "$dict_keys",
    "values": "$dict_values",
    "items": "$dict_items",
    "get": "$dict_get_default",
    "pop": "$dict_pop",
    "update": "$dict_update",
    "clear": "$dict_clear",
    "copy": "$dict_copy",
}

# Set methods
SET_METHODS = {
    "add": "$set_add",
    "remove": "$set_remove",
    "discard": "$set_discard",
}


def compile_call(
    func: ast.expr,
    args: list[ast.expr],
    keywords: list[ast.keyword] | None,
    ctx: CompilerContext,
) -> None:
    """Compile function call."""

    keywords = keywords or []

    # Method calls
    if isinstance(func, ast.Attribute):
        compile_method_call(func.value, func.attr, args, keywords, ctx)
        return

    # Direct builtin calls optimization: avoid PAIR chain for single-arg builtins
    if (
        ENABLE_DIRECT_BUILTIN_CALLS
        and isinstance(func, ast.Name)
        and func.id in DIRECT_BUILTINS
        and not keywords  # No keyword args
    ):
        direct_func, expected_arity = DIRECT_BUILTINS[func.id]
        if len(args) == expected_arity:
            ctx.emitter.comment(f"direct builtin: {func.id}")
            for arg in args:
                compile_expr(arg, ctx)
            ctx.emitter.emit_call(direct_func)
            return

    # dict() with kwargs
    if isinstance(func, ast.Name) and func.id == "dict" and keywords:
        _compile_dict_with_kwargs(args, keywords, ctx)
        return

    # print() with sep= and/or end= keyword arguments
    if isinstance(func, ast.Name) and func.id == "print" and keywords:
        sep_kw = next((kw for kw in keywords if kw.arg == "sep"), None)
        end_kw = next((kw for kw in keywords if kw.arg == "end"), None)
        _compile_print_with_kwargs(args, sep_kw, end_kw, ctx)
        return

    # enumerate() with start= keyword argument
    if isinstance(func, ast.Name) and func.id == "enumerate" and keywords:
        start_kw = next((kw for kw in keywords if kw.arg == "start"), None)
        if start_kw and len(args) == 1:
            ctx.emitter.comment("enumerate with start kwarg")
            compile_expr(args[0], ctx)  # iterable
            compile_expr(start_kw.value, ctx)  # start value
            ctx.emitter.emit_null_eq()
            ctx.emitter.emit_struct_new("$PAIR")
            ctx.emitter.emit_struct_new("$PAIR")
            ctx.emitter.line("(ref.null $ENV)")
            ctx.emitter.emit_call("$enumerate")
            return

    # sorted() with key and/or reverse keyword
    if isinstance(func, ast.Name) and func.id == "sorted":
        has_reverse = any(
            kw.arg == "reverse"
            and isinstance(kw.value, ast.Constant)
            and kw.value.value is True
            for kw in keywords
        )
        key_kw = next((kw for kw in keywords if kw.arg == "key"), None)

        if key_kw:
            # sorted with key function
            ctx.emitter.comment("sorted with key function")
            # Compile the iterable argument
            if args:
                compile_expr(args[0], ctx)
            else:
                ctx.emitter.emit_null_eq()
            # Compile the key function
            compile_expr(key_kw.value, ctx)
            ctx.emitter.emit_call("$sorted_with_key")
        else:
            # sorted without key function
            # Compile the iterable argument
            if args:
                compile_expr(args[0], ctx)
                ctx.emitter.emit_null_eq()
                ctx.emitter.emit_struct_new("$PAIR")
            else:
                ctx.emitter.emit_null_eq()
            ctx.emitter.line("(ref.null $ENV)")
            ctx.emitter.emit_call("$sorted")

        if has_reverse:
            ctx.emitter.emit_call("$list_reverse")
        return

    # super() - handle both no-argument and explicit (Class, self) forms
    if isinstance(func, ast.Name) and func.id == "super":
        if not args:
            # super() with no arguments - implicitly pass self and current class
            # IMPORTANT: We must use the LEXICAL class (ctx.current_class), not
            # the runtime class of self. Otherwise 3-level inheritance breaks:
            # C -> B -> A: when B.__init__ calls super(), we need SUPER(A, self)
            # not SUPER(B, self) which would happen if we used self's runtime class.
            ctx.emitter.comment("super() with no arguments")
            if "self" in ctx.local_vars and ctx.current_class:
                # Use explicit form with lexical class name
                ctx.emitter.emit_string(ctx.current_class)
                ctx.emitter.emit_local_get(ctx.local_vars["self"])
                ctx.emitter.emit_call("$super_explicit")
                return
            if "self" in ctx.local_vars:
                # Fallback for classes without ctx.current_class set
                ctx.emitter.emit_local_get(ctx.local_vars["self"])
                ctx.emitter.emit_null_eq()
                ctx.emitter.emit_struct_new("$PAIR")
                ctx.emitter.line("(ref.null $ENV)")
                ctx.emitter.emit_call("$super")
                return
            # Fallback: return null if not in a method context
            ctx.emitter.emit_null_eq()
            return
        if len(args) == 2:
            # super(Class, self) - explicit form
            # The Class argument determines which class's parent to look up
            # We pass the class NAME as a string to resolve at runtime
            ctx.emitter.comment("super(Class, self) explicit form")
            # First arg should be a class name - emit it as a string
            if isinstance(args[0], ast.Name):
                ctx.emitter.emit_string(args[0].id)
            else:
                # Fallback: try to compile as expression
                compile_expr(args[0], ctx)
            compile_expr(args[1], ctx)  # Compile self (second argument)
            ctx.emitter.emit_call("$super_explicit")
            return

    # Check for **kwargs in the call
    kwargs_spread = next((kw for kw in keywords if kw.arg is None), None)
    if kwargs_spread and isinstance(func, ast.Name) and func.id in ctx.func_signatures:
        _compile_call_with_kwargs(func.id, args, keywords, ctx)
        return

    # Analyze call target for optimization
    target = analyze_call_target(func, ctx)

    # Direct call to user-defined function (Phase 2 optimization)
    # Skips $call_or_instantiate dispatch for known function targets
    if isinstance(target, DirectUserCall) and not keywords:
        has_starred = any(isinstance(arg, ast.Starred) for arg in args)
        if not has_starred:
            _compile_direct_user_call(target.func_name, target.table_idx, args, ctx)
            return

    # Slotted class instantiation (struct-based, no hash table)
    if isinstance(target, SlottedClassInstantiation) and not keywords:
        has_starred = any(isinstance(arg, ast.Starred) for arg in args)
        if not has_starred:
            _compile_slotted_class_instantiation(
                target.class_name, target.slots, args, ctx
            )
            return

    # General function call
    ctx.emitter.comment("call function or instantiate class")
    compile_expr(func, ctx)
    ctx.emitter.emit_string("__init__")

    # Check for starred expressions in args
    has_starred = any(isinstance(arg, ast.Starred) for arg in args)

    if not args:
        ctx.emitter.emit_null_eq()
    elif not has_starred:
        # Simple case: no starred expressions
        for arg in args:
            compile_expr(arg, ctx)
        ctx.emitter.emit_null_eq()
        for _ in range(len(args)):
            ctx.emitter.emit_struct_new("$PAIR")
    else:
        # Complex case: starred expressions - build list incrementally
        ctx.emitter.comment("function call with starred args")
        ctx.emitter.emit_null_eq()  # Start with empty list

        for arg in args:
            if isinstance(arg, ast.Starred):
                # Starred: compile iterable and concat
                compile_expr(arg.value, ctx)
                ctx.emitter.emit_call("$list_concat")
            else:
                # Regular arg: wrap in single-element list and concat
                compile_expr(arg, ctx)
                ctx.emitter.emit_null_eq()
                ctx.emitter.emit_struct_new("$PAIR")
                ctx.emitter.emit_call("$list_concat")

    ctx.emitter.line("(ref.null $ENV)")
    ctx.emitter.emit_call("$call_or_instantiate")


def compile_method_call(
    obj: ast.expr,
    method: str,
    args: list[ast.expr],
    keywords: list[ast.keyword],
    ctx: CompilerContext,
) -> None:
    """Compile method call."""

    # Handle JS-specific methods that work on any object (e.g., event callbacks)
    if ctx.js_imported and method == "preventDefault":
        ctx.emitter.comment("js: event.preventDefault()")
        compile_expr(obj, ctx)
        ctx.emitter.emit_call("$js_event_prevent_default")
        return

    # Check for JS object method calls first
    if ctx.js_imported and is_js_method_call(obj, ctx):
        compile_js_method_call(obj, method, args, ctx)
        return

    # Check for slotted instance method calls
    # For slotted classes, method lookup goes directly to the class
    if isinstance(obj, ast.Name):
        class_name = ctx.get_slotted_instance_class(obj.id)
        if class_name:
            _compile_slotted_method_call(obj, class_name, method, args, ctx)
            return

    ctx.emitter.comment(f"method call: .{method}()")

    # Handle special cases first
    if method == "pop":
        _compile_pop_method(obj, args, ctx)
        return

    if method == "index" and len(args) >= 2:
        compile_expr(obj, ctx)
        compile_expr(args[0], ctx)
        compile_expr(args[1], ctx)
        ctx.emitter.emit_call("$list_index_from")
        return

    if method == "sort":
        has_reverse = any(
            kw.arg == "reverse"
            and isinstance(kw.value, ast.Constant)
            and kw.value.value is True
            for kw in keywords
        )
        key_kw = next((kw for kw in keywords if kw.arg == "key"), None)

        if key_kw:
            # sort with key function
            ctx.emitter.comment("list.sort with key function")
            compile_expr(obj, ctx)
            compile_expr(key_kw.value, ctx)
            ctx.emitter.emit_call("$list_sort_with_key")
        else:
            # sort without key function
            compile_expr(obj, ctx)
            ctx.emitter.emit_call("$list_sort_inplace")

        if has_reverse:
            ctx.emitter.emit_call("$list_reverse_inplace")
        return

    if method == "count":
        compile_expr(obj, ctx)
        compile_expr(args[0], ctx)
        ctx.emitter.emit_call("$method_count")
        return

    if method == "to_bytes":
        # int.to_bytes(length, byteorder, signed=False)
        ctx.emitter.comment("int.to_bytes")
        compile_expr(obj, ctx)  # The integer value
        compile_expr(args[0], ctx)  # length
        # Check byteorder (second arg)
        is_little = isinstance(args[1], ast.Constant) and args[1].value == "little"
        # Check signed keyword
        is_signed = any(
            kw.arg == "signed"
            and isinstance(kw.value, ast.Constant)
            and kw.value.value is True
            for kw in keywords
        )
        if is_little and is_signed:
            ctx.emitter.emit_call("$int_to_bytes_little_signed")
        elif is_little:
            ctx.emitter.emit_call("$int_to_bytes_little")
        elif is_signed:
            ctx.emitter.emit_call("$int_to_bytes_big_signed")
        else:
            ctx.emitter.emit_call("$int_to_bytes_big")
        return

    if method == "from_bytes":
        # int.from_bytes(data, byteorder, signed=False)
        # Called as int.from_bytes(...), but we detect it on the method name
        ctx.emitter.comment("int.from_bytes")
        compile_expr(args[0], ctx)  # The bytes data
        # Check byteorder (second arg)
        is_little = isinstance(args[1], ast.Constant) and args[1].value == "little"
        # Check signed keyword
        is_signed = any(
            kw.arg == "signed"
            and isinstance(kw.value, ast.Constant)
            and kw.value.value is True
            for kw in keywords
        )
        if is_little and is_signed:
            ctx.emitter.emit_call("$bytes_to_int_little_signed")
        elif is_little:
            ctx.emitter.emit_call("$bytes_to_int_little")
        elif is_signed:
            ctx.emitter.emit_call("$bytes_to_int_big_signed")
        else:
            ctx.emitter.emit_call("$bytes_to_int_big")
        return

    if method == "get":
        compile_expr(obj, ctx)
        compile_expr(args[0], ctx)
        if len(args) >= 2:
            compile_expr(args[1], ctx)
        else:
            ctx.emitter.emit_null_eq()
        ctx.emitter.emit_call("$dict_get_default")
        return

    if method == "setdefault":
        compile_expr(obj, ctx)
        compile_expr(args[0], ctx)
        if len(args) >= 2:
            compile_expr(args[1], ctx)
        else:
            ctx.emitter.emit_null_eq()
        ctx.emitter.emit_call("$dict_setdefault")
        if isinstance(obj, ast.Name) and obj.id in ctx.local_vars:
            var_name = obj.id
            # For module-level variables, update both local and global
            if var_name in ctx.global_vars and len(ctx.lexical_env.frames) <= 1:
                ctx.emitter.line(
                    f"(local.tee {ctx.local_vars[var_name]})  ;; update dict"
                )
                ctx.emitter.line(f"(global.set $global_{var_name})")
            else:
                ctx.emitter.line(
                    f"(local.set {ctx.local_vars[var_name]})  ;; update dict"
                )
        else:
            ctx.emitter.line("drop  ;; discard updated dict")
        return

    if method in {"strip", "lstrip", "rstrip"}:
        compile_expr(obj, ctx)
        if args:
            compile_expr(args[0], ctx)
            ctx.emitter.emit_call(f"$string_{method}_chars")
        else:
            ctx.emitter.emit_call(f"$string_{method}")
        return

    if method == "split":
        compile_expr(obj, ctx)
        if args:
            compile_expr(args[0], ctx)
        else:
            ctx.emitter.emit_string(" ")
        if len(args) >= 2:
            compile_expr(args[1], ctx)
            ctx.emitter.emit_call("$string_split_max")
        else:
            ctx.emitter.emit_call("$string_split")
        return

    if method == "replace":
        compile_expr(obj, ctx)
        compile_expr(args[0], ctx)
        compile_expr(args[1], ctx)
        if len(args) >= 3:
            compile_expr(args[2], ctx)
            ctx.emitter.emit_call("$string_replace_count")
        else:
            ctx.emitter.emit_call("$string_replace")
        return

    if method == "format":
        ctx.emitter.comment("string.format()")
        compile_expr(obj, ctx)
        for arg in args:
            compile_expr(arg, ctx)
        ctx.emitter.line("(ref.null eq)  ;; args terminator")
        for _ in args:
            ctx.emitter.line("(struct.new $PAIR)  ;; args entry")
        ctx.emitter.emit_call("$string_format")
        return

    if method == "copy":
        compile_expr(obj, ctx)
        ctx.emitter.emit_call("$method_copy")
        return

    # Generator methods: send and throw (unique to generators)
    if method == "send":
        ctx.emitter.comment("generator.send()")
        compile_expr(obj, ctx)
        if args:
            compile_expr(args[0], ctx)
        else:
            ctx.emitter.emit_null_eq()
        ctx.emitter.emit_call("$generator_send")
        return

    if method == "throw":
        ctx.emitter.comment("generator.throw()")
        compile_expr(obj, ctx)
        if args:
            compile_expr(args[0], ctx)
        else:
            ctx.emitter.emit_null_eq()
        ctx.emitter.emit_call("$generator_throw")
        return

    # Generator close - use runtime type checking helper
    if method == "close" and not args:
        ctx.emitter.comment("method.close() - may be generator or other")
        compile_expr(obj, ctx)
        ctx.emitter.emit_call("$method_close")
        return

    if method == "add" and len(args) == 1:
        _compile_add_method(obj, args[0], ctx)
        return

    # Check builtin helpers
    helper = (
        STRING_METHODS.get(method)
        or LIST_METHODS.get(method)
        or DICT_METHODS.get(method)
        or (SET_METHODS.get(method) if method != "add" else None)
    )

    if helper:
        # For list-modifying methods, we need to store the result back
        # since operations on empty lists return a new list
        # Only mutating methods need store-back; index/count/copy return non-list values
        list_mutating_methods = {"append", "extend", "insert", "clear", "pop", "remove"}
        is_list_mutating = method in list_mutating_methods
        is_attr_access = isinstance(obj, ast.Attribute)
        is_name_access = isinstance(obj, ast.Name)

        if is_list_mutating and is_attr_access:
            # Type narrowing for attribute access
            assert isinstance(obj, ast.Attribute)
            # Save the object for later attribute update
            compile_expr(obj.value, ctx)
            ctx.emitter.line("(local.set $tmp)  ;; save object for attr update")
            # Get the list attribute
            ctx.emitter.emit_local_get("$tmp")
            ctx.emitter.emit_string(obj.attr)
            ctx.emitter.emit_call("$object_getattr")
            # Call the list method
            for arg in args:
                compile_expr(arg, ctx)
            ctx.emitter.emit_call(helper)
            # Store result back into attribute
            ctx.emitter.line("(local.set $tmp2)  ;; save list method result")
            ctx.emitter.emit_local_get("$tmp")
            ctx.emitter.emit_string(obj.attr)
            ctx.emitter.emit_local_get("$tmp2")
            ctx.emitter.emit_call("$object_setattr")
            ctx.emitter.emit_drop()
            ctx.emitter.emit_local_get("$tmp2")  # return the result
        elif is_list_mutating and is_name_access:
            # Type narrowing for name access
            assert isinstance(obj, ast.Name)
            var_name = obj.id
            # Call the list method
            compile_expr(obj, ctx)
            for arg in args:
                compile_expr(arg, ctx)
            ctx.emitter.emit_call(helper)
            # Store result back into variable (for empty list case)
            if var_name in ctx.local_vars:
                ctx.emitter.line("(local.tee $tmp)  ;; save and return result")
                ctx.emitter.emit_local_set(ctx.local_vars[var_name])
                ctx.emitter.emit_local_get("$tmp")
            elif var_name in ctx.global_vars:
                ctx.emitter.line("(local.tee $tmp)  ;; save and return result")
                ctx.emitter.emit_global_set(f"$global_{var_name}")
                ctx.emitter.emit_local_get("$tmp")
            # If not found in locals or globals, just leave result on stack
        else:
            compile_expr(obj, ctx)
            for arg in args:
                compile_expr(arg, ctx)
            ctx.emitter.emit_call(helper)
    else:
        # User-defined method
        _compile_user_method_call(obj, method, args, ctx)


def _compile_pop_method(
    obj: ast.expr, args: list[ast.expr], ctx: CompilerContext
) -> None:
    """Compile pop method call."""

    if args:
        compile_expr(obj, ctx)
        ctx.emitter.line("(local.set $tmp)  ;; save obj")
        compile_expr(args[0], ctx)
        ctx.emitter.line("(local.set $tmp2)  ;; save arg")

        ctx.emitter.emit_local_get("$tmp")
        ctx.emitter.emit_local_get("$tmp2")
        if len(args) >= 2:
            compile_expr(args[1], ctx)
            ctx.emitter.emit_call("$method_pop_arg_default")
        else:
            ctx.emitter.emit_call("$method_pop_arg")

        # Update the variable with the modified list (needed for index 0 case)
        if isinstance(obj, ast.Name):
            var_name = obj.id
            ctx.emitter.emit_local_get("$tmp")
            ctx.emitter.emit_local_get("$tmp2")
            ctx.emitter.emit_call("$method_pop_arg_update")
            if var_name in ctx.local_vars:
                ctx.emitter.emit_local_set(ctx.local_vars[var_name])
            elif var_name in ctx.global_vars:
                ctx.emitter.emit_global_set(f"$global_{var_name}")
    else:
        compile_expr(obj, ctx)
        ctx.emitter.emit_call("$list_pop")


def _compile_add_method(obj: ast.expr, arg: ast.expr, ctx: CompilerContext) -> None:
    """Compile add method with runtime dispatch."""

    compile_expr(obj, ctx)
    ctx.emitter.line("(local.set $tmp)  ;; save obj for add dispatch")
    ctx.emitter.line(
        "(if (result (ref null eq)) (ref.test (ref $OBJECT) (local.get $tmp))"
    )
    ctx.emitter.line("  (then")
    ctx.emitter.comment("user-defined add method")
    ctx.emitter.line("    (local.get $tmp)  ;; self")
    compile_expr(arg, ctx)
    ctx.emitter.emit_null_eq()
    ctx.emitter.emit_struct_new("$PAIR")
    ctx.emitter.line("    (struct.new $PAIR)  ;; args with self")
    ctx.emitter.line("    (local.get $tmp)  ;; object")
    ctx.emitter.emit_string("add")
    ctx.emitter.emit_call("$object_getattr")
    ctx.emitter.emit_ref_cast("$CLOSURE")
    ctx.emitter.line("    (local.tee $tmp2)")
    ctx.emitter.emit_ref_cast("$CLOSURE")
    ctx.emitter.line("    (struct.get $CLOSURE 0)  ;; env")
    ctx.emitter.emit_local_get("$tmp2")
    ctx.emitter.emit_ref_cast("$CLOSURE")
    ctx.emitter.line("    (struct.get $CLOSURE 1)  ;; func index")
    ctx.emitter.line("    (call_indirect (type $FUNC))")
    ctx.emitter.line("    drop  ;; discard method return value")
    ctx.emitter.line("    (local.get $tmp)  ;; return original object")
    ctx.emitter.line("  )")
    ctx.emitter.line("  (else")
    ctx.emitter.comment("set.add")
    ctx.emitter.emit_local_get("$tmp")
    compile_expr(arg, ctx)
    ctx.emitter.emit_call("$set_add")
    ctx.emitter.line("  )")
    ctx.emitter.line(")")


def _compile_user_method_call(
    obj: ast.expr, method: str, args: list[ast.expr], ctx: CompilerContext
) -> None:
    """Compile user-defined method call."""

    ctx.emitter.comment("user-defined method call")

    # Save object for both method lookup and potential self arg
    compile_expr(obj, ctx)
    ctx.emitter.line("(local.set $tmp)  ;; save object/super")

    # Build args list WITHOUT self (dispatch helper will add self/cls if needed)
    for arg in args:
        compile_expr(arg, ctx)
    ctx.emitter.emit_null_eq()
    for _ in range(len(args)):
        ctx.emitter.emit_struct_new("$PAIR")
    ctx.emitter.line("(local.set $tmp2)  ;; save args")

    # Get the method (may be wrapped in STATICMETHOD/CLASSMETHOD)
    ctx.emitter.line("(local.get $tmp)  ;; object/super for attr lookup")
    ctx.emitter.emit_string(method)
    ctx.emitter.emit_call("$object_getattr")
    ctx.emitter.line("(local.set $chain_val)  ;; save method")

    # Call dispatch helper: handles staticmethod/classmethod/regular
    ctx.emitter.line("(local.get $tmp)  ;; object")
    ctx.emitter.line("(local.get $chain_val)  ;; method (possibly wrapped)")
    ctx.emitter.line("(local.get $tmp2)  ;; args")
    ctx.emitter.emit_call("$call_method_dispatch")


def _compile_dict_with_kwargs(
    args: list[ast.expr], keywords: list[ast.keyword], ctx: CompilerContext
) -> None:
    """Compile dict() with keyword arguments using hash table."""

    ctx.emitter.comment("dict() with kwargs (hash table)")

    # Start with empty dict or copy of base dict
    if args:
        compile_expr(args[0], ctx)
        ctx.emitter.line("call $dict_copy  ;; copy base dict")
    else:
        ctx.emitter.line("(call $dict_new)  ;; new hash table dict")

    # Add each keyword argument
    for kw in keywords:
        if kw.arg:
            ctx.emitter.emit_string(kw.arg)
            compile_expr(kw.value, ctx)
            ctx.emitter.line("call $dict_set_wrapped  ;; set key-value")


def _compile_print_with_kwargs(
    args: list[ast.expr],
    sep_kw: ast.keyword | None,
    end_kw: ast.keyword | None,
    ctx: CompilerContext,
) -> None:
    """Compile print() with sep= and/or end= keyword arguments."""
    ctx.emitter.comment("print with kwargs")

    # Compile positional args into PAIR chain
    if args:
        for arg in args:
            compile_expr(arg, ctx)
        ctx.emitter.emit_null_eq()
        for _ in range(len(args)):
            ctx.emitter.emit_struct_new("$PAIR")
    else:
        ctx.emitter.emit_null_eq()

    # Compile sep value (default is space)
    if sep_kw:
        compile_expr(sep_kw.value, ctx)
    else:
        ctx.emitter.emit_string(" ")

    # Compile end value (default is newline)
    if end_kw:
        compile_expr(end_kw.value, ctx)
    else:
        ctx.emitter.emit_string("\n")

    ctx.emitter.emit_call("$print_with_sep_end")


def _compile_slotted_class_instantiation(
    class_name: str,
    slots: list[str],
    args: list[ast.expr],
    ctx: CompilerContext,
) -> None:
    """Compile direct instantiation of a slotted class.

    Slotted classes use struct-based storage instead of hash tables,
    providing O(1) attribute access via struct.get/struct.set.

    The generated code:
    1. Creates a struct with class ref and null fields
    2. Stores it to $tmp
    3. Builds args PAIR chain with self prepended
    4. Looks up __init__ from class methods
    5. Calls __init__ via indirect call
    6. Returns the instance from $tmp
    """
    type_name = ctx.get_slotted_type_name(class_name)
    ctx.emitter.comment(f"slotted class instantiation: {class_name}")

    # Get the class reference from global
    ctx.emitter.emit_global_get(f"$global_{class_name}")
    ctx.emitter.emit_ref_cast("$CLASS")

    # Create struct with null fields for each slot
    for _ in slots:
        ctx.emitter.emit_null_eq()

    ctx.emitter.line(f"(struct.new {type_name})")
    ctx.emitter.line("(local.set $tmp)  ;; save instance")

    # Build args PAIR chain with self prepended: (self, arg1, arg2, ...)
    # First compile all args, then self, then build chain
    ctx.emitter.emit_local_get("$tmp")  # self
    for arg in args:
        compile_expr(arg, ctx)
    ctx.emitter.emit_null_eq()
    # Build chain: need len(args) + 1 PAIR structs (args + self)
    for _ in range(len(args) + 1):
        ctx.emitter.emit_struct_new("$PAIR")
    ctx.emitter.line("(local.set $tmp2)  ;; save args with self")

    # Look up __init__ from class methods
    ctx.emitter.emit_global_get(f"$global_{class_name}")
    ctx.emitter.emit_ref_cast("$CLASS")
    ctx.emitter.emit_string("__init__")
    ctx.emitter.emit_call("$class_lookup_method")
    ctx.emitter.emit_ref_cast("$CLOSURE")
    ctx.emitter.line("(local.set $chain_val)  ;; save __init__ closure")

    # Call __init__: args, env (from closure), func_idx (from closure)
    ctx.emitter.emit_local_get("$tmp2")  # args
    ctx.emitter.emit_local_get("$chain_val")
    ctx.emitter.emit_ref_cast("$CLOSURE")
    ctx.emitter.line("(struct.get $CLOSURE 0)  ;; env from closure")
    ctx.emitter.emit_local_get("$chain_val")
    ctx.emitter.emit_ref_cast("$CLOSURE")
    ctx.emitter.line("(struct.get $CLOSURE 1)  ;; func index")
    ctx.emitter.line("(call_indirect (type $FUNC))")
    ctx.emitter.emit_drop()  # __init__ returns None, discard

    # Return the instance
    ctx.emitter.emit_local_get("$tmp")


def _compile_slotted_method_call(
    obj: ast.expr,
    class_name: str,
    method: str,
    args: list[ast.expr],
    ctx: CompilerContext,
) -> None:
    """Compile method call on a slotted instance.

    For slotted classes, we look up methods directly from the class
    instead of going through $object_getattr (which expects $OBJECT structs).
    """
    type_name = ctx.get_slotted_type_name(class_name)
    ctx.emitter.comment(f"slotted method call: {method}()")

    # Save object for self
    compile_expr(obj, ctx)
    ctx.emitter.line("(local.set $tmp)  ;; save slotted instance")

    # Build args list WITHOUT self (dispatch helper will add self)
    for arg in args:
        compile_expr(arg, ctx)
    ctx.emitter.emit_null_eq()
    for _ in range(len(args)):
        ctx.emitter.emit_struct_new("$PAIR")
    ctx.emitter.line("(local.set $tmp2)  ;; save args")

    # Get class from the slotted instance's $class field
    ctx.emitter.emit_local_get("$tmp")
    ctx.emitter.emit_ref_cast(type_name)
    ctx.emitter.line(f"(struct.get {type_name} 0)  ;; get $class field")

    # Look up method from class
    ctx.emitter.emit_string(method)
    ctx.emitter.emit_call("$class_lookup_method")
    ctx.emitter.line("(local.set $chain_val)  ;; save method")

    # Call dispatch helper: handles staticmethod/classmethod/regular
    ctx.emitter.emit_local_get("$tmp")  # object (self)
    ctx.emitter.emit_local_get("$chain_val")  # method
    ctx.emitter.emit_local_get("$tmp2")  # args
    ctx.emitter.emit_call("$call_method_dispatch")


def _compile_call_with_kwargs(
    func_name: str,
    args: list[ast.expr],
    keywords: list[ast.keyword],
    ctx: CompilerContext,
) -> None:
    """Compile function call with **kwargs unpacking."""
    sig = ctx.func_signatures[func_name]

    ctx.emitter.comment(f"call {func_name} with **kwargs")

    # Compile the function itself
    ctx.emitter.emit_local_get(ctx.local_vars[func_name])
    ctx.emitter.emit_string("__init__")

    # Find the kwargs dict (kw.arg is None)
    kwargs_dict = next(kw for kw in keywords if kw.arg is None)

    # Also collect explicit keyword args (kw.arg is not None)
    explicit_kwargs = {kw.arg: kw.value for kw in keywords if kw.arg is not None}

    # Compile the kwargs dict and store it
    compile_expr(kwargs_dict.value, ctx)
    ctx.emitter.line("(local.set $tmp2)  ;; save kwargs dict")

    # Build args list for each parameter
    num_positional = len(args)

    for i, param_name in enumerate(sig.param_names):
        if i < num_positional:
            # Parameter covered by positional arg
            compile_expr(args[i], ctx)
        elif param_name in explicit_kwargs:
            # Parameter provided as explicit keyword arg
            compile_expr(explicit_kwargs[param_name], ctx)
        else:
            # Try to get from kwargs dict, fall back to default
            ctx.emitter.emit_local_get("$tmp2")  # kwargs dict
            ctx.emitter.emit_string(param_name)
            # Check if param has a default
            if i >= sig.first_default_idx:
                default_idx = i - sig.first_default_idx
                compile_expr(sig.defaults[default_idx], ctx)
            else:
                # Required param - use null as sentinel (will error at runtime if missing)
                ctx.emitter.emit_null_eq()
            ctx.emitter.emit_call("$dict_get_default")

    # Build PAIR chain
    ctx.emitter.emit_null_eq()
    for _ in sig.param_names:
        ctx.emitter.emit_struct_new("$PAIR")

    ctx.emitter.line("(ref.null $ENV)")
    ctx.emitter.emit_call("$call_or_instantiate")
