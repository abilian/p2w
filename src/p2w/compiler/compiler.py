"""Core compiler module - simple functional design."""

from __future__ import annotations

import ast
from io import StringIO
from typing import TYPE_CHECKING

from p2w.compiler.analysis import (
    collect_all_global_refs,
    collect_class_names,
    collect_comprehension_locals,
    collect_function_names,
    collect_iter_locals,
    collect_local_vars,
    collect_slotted_classes,
    collect_with_locals,
    has_try_except,
    has_try_finally,
)
from p2w.compiler.builtins import BUILTINS
from p2w.compiler.codegen.statements import compile_stmt
from p2w.compiler.context import CompilerContext
from p2w.compiler.inference import TypeInferencer
from p2w.compiler.inlining import inline_functions
from p2w.compiler.types import NativeType
from p2w.emitter import WATEmitter
from p2w.wat import HELPERS_CODE, IMPORTS_CODE, POST_TYPES_GLOBALS, TYPES_CODE

# Enable function inlining optimization (Phase 3)
ENABLE_INLINING = True

if TYPE_CHECKING:
    from typing import TextIO


def compile_to_wat(source: str) -> str:
    """Compile Python source code to WAT.

    Args:
        source: Python source code.

    Returns:
        WAT (WebAssembly Text) code.
    """
    output = StringIO()
    tree = ast.parse(source)
    compile_module(tree.body, output)
    return output.getvalue()


def compile_module(body: list[ast.stmt], stream: TextIO) -> None:
    """Compile a module (list of statements) to WAT."""
    # Apply function inlining optimization (Phase 3)
    if ENABLE_INLINING:
        body, _inlined_count = inline_functions(body)

    emitter = WATEmitter(stream)
    ctx = CompilerContext(emitter=emitter)

    # Pre-pass: collect all variables referenced via 'global' statements
    # Also include class names and function names so they can be referenced
    # from anywhere (e.g., forward references between functions)
    ctx.global_vars = (
        collect_all_global_refs(body)
        | collect_class_names(body)
        | collect_function_names(body)
    )

    # Collect slotted classes (classes with __slots__)
    ctx.slotted_classes = collect_slotted_classes(body)

    emitter.line("(module")
    emitter.indent += 2

    # Imports
    emitter.text(IMPORTS_CODE)

    # Type definitions
    emitter.text(TYPES_CODE)

    # Generate struct types for slotted classes
    if ctx.slotted_classes:
        emitter.line("")
        emitter.comment("Slotted class struct types (optimized attribute access)")
        for class_name, slots in ctx.slotted_classes.items():
            _emit_slotted_class_type(class_name, slots, emitter)

    # Post-type globals (like Ellipsis singleton)
    emitter.text(POST_TYPES_GLOBALS)

    # Emit wasm globals
    if ctx.global_vars:
        emitter.line("")
        emitter.comment("Module-level globals (accessed via 'global' statements)")
        for var_name in sorted(ctx.global_vars):
            emitter.line(
                f"(global $global_{var_name} (mut (ref null eq)) (ref.null eq))"
            )

    # Initialize lexical env with builtins
    ctx.lexical_env.push_frame()
    for builtin in BUILTINS:
        ctx.lexical_env.frames[-1].insert(0, builtin.name)

    # Builtin functions
    for builtin in BUILTINS:
        emitter.text(builtin.code)

    # Helper functions
    emitter.text(HELPERS_CODE)

    # Generate slotted dispatch getattr (must come after helpers)
    _emit_slotted_dispatch_getattr(ctx)

    # User code
    _compile_user_code(body, ctx)

    # Start function
    _compile_start_func(ctx)

    # Event callback export (for JS->WASM callbacks)
    _compile_event_callback(ctx)

    # Emit all user functions
    for func_stream in ctx.user_funcs:
        emitter.line("")
        emitter.text(func_stream.getvalue())

    # Emit specialized functions (Phase 4.1 optimization)
    # These are called directly by name, not via call_indirect
    for func_stream in ctx.spec_func_code:
        emitter.line("")
        emitter.text(func_stream.getvalue())

    # Function table
    _compile_function_table(ctx)

    # Memory and data section
    _compile_memory_section(ctx)

    emitter.indent -= 2
    emitter.line(")")


def _compile_user_code(body: list[ast.stmt], ctx: CompilerContext) -> None:
    """Compile user code as the main function ($user_func_0)."""
    saved_stream = ctx.emitter.stream
    saved_indent = ctx.emitter.indent
    saved_locals = ctx.local_vars

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

    # Declare locals
    local_names = collect_local_vars(body)
    for name in sorted(local_names):
        local_name = f"$var_{name}"
        ctx.local_vars[name] = local_name
        ctx.emitter.line(f"(local {local_name} (ref null eq))")

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

    # Declare $exc local if there are try/except statements
    # Must be nullable since it's set in catch clause
    if has_try_except(body):
        ctx.emitter.line("(local $exc (ref null $EXCEPTION))")

    # Declare $exnref local if there are try/finally statements
    # Needed for rethrowing exceptions after finally block
    if has_try_finally(body):
        ctx.emitter.line("(local $exnref exnref)")

    # Set up type inferencer for module-level code
    inferencer = TypeInferencer()
    inferencer.analyze_module(body)
    ctx.type_inferencer = inferencer

    # Save and set native locals
    saved_native_locals = ctx.native_locals
    ctx.native_locals = inferencer.native_vars.copy()

    # Declare native locals for unboxed variables (f64/i32/i64)
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
    ctx.emitter.comment("prologue: create env with builtins")
    ctx.emitter.line(
        "(local.set $env (struct.new $ENV (local.get $env) (local.get $args)))"
    )

    # Compile statements
    for stmt in body:
        compile_stmt(stmt, ctx)

    ctx.emitter.emit_null_eq()

    ctx.emitter.indent -= 2
    ctx.emitter.line(")")

    ctx.emitter.stream = saved_stream
    ctx.emitter.indent = saved_indent
    ctx.local_vars = saved_locals
    ctx.native_locals = saved_native_locals


def _compile_start_func(ctx: CompilerContext) -> None:
    """Compile the start function."""
    ctx.emitter.line("")
    ctx.emitter.line('(func (export "_start") (result i32)')
    ctx.emitter.indent += 2
    ctx.emitter.line("(local $builtins (ref null eq))")

    for i, builtin in enumerate(BUILTINS):
        ctx.emitter.line(
            f"(local.set $builtins (struct.new $PAIR "
            f"(struct.new $CLOSURE (ref.null $ENV) (i32.const {i})) "
            f"(local.get $builtins)))"
        )

    ctx.emitter.line("")
    ctx.emitter.comment("call main user function")
    ctx.emitter.line("(call $user_func_0 (local.get $builtins) (ref.null $ENV))")
    ctx.emitter.emit_drop()
    ctx.emitter.emit_i32_const(0)

    ctx.emitter.indent -= 2
    ctx.emitter.line(")")


def _compile_event_callback(ctx: CompilerContext) -> None:
    """Compile the event_callback export for JS->WASM callbacks."""
    ctx.emitter.line("")
    ctx.emitter.comment("Event callback dispatcher - called by JS when events fire")
    ctx.emitter.line(
        '(func (export "event_callback") (param $idx i32) (param $event_handle i32)'
    )
    ctx.emitter.indent += 2

    ctx.emitter.line("(local $closure (ref null eq))")
    ctx.emitter.line("(local $func_idx i32)")
    ctx.emitter.line("(local $env (ref null $ENV))")
    ctx.emitter.line("(local $args (ref null eq))")
    ctx.emitter.line("(local $event (ref null eq))")

    ctx.emitter.line("")
    ctx.emitter.comment("Get the closure from callback table")
    ctx.emitter.line("(local.set $closure (call $get_callback (local.get $idx)))")

    ctx.emitter.line("")
    ctx.emitter.comment("Check if valid closure")
    ctx.emitter.line("(if (ref.is_null (local.get $closure))")
    ctx.emitter.indent += 2
    ctx.emitter.line("(then (return))")
    ctx.emitter.indent -= 2
    ctx.emitter.line(")")

    ctx.emitter.line("")
    ctx.emitter.comment("Extract function index and environment from closure")
    ctx.emitter.line("(if (ref.test (ref $CLOSURE) (local.get $closure))")
    ctx.emitter.indent += 2
    ctx.emitter.line("(then")
    ctx.emitter.indent += 2
    ctx.emitter.line(
        "(local.set $func_idx (struct.get $CLOSURE 1 "
        "(ref.cast (ref $CLOSURE) (local.get $closure))))"
    )
    ctx.emitter.line(
        "(local.set $env (struct.get $CLOSURE 0 "
        "(ref.cast (ref $CLOSURE) (local.get $closure))))"
    )
    ctx.emitter.indent -= 2
    ctx.emitter.line(")")
    ctx.emitter.line("(else (return))")
    ctx.emitter.indent -= 2
    ctx.emitter.line(")")

    ctx.emitter.line("")
    ctx.emitter.comment("Wrap event handle as i31 and build args list")
    ctx.emitter.line("(local.set $event (ref.i31 (local.get $event_handle)))")
    ctx.emitter.line(
        "(local.set $args (struct.new $PAIR (local.get $event) (ref.null eq)))"
    )

    ctx.emitter.line("")
    ctx.emitter.comment("Call the handler function via indirect call")
    ctx.emitter.line(
        "(call_indirect (type $FUNC) "
        "(local.get $args) (local.get $env) (local.get $func_idx))"
    )
    ctx.emitter.line("drop")

    ctx.emitter.indent -= 2
    ctx.emitter.line(")")


def _compile_function_table(ctx: CompilerContext) -> None:
    """Compile function table and element sections."""
    ctx.emitter.line("")
    total_funcs = len(BUILTINS) + len(ctx.user_funcs)
    ctx.emitter.line(f"(table {total_funcs} funcref)")

    elem_idx = 0
    for builtin in BUILTINS:
        ctx.emitter.line(f"(elem (i32.const {elem_idx}) ${builtin.name})")
        elem_idx += 1
    for i in range(len(ctx.user_funcs)):
        ctx.emitter.line(f"(elem (i32.const {elem_idx}) $user_func_{i})")
        elem_idx += 1


def _compile_memory_section(ctx: CompilerContext) -> None:
    """Compile memory and data sections."""
    ctx.emitter.line("")
    ctx.emitter.line('(memory (export "memory") 16)')

    if ctx.emitter.string_map:
        sorted_strings = sorted(ctx.emitter.string_map.items(), key=lambda x: x[1][0])
        for s, (offset, _length) in sorted_strings:
            # Check if this is a bytes entry (special key format)
            if s.startswith("\x00bytes:"):
                # Extract hex data and convert to bytes
                hex_data = s[7:]  # Skip "\x00bytes:"
                raw_bytes = bytes.fromhex(hex_data)
                # Escape bytes for WAT data segment
                escaped = "".join(f"\\{b:02x}" for b in raw_bytes)
            else:
                # Regular string - escape for WAT
                escaped = (
                    s
                    .replace("\\", "\\\\")
                    .replace('"', '\\"')
                    .replace("\n", "\\n")
                    .replace("\r", "\\r")
                    .replace("\t", "\\t")
                )
            ctx.emitter.line(f'(data (i32.const {offset}) "{escaped}")')


def _emit_slotted_class_type(
    class_name: str, slots: list[str], emitter: WATEmitter
) -> None:
    """Emit WASM struct type definition for a slotted class.

    Generates a struct with:
    - $class field: reference to the class metadata (for isinstance, etc.)
    - One field per slot in __slots__, in order

    The struct is a subtype of $INSTANCE_BASE, enabling isinstance() to work
    with both regular OBJECT and slotted class instances.

    Example:
        class Record:
            __slots__ = ('x', 'y')

        Generates:
        (type $SLOTTED_Record (sub $INSTANCE_BASE (struct
          (field $class (ref $CLASS))
          (field $x (mut (ref null eq)))
          (field $y (mut (ref null eq)))
        )))
    """
    type_name = f"$SLOTTED_{class_name}"
    # Use (sub final $INSTANCE_BASE ...) to make slotted types subtypes of INSTANCE_BASE
    # This allows isinstance() to work via ref.test (ref $INSTANCE_BASE)
    # 'final' since slotted types are not meant to be subclassed further
    emitter.line(f"(type {type_name} (sub final $INSTANCE_BASE (struct")
    emitter.indent += 2
    # First field is always the class reference (for isinstance, method lookup)
    emitter.line("(field $class (ref $CLASS))")
    # Then each slot as a mutable field
    for slot in slots:
        emitter.line(f"(field ${slot} (mut (ref null eq)))")
    emitter.indent -= 2
    emitter.line(")))")


def _emit_slotted_dispatch_getattr(ctx: CompilerContext) -> None:
    """Generate $slotted_dispatch_getattr function for runtime attribute access.

    This function is called by $object_getattr when it encounters a slotted
    instance. It dispatches to the correct struct field based on the attribute
    name and the runtime type of the object.

    Generated code looks like:
        (func $slotted_dispatch_getattr (param $obj (ref null eq)) (param $name (ref null eq)) (result (ref null eq))
          ;; Check if obj is Record
          (if (ref.test (ref $SLOTTED_Record) (local.get $obj))
            (then
              ;; Check each slot name
              (if (call $strings_equal (ref.cast (ref $STRING) (local.get $name)) (struct.new $STRING offset len))
                (then (return (struct.get $SLOTTED_Record 1 (ref.cast (ref $SLOTTED_Record) (local.get $obj))))))
              ...
            )
          )
          (ref.null eq)  ;; Not found
        )
    """
    emitter = ctx.emitter

    if not ctx.slotted_classes:
        # No slotted classes - emit stubs that always return null/obj
        emitter.line("")
        emitter.comment("Slotted dispatch getattr (no slotted classes)")
        emitter.line(
            "(func $slotted_dispatch_getattr (param $obj (ref null eq)) "
            "(param $name (ref null eq)) (result (ref null eq))"
        )
        emitter.line("  (ref.null eq)")
        emitter.line(")")
        # Also emit setattr stub
        _emit_slotted_dispatch_setattr(ctx)
        return

    emitter.line("")
    emitter.comment(
        "Slotted dispatch getattr - runtime attribute access for slotted instances"
    )
    emitter.line(
        "(func $slotted_dispatch_getattr (param $obj (ref null eq)) "
        "(param $name (ref null eq)) (result (ref null eq))"
    )
    emitter.indent += 2

    for class_name, slots in ctx.slotted_classes.items():
        type_name = f"$SLOTTED_{class_name}"

        # Check if obj is this slotted type
        emitter.line(f"(if (ref.test (ref {type_name}) (local.get $obj))")
        emitter.indent += 2
        emitter.line("(then")
        emitter.indent += 2

        # Check each slot name
        for idx, slot_name in enumerate(slots):
            field_idx = idx + 1  # Field 0 is $class
            # Get the string offset for this slot name
            str_offset, str_len = emitter.intern_string(slot_name)

            emitter.line(
                f"(if (call $strings_equal "
                f"(ref.cast (ref $STRING) (local.get $name)) "
                f"(struct.new $STRING (i32.const {str_offset}) (i32.const {str_len})))"
            )
            emitter.indent += 2
            emitter.line(
                f"(then (return (struct.get {type_name} {field_idx} "
                f"(ref.cast (ref {type_name}) (local.get $obj))))))"
            )
            emitter.indent -= 2

        # Also check class methods (for method calls on slotted instances)
        emitter.line(
            "(return (call $class_lookup_method "
            "(struct.get $INSTANCE_BASE 0 (ref.cast (ref $INSTANCE_BASE) (local.get $obj))) "
            "(local.get $name)))"
        )

        emitter.indent -= 2
        emitter.line(")")
        emitter.indent -= 2
        emitter.line(")")

    # Not found in any slotted type
    emitter.line("(ref.null eq)")
    emitter.indent -= 2
    emitter.line(")")

    # Also generate setattr dispatch
    _emit_slotted_dispatch_setattr(ctx)


def _emit_slotted_dispatch_setattr(ctx: CompilerContext) -> None:
    """Generate $slotted_dispatch_setattr function for runtime attribute setting.

    Similar to getattr, but sets the struct field instead of getting it.
    """
    emitter = ctx.emitter

    if not ctx.slotted_classes:
        # No slotted classes - emit a stub that returns obj unchanged
        emitter.line("")
        emitter.comment("Slotted dispatch setattr (no slotted classes)")
        emitter.line(
            "(func $slotted_dispatch_setattr (param $obj (ref null eq)) "
            "(param $name (ref null eq)) (param $value (ref null eq)) (result (ref null eq))"
        )
        emitter.line("  (local.get $obj)")
        emitter.line(")")
        return

    emitter.line("")
    emitter.comment(
        "Slotted dispatch setattr - runtime attribute setting for slotted instances"
    )
    emitter.line(
        "(func $slotted_dispatch_setattr (param $obj (ref null eq)) "
        "(param $name (ref null eq)) (param $value (ref null eq)) (result (ref null eq))"
    )
    emitter.indent += 2

    for class_name, slots in ctx.slotted_classes.items():
        type_name = f"$SLOTTED_{class_name}"

        # Check if obj is this slotted type
        emitter.line(f"(if (ref.test (ref {type_name}) (local.get $obj))")
        emitter.indent += 2
        emitter.line("(then")
        emitter.indent += 2

        # Check each slot name
        for idx, slot_name in enumerate(slots):
            field_idx = idx + 1  # Field 0 is $class
            # Get the string offset for this slot name
            str_offset, str_len = emitter.intern_string(slot_name)

            emitter.line(
                f"(if (call $strings_equal "
                f"(ref.cast (ref $STRING) (local.get $name)) "
                f"(struct.new $STRING (i32.const {str_offset}) (i32.const {str_len})))"
            )
            emitter.indent += 2
            emitter.line("(then")
            emitter.indent += 2
            emitter.line(
                f"(struct.set {type_name} {field_idx} "
                f"(ref.cast (ref {type_name}) (local.get $obj)) "
                f"(local.get $value))"
            )
            emitter.line("(return (local.get $obj))")
            emitter.indent -= 2
            emitter.line(")")
            emitter.indent -= 2
            emitter.line(")")

        # Slot not found - return obj unchanged (shouldn't happen in valid code)
        emitter.line("(return (local.get $obj))")

        emitter.indent -= 2
        emitter.line(")")
        emitter.indent -= 2
        emitter.line(")")

    # Not a slotted type - return obj unchanged
    emitter.line("(local.get $obj)")
    emitter.indent -= 2
    emitter.line(")")


# Keep WasmCompiler for backward compatibility
class WasmCompiler:
    """Wrapper class for backward compatibility."""

    def __init__(self, stream: TextIO) -> None:
        self.stream = stream

    def compile(self, source: str) -> None:
        tree = ast.parse(source)
        compile_module(tree.body, self.stream)
