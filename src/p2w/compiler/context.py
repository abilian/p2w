"""Compiler context - shared state passed through compilation."""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from p2w.compiler.types import UNKNOWN

if TYPE_CHECKING:
    import ast
    from io import StringIO

    from p2w.compiler.codegen.generators import GeneratorContext
    from p2w.compiler.inference import TypeInferencer
    from p2w.compiler.types import BobType, NativeType
    from p2w.emitter import WATEmitter


@dataclass
class FunctionSignature:
    """Stores function signature information for kwargs handling."""

    param_names: list[str]
    defaults: list[
        ast.expr
    ]  # defaults[i] corresponds to param_names[first_default_idx + i]
    first_default_idx: int  # index of first param with a default


@dataclass
class LexicalEnv:
    """Compile-time lexical environment for variable resolution.

    Maintains a stack of frames, each containing variable names.
    Used to resolve variables to (frame_depth, slot_index) pairs.
    """

    frames: list[list[str]] = field(default_factory=list)

    def push_frame(self, names: list[str] | None = None) -> None:
        """Push a new frame with optional initial names."""
        self.frames.append(list(names) if names else [])

    def pop_frame(self) -> None:
        """Pop the innermost frame."""
        self.frames.pop()

    def add_name(self, name: str) -> int:
        """Add a name to the current frame, return its slot index."""
        self.frames[-1].append(name)
        return len(self.frames[-1]) - 1

    def lookup(self, name: str) -> tuple[int, int]:
        """Look up a variable, return (frame_depth, slot_index).

        Raises NameError if not found.
        """
        for depth, frame in enumerate(reversed(self.frames)):
            if name in frame:
                return (depth, frame.index(name))
        msg = f"Variable '{name}' not found"
        raise NameError(msg)

    def contains(self, name: str) -> bool:
        """Check if a name exists in any frame."""
        return any(name in frame for frame in self.frames)


@dataclass
class CompilerContext:
    """Shared state passed through all compilation functions.

    This replaces the implicit `self` in the mixin-based design.
    All compilation functions take this as their first argument.
    """

    emitter: WATEmitter

    # Compile-time lexical environment
    lexical_env: LexicalEnv = field(default_factory=LexicalEnv)

    # List of StringIO for each user-defined function's code
    user_funcs: list[StringIO] = field(default_factory=list)

    # List of StringIO for specialized functions (not in function table)
    # These are called directly by name, not via call_indirect
    spec_func_code: list[StringIO] = field(default_factory=list)

    # Local variables for current function (name -> wasm local name)
    local_vars: dict[str, str] = field(default_factory=dict)

    # Counter for generating unique comprehension local names
    comp_counter: int = 0

    # Module-level variables accessed via 'global' statements
    global_vars: set[str] = field(default_factory=set)

    # Per-function tracking: variables declared global in current function
    current_global_decls: set[str] = field(default_factory=set)

    # Per-function tracking: variables declared nonlocal in current function
    current_nonlocal_decls: set[str] = field(default_factory=set)

    # Variables that need cell treatment (accessed by nested nonlocals)
    cell_vars: set[str] = field(default_factory=set)

    # Type inferencer for compile-time type analysis (optional)
    type_inferencer: TypeInferencer | None = None

    # Current class being compiled (for super(Class, self) support)
    current_class: str | None = None

    # Function signatures for **kwargs support (func_name -> FunctionSignature)
    func_signatures: dict[str, FunctionSignature] = field(default_factory=dict)

    # Counter for generating unique labels (for try/except, loops, etc.)
    _label_counter: int = 0

    # Counter for with statements (must match analysis order)
    _with_counter: int = 0

    # Generator context for compiling generator functions
    generator_context: GeneratorContext | None = None

    # JavaScript interop: True if "import js" was seen
    js_imported: bool = False

    # Variables known to hold JS handles (for proper method dispatch)
    js_handle_vars: set[str] = field(default_factory=set)

    # Native locals: variables stored as raw WASM types (f64, i32) instead of boxed
    # Maps variable name to NativeType. Populated from TypeInferencer.native_vars.
    native_locals: dict[str, NativeType] = field(default_factory=dict)

    # Track whether current expression result is a native (unboxed) value
    # Used to determine if boxing is needed before certain operations
    has_native_value: bool = False

    # The native type of the current value on stack (when has_native_value is True)
    current_native_type: NativeType | None = None

    # Function table: maps function name -> WASM table index for direct calls
    # Populated when functions are compiled, used to bypass $call_or_instantiate
    func_table: dict[str, int] = field(default_factory=dict)

    # Specialized functions: maps function name -> (wasm_func_name, arity)
    # These have direct parameters instead of PAIR chains for faster calls
    spec_functions: dict[str, tuple[str, int]] = field(default_factory=dict)

    # Safe bounds tracking for loop-based bounds elimination
    # Maps loop variable name -> (container_var_name, container_local)
    # When set, subscript access using loop_var on container can skip bounds checks
    safe_bounds: dict[str, tuple[str, str]] = field(default_factory=dict)

    # Slotted classes: classes with __slots__ that use struct-based storage
    # Maps class name -> list of slot names (field order)
    slotted_classes: dict[str, list[str]] = field(default_factory=dict)

    # Track variables known to be instances of slotted classes
    # Maps variable name -> class name (for optimized attribute access)
    slotted_instances: dict[str, str] = field(default_factory=dict)

    # Track global variables known to be slotted class instances
    # This persists across function compilations for module-level globals
    global_slotted_instances: dict[str, str] = field(default_factory=dict)

    def next_label_id(self) -> int:
        """Generate a unique label ID."""
        label_id = self._label_counter
        self._label_counter += 1
        return label_id

    def next_with_id(self) -> int:
        """Generate a unique with statement ID (matches analysis order)."""
        with_id = self._with_counter
        self._with_counter += 1
        return with_id

    def get_expr_type(self, node: ast.expr) -> BobType:
        """Get inferred type for expression.

        Returns UNKNOWN if type inference is disabled or type cannot be inferred.
        """
        if self.type_inferencer:
            return self.type_inferencer.infer(node)
        return UNKNOWN

    def is_native_var(self, name: str) -> bool:
        """Check if variable uses native (unboxed) WASM type."""
        return name in self.native_locals

    def get_native_type(self, name: str) -> NativeType | None:
        """Get native type for variable, or None if boxed."""
        return self.native_locals.get(name)

    def get_native_local_name(self, name: str) -> str:
        """Get WASM local name for native variable."""
        return f"$native_{name}"

    def set_native_value(self, native_type: NativeType) -> None:
        """Mark that stack top has a native (unboxed) value."""
        self.has_native_value = True
        self.current_native_type = native_type

    def clear_native_value(self) -> None:
        """Mark that stack top has a boxed value."""
        self.has_native_value = False
        self.current_native_type = None

    def register_function(self, name: str, table_idx: int) -> None:
        """Register a function for direct calling.

        Args:
            name: Function name
            table_idx: Index in WASM function table (len(BUILTINS) + func_idx)
        """
        self.func_table[name] = table_idx

    def register_spec_function(self, name: str, wasm_name: str, arity: int) -> None:
        """Register a specialized function with direct parameters.

        Args:
            name: Python function name
            wasm_name: WASM function name (e.g., $user_func_3_spec)
            arity: Number of parameters
        """
        self.spec_functions[name] = (wasm_name, arity)

    def is_slotted_class(self, class_name: str) -> bool:
        """Check if a class uses __slots__ (struct-based storage)."""
        return class_name in self.slotted_classes

    def get_slot_names(self, class_name: str) -> list[str] | None:
        """Get the slot names for a slotted class."""
        return self.slotted_classes.get(class_name)

    def get_slot_index(self, class_name: str, slot_name: str) -> int | None:
        """Get the index of a slot in a slotted class (0-based)."""
        slots = self.slotted_classes.get(class_name)
        if slots and slot_name in slots:
            return slots.index(slot_name)
        return None

    def get_slotted_type_name(self, class_name: str) -> str:
        """Get WASM struct type name for a slotted class."""
        return f"$SLOTTED_{class_name}"

    def register_slotted_instance(
        self, var_name: str, class_name: str, *, is_global: bool = False
    ) -> None:
        """Register a variable as an instance of a slotted class."""
        self.slotted_instances[var_name] = class_name
        if is_global:
            self.global_slotted_instances[var_name] = class_name

    def get_slotted_instance_class(self, var_name: str) -> str | None:
        """Get the slotted class name for a variable, if known.

        Checks both local scope and global scope.
        """
        # Check local scope first
        if var_name in self.slotted_instances:
            return self.slotted_instances[var_name]
        # Check global scope
        return self.global_slotted_instances.get(var_name)
