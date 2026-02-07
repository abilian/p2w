"""WAT emitter for p2w.

Provides the WATEmitter class that handles all WAT code generation.
The Compiler delegates code emission to the Emitter, maintaining clean separation
between AST traversal/analysis and code generation.
"""

from __future__ import annotations

from typing import TextIO


class WATEmitter:
    """Generates WebAssembly Text (WAT) code.

    Handles:
    - Line and text emission with automatic indentation
    - String constant interning
    - Basic WAT constructs (literals, locals, globals)

    The Compiler traverses the AST and calls Emitter methods to generate code.
    This separation allows the Emitter to focus purely on WAT syntax.
    """

    def __init__(self, stream: TextIO) -> None:
        """Initialize the emitter.

        Args:
            stream: Output stream where WAT code is written.
        """
        self.stream = stream
        self.indent = 0

        # String interning: string -> (offset, length)
        self.string_map: dict[str, tuple[int, int]] = {}
        self.string_offset = 2048

    # =========================================================================
    # Core Emission
    # =========================================================================

    def line(self, code: str) -> None:
        """Emit a single line of WAT code with proper indentation."""
        self.stream.write(" " * self.indent + code + "\n")

    def text(self, code: str) -> None:
        """Emit multi-line WAT code, preserving internal structure."""
        for ln in code.strip().split("\n"):
            self.stream.write(" " * self.indent + ln + "\n")

    def comment(self, text: str) -> None:
        """Emit a WAT comment."""
        self.line(f";; {text}")

    def indent_inc(self, amount: int = 2) -> None:
        """Increase indentation level."""
        self.indent += amount

    def indent_dec(self, amount: int = 2) -> None:
        """Decrease indentation level."""
        self.indent -= amount

    # =========================================================================
    # String Handling
    # =========================================================================

    def intern_string(self, s: str) -> tuple[int, int]:
        """Intern a string constant, returning (offset, length).

        Deduplicates strings that have already been interned.
        """
        if s not in self.string_map:
            offset = self.string_offset
            length = len(s.encode("utf-8"))
            self.string_map[s] = (offset, length)
            self.string_offset += length
        return self.string_map[s]

    def emit_string(self, s: str) -> None:
        """Emit a string constant reference."""
        offset, length = self.intern_string(s)
        self.line(f"(struct.new $STRING (i32.const {offset}) (i32.const {length}))")

    def intern_bytes(self, data: bytes) -> tuple[int, int]:
        """Intern a bytes constant, returning (offset, length).

        Unlike strings, bytes are stored as raw bytes without UTF-8 encoding.
        We use the string_map with a special prefix to avoid collisions.
        """
        # Use a special key to distinguish bytes from strings
        key = f"\x00bytes:{data.hex()}"
        if key not in self.string_map:
            offset = self.string_offset
            length = len(data)
            self.string_map[key] = (offset, length)
            self.string_offset += length
        return self.string_map[key]

    def emit_bytes(self, data: bytes) -> None:
        """Emit a bytes constant reference."""
        offset, length = self.intern_bytes(data)
        self.line(
            f"(struct.new $BYTES (i32.const {offset}) (i32.const {length}) (i32.const 0))"
        )

    # =========================================================================
    # Literals
    # =========================================================================

    def emit_int(self, value: int) -> None:
        """Emit an integer literal (as i31 reference)."""
        self.line(f"(ref.i31 (i32.const {value}))")

    def emit_int64(self, value: int) -> None:
        """Emit a large integer literal (as INT64 struct)."""
        self.line(f"(struct.new $INT64 (i64.const {value}))")

    def emit_float(self, value: float) -> None:
        """Emit a float literal."""
        self.line(f"(struct.new $FLOAT (f64.const {value}))")

    def emit_bool(self, value: bool) -> None:
        """Emit a boolean literal using singleton globals."""
        global_name = "$TRUE" if value else "$FALSE"
        self.line(f"(global.get {global_name})")

    def emit_none(self) -> None:
        """Emit None (null reference)."""
        self.line("(ref.null eq)")

    def emit_empty_list(self) -> None:
        """Emit an empty list marker."""
        self.line("(struct.new $EMPTY_LIST)  ;; empty list")

    def emit_empty_dict(self) -> None:
        """Emit an empty dict (hash table based)."""
        self.line("(call $dict_new)  ;; empty dict (hash table)")

    def emit_ellipsis(self) -> None:
        """Emit Ellipsis singleton (...)."""
        self.line("(global.get $ellipsis)  ;; Ellipsis")

    # =========================================================================
    # List/Set Construction
    # =========================================================================

    def emit_list_terminator(self) -> None:
        """Emit null terminator for list PAIR chain."""
        self.line("(ref.null eq)  ;; list terminator")

    def emit_pair_cons(self) -> None:
        """Emit PAIR construction (cons cell)."""
        self.line("(struct.new $PAIR)  ;; cons")

    def emit_list_construct(self, count: int) -> None:
        """Emit $LIST (array-backed) construction for a list with `count` elements.

        Assumes all `count` elements are already on the stack.
        Creates an array-backed $LIST with O(1) indexed access.
        $LIST has fields: (field $data (ref $ARRAY_ANY)) (field $len i32) (field $cap i32)
        """
        if count == 0:
            # Empty list - use emit_empty_list for consistency
            self.emit_empty_list()
        else:
            # Create array from stack elements and wrap in $LIST
            # array.new_fixed pops count elements from stack to create array
            self.line("(struct.new $LIST")
            self.line(f"  (array.new_fixed $ARRAY_ANY {count})")
            self.line(f"  (i32.const {count})  ;; len")
            self.line(f"  (i32.const {count})  ;; cap")
            self.line(")")

    def emit_tuple_construct(self, count: int) -> None:
        """Emit TUPLE construction for a tuple with `count` elements.

        Assumes all `count` elements are already on the stack.
        Creates a $TUPLE struct with array and length.
        $TUPLE has fields: (field $data (ref $ARRAY_ANY)) (field $len i32)
        """
        if count == 0:
            # Empty tuple - create with empty array
            self.line("(struct.new $TUPLE")
            self.line("  (array.new_default $ARRAY_ANY (i32.const 0))")
            self.line("  (i32.const 0)")
            self.line(")")
        else:
            # Create array from stack elements and wrap in TUPLE
            # array.new_fixed pops count elements from stack to create array
            self.line("(struct.new $TUPLE")
            self.line(f"  (array.new_fixed $ARRAY_ANY {count})")
            self.line(f"  (i32.const {count})")
            self.line(")")

    def emit_set_add(self) -> None:
        """Emit call to $set_add (adds element to set with deduplication)."""
        self.line("(call $set_add)")

    def emit_list_reverse(self) -> None:
        """Emit call to $list_reverse."""
        self.line("call $list_reverse")

    # =========================================================================
    # Array-Based List Operations ($LIST type)
    # =========================================================================

    def emit_list_v2_new(self, capacity: int) -> None:
        """Emit creation of new array-based list with given capacity."""
        self.line(f"(call $list_v2_new (i32.const {capacity}))")

    def emit_list_v2_append(self) -> None:
        """Emit append to array-based list. Stack: [list, value] -> [list]."""
        self.line("(call $list_v2_append)")

    def emit_list_v2_get(self) -> None:
        """Emit get from array-based list. Stack: [list, idx] -> [value]."""
        self.line("(call $list_v2_get)")

    def emit_list_v2_set(self) -> None:
        """Emit set on array-based list. Stack: [list, idx, value] -> []."""
        self.line("(call $list_v2_set)")

    def emit_list_v2_len(self) -> None:
        """Emit length of array-based list. Stack: [list] -> [i32]."""
        self.line("(call $list_v2_len)")

    def emit_list_v2_to_pair(self) -> None:
        """Convert array-based list to PAIR chain. Stack: [list] -> [pair]."""
        self.line("(call $list_v2_to_pair)")

    def emit_pair_to_list_v2(self) -> None:
        """Convert PAIR chain to array-based list. Stack: [pair] -> [list]."""
        self.line("(call $pair_to_list_v2)")

    # =========================================================================
    # Variables
    # =========================================================================

    def emit_local_get(self, name: str) -> None:
        """Emit local.get instruction."""
        self.line(f"(local.get {name})")

    def emit_local_set(self, name: str) -> None:
        """Emit local.set instruction."""
        self.line(f"(local.set {name})")

    def emit_local_tee(self, name: str) -> None:
        """Emit local.tee instruction (set and keep on stack)."""
        self.line(f"(local.tee {name})")

    def emit_global_get(self, name: str) -> None:
        """Emit global.get instruction."""
        self.line(f"(global.get {name})")

    def emit_global_set(self, name: str) -> None:
        """Emit global.set instruction."""
        self.line(f"(global.set {name})")

    # =========================================================================
    # Stack Operations
    # =========================================================================

    def emit_drop(self) -> None:
        """Emit drop instruction."""
        self.line("drop")

    def emit_null_eq(self) -> None:
        """Emit null reference of type eq."""
        self.line("(ref.null eq)")

    # =========================================================================
    # Function Calls
    # =========================================================================

    def emit_call(self, func_name: str) -> None:
        """Emit a direct function call."""
        self.line(f"(call {func_name})")

    def emit_call_indirect(self, type_name: str = "$FUNC") -> None:
        """Emit an indirect function call."""
        self.line(f"(call_indirect (type {type_name}))")

    def emit_return(self) -> None:
        """Emit return instruction."""
        self.line("return")

    # =========================================================================
    # Struct Operations
    # =========================================================================

    def emit_struct_new(self, struct_name: str, comment: str = "") -> None:
        """Emit struct.new instruction."""
        suffix = f"  ;; {comment}" if comment else ""
        self.line(f"(struct.new {struct_name}){suffix}")

    def emit_struct_get(self, struct_name: str, field: str | int) -> None:
        """Emit struct.get instruction."""
        self.line(f"(struct.get {struct_name} {field})")

    def emit_struct_set(self, struct_name: str, field: str | int) -> None:
        """Emit struct.set instruction."""
        self.line(f"(struct.set {struct_name} {field})")

    # =========================================================================
    # Reference Operations
    # =========================================================================

    def emit_ref_cast(self, ref_type: str) -> None:
        """Emit ref.cast instruction."""
        self.line(f"(ref.cast (ref {ref_type}))")

    def emit_ref_test(self, ref_type: str) -> None:
        """Emit ref.test instruction."""
        self.line(f"(ref.test (ref {ref_type}))")

    def emit_ref_is_null(self) -> None:
        """Emit ref.is_null instruction."""
        self.line("(ref.is_null)")

    # =========================================================================
    # Integer Operations
    # =========================================================================

    def emit_i32_const(self, value: int) -> None:
        """Emit i32.const instruction."""
        self.line(f"(i32.const {value})")

    def emit_i31_get_s(self) -> None:
        """Emit i31.get_s (extract signed i32 from i31)."""
        self.line("(i31.get_s (ref.cast (ref i31)))")

    def emit_ref_i31(self) -> None:
        """Emit ref.i31 (wrap i32 as i31 reference)."""
        self.line("ref.i31")

    # =========================================================================
    # Control Flow
    # =========================================================================

    def emit_block_start(self, label: str, result_type: str = "") -> None:
        """Emit block start."""
        result = f" (result {result_type})" if result_type else ""
        self.line(f"(block {label}{result}")
        self.indent_inc()

    def emit_block_end(self) -> None:
        """Emit block end."""
        self.indent_dec()
        self.line(")")

    def emit_loop_start(self, label: str) -> None:
        """Emit loop start."""
        self.line(f"(loop {label}")
        self.indent_inc()

    def emit_loop_end(self) -> None:
        """Emit loop end."""
        self.indent_dec()
        self.line(")")

    def emit_br(self, label: str) -> None:
        """Emit unconditional branch."""
        self.line(f"br {label}")

    def emit_br_if(self, label: str) -> None:
        """Emit conditional branch."""
        self.line(f"br_if {label}")

    def emit_if_start(self, result_type: str = "") -> None:
        """Emit if start."""
        result = f" (result {result_type})" if result_type else ""
        self.line(f"if{result}")
        self.indent_inc()

    def emit_if_else(self) -> None:
        """Emit else clause."""
        self.indent_dec()
        self.line("else")
        self.indent_inc()

    def emit_if_end(self) -> None:
        """Emit if end."""
        self.indent_dec()
        self.line("end")

    # =========================================================================
    # Exception Handling (using try_table syntax)
    # =========================================================================

    def emit_throw(self, tag: str = "$PyException") -> None:
        """Emit throw instruction. Value must be on stack."""
        self.line(f"(throw {tag})")

    def emit_throw_ref(self) -> None:
        """Emit throw_ref instruction. Exception ref must be on stack."""
        self.line("(throw_ref)")


__all__ = ["WATEmitter"]
