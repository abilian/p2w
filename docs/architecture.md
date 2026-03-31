# p2w Architecture

This document describes the architecture of the p2w Python-to-WebAssembly compiler.

This is based on the 0.2.2 version.

## Overview

p2w is an ahead-of-time (AOT) compiler that translates Python source code to WebAssembly Text format (WAT), which can then be converted to WASM binary using, e.g., `wasm-tools`. The compiler leverages WASM GC (Garbage Collection) for automatic memory management.

```
Python Source → AST → Inlining → Analysis → Type Inference → Code Generation → WAT → WASM
```

## Compilation Pipeline

### Phase 1: Parsing

Python source code is parsed using Python's built-in `ast` module:

```python
import ast
tree = ast.parse(source_code)
```

This produces a standard Python AST that subsequent phases analyze and transform.

### Phase 2: Function Inlining

**Module:** `src/p2w/compiler/inlining.py`

Before analysis, the compiler performs AST-level function inlining. Small, non-recursive functions (single-expression bodies, simple arithmetic helpers) are inlined at their call sites. This eliminates call overhead and enables native type propagation across the inlined code.

Candidates are scored by estimated code size and static call count. Functions that are recursive, contain nested functions, or use try/except are excluded.

### Phase 3: Analysis

**Module:** `src/p2w/compiler/analysis.py`

Pre-compilation analysis extracts information needed for code generation:

- **Variable collection**: `collect_local_vars()` identifies all local variables assigned in a function body (shallow — doesn't recurse into nested functions)
- **Iterator locals**: `collect_iter_locals()` finds `$iter_x` locals needed for for-loop iterators
- **Comprehension locals**: `collect_comprehension_locals()` allocates locals for list/dict/set comprehension loop variables, iterators, and result accumulators
- **With-statement locals**: `collect_with_locals()` allocates `$with_cm_N` / `$with_method_N` locals for context managers
- **Named expression vars**: `collect_namedexpr_vars()` finds walrus operator (`x := value`) assignments
- **Free variables**: `find_free_vars_in_func()` identifies variables captured by closures
- **Generator detection**: `is_generator_function()` and `collect_yield_points()` identify generator functions and their yield locations
- **Exception handling**: `has_try_except()` and `has_try_finally()` determine which locals are needed for exception state
- **Scope declarations**: `collect_global_decls()` and `collect_nonlocal_decls()` find `global` and `nonlocal` statements
- **Module-level declarations**: `collect_class_names()`, `collect_function_names()`, `collect_module_level_vars()` for forward reference resolution

Internal helpers (`_SkipNestedScopes` base class, `_collect_decls`, `_has_try_feature`) eliminate duplication across these functions.

### Phase 4: Type Inference

**Module:** `src/p2w/compiler/inference.py`

The `TypeInferencer` class performs forward-flow type analysis:

1. **Constant types**: Infers types from literal values (`42` → INT, `3.14` → FLOAT)
2. **Annotation parsing**: Reads type hints including native types (`i32`, `i64`, `f64`) and parameterized types (`list[float]`, `dict[str, int]`)
3. **Operation result types**: Determines result types of binary/unary operations and known function calls
4. **Native type eligibility**: Escape analysis identifies variables that can use unboxed native WASM types. A variable "escapes" if it's passed to a function, stored in a collection, returned, or used in attribute access. Float variables that don't escape are promoted to `f64`. Loop counter variables over small ranges are promoted to `i32`.

**Type hierarchy:**

```
BaseType (base)
├── IntType     - Boxed Python int (i31 or INT64)
├── FloatType   - Boxed Python float
├── StringType  - Python str
├── BoolType    - Python bool
├── NoneType    - Python None
├── ListType    - Python list (optionally parameterized: ListType(INT))
├── DictType    - Python dict (optionally parameterized: DictType(STRING, INT))
├── TupleType   - Python tuple (optionally parameterized: TupleType((INT, FLOAT)))
├── NativeType  - Native WASM types:
│   ├── I32     - Native WASM i32 (unboxed)
│   ├── I64     - Native WASM i64 (unboxed)
│   └── F64     - Native WASM f64 (unboxed)
└── UnknownType - Type not known at compile time
```

### Phase 5: Code Generation

**Modules:** `src/p2w/compiler/codegen/`

Code generation uses a visitor pattern with singledispatch:

```python
@singledispatch
def compile_expr(node: ast.expr, ctx: CompilerContext) -> None:
    """Compile an expression, leaving result on stack."""
    ...

@singledispatch
def compile_stmt(node: ast.stmt, ctx: CompilerContext) -> None:
    """Compile a statement."""
    ...
```

Handlers are registered in separate modules to keep file sizes manageable. The codegen directory contains specialized modules for expressions, statements, functions, classes, closures, generators, operators, collections, comprehensions, subscript/slicing, control flow, exception handling, pattern matching, f-strings, lambdas, variable access, attribute access, unpacking, context managers, calls (including built-in function dispatch), and JavaScript interop.

**Import order constraint:** The base dispatcher modules (`expressions.py`, `statements.py`) must be imported before their handler modules (`expr_handlers.py`, `stmt_handlers.py`) due to singledispatch registration.

### Phase 6: WAT Emission

**Module:** `src/p2w/emitter.py`

The `WATEmitter` class handles all WAT code output:

- **Indentation management**: Automatic indent/dedent for readable output
- **String interning**: Deduplicates string constants, assigns linear memory offsets
- **Type-specific emission**: Methods for each value type (int, float, string, bool, etc.)

### Phase 7: Assembly

**External tool:** `wasm-tools`

The generated WAT is assembled to WASM binary:

```bash
wasm-tools parse code.wat -o code.wasm
```

## Module Structure

The WAT output is structured as a single WASM module containing:

1. **Imports** (`wat/imports.py`) — Host function imports for I/O (`write_char`, `write_i32`, etc.), float formatting, math, and optionally JavaScript DOM/Canvas operations
2. **Type definitions** (`wat/types.py`) — WASM GC struct/array types for all runtime values
3. **Globals** — Module-level variables (one `(global (mut (ref null eq)))` per global)
4. **Built-in functions** (`wat/builtins/`) — WAT implementations of Python builtins (`len`, `print`, `range`, `isinstance`, `sorted`, `map`, etc.)
5. **Helper functions** (`wat/helpers/`) — Runtime support for strings, lists, tuples, dicts, sets, integers, arithmetic, comparisons, sorting, exceptions, generators, and JS interop
6. **User functions** — Compiled user code, each as a `$user_func_N`
7. **Specialized functions** — Optimized direct-call versions of hot functions (bypass PAIR chain arg passing)
8. **Function table** — `funcref` table enabling indirect calls and closures
9. **Memory and data section** — Linear memory with interned string data

## Runtime Architecture

### WASM GC Types

All Python objects live on the WASM GC heap. Core types:

| WAT Type | Purpose | Fields |
|---|---|---|
| `$PAIR` | Cons cell (arg passing, linked lists) | `car`, `cdr` (both `ref null eq`) |
| `$FLOAT` | Boxed float | `f64` |
| `$INT64` | Large integer (outside i31 range) | `i64` |
| `$STRING` | String | `offset: i32`, `length: i32` (into linear memory) |
| `$BYTES` | Byte string | `offset: i32`, `length: i32`, `tag: i32` |
| `$LIST` | Array-backed list | `data: ref $ARRAY_ANY`, `len: i32`, `cap: i32` |
| `$TUPLE` | Immutable sequence | `data: ref $ARRAY_ANY`, `len: i32` |
| `$DICT` | Hash table dictionary | `table: ref $HASHTABLE` |
| `$SET` | Hash table set | `table: ref $HASHTABLE` |
| `$CLOSURE` | Function closure | `env: ref null $ENV`, `func_idx: i32` |
| `$ENV` | Lexical environment frame | `parent: ref null $ENV`, `value: ref null eq` |
| `$CLASS` | Class metadata | `name`, `methods`, `base` |
| `$OBJECT` | Class instance | `class: ref $CLASS`, `attrs` (PAIR chain) |
| `$EXCEPTION` | Exception object | `type`, `message`, `cause`, `context` |
| `$GENERATOR` | Generator state machine | `state`, `value`, `locals`, `func_idx`, `env`, `sent_value` |

Slotted classes (with `__slots__`) get custom struct types with named fields instead of the generic `$OBJECT` attribute dict.

### Integer Representation

- **i31ref**: Small integers (-2^30 to 2^30-1) stored inline as WASM i31ref — no allocation
- **INT64**: Large integers boxed in an `$INT64` struct on the GC heap
- **Native i32/i64**: When type inference proves a variable doesn't escape, it can be stored as an unboxed WASM local

### Memory Layout

- **GC heap**: All objects are WASM GC managed — no manual allocation or freeing
- **Linear memory**: Used exclusively for string/bytes data. Strings are interned at compile time starting at offset 2048. Runtime string operations (concatenation, f-strings) allocate from a bump pointer.

### Function Calling Convention

Functions use a uniform signature: `(param $args (ref null eq)) (param $env (ref null $ENV)) (result (ref null eq))`. Arguments are passed as a PAIR chain (linked list of cons cells). The environment carries captured variables for closures.

**Specialized functions** (an optimization for hot paths) use direct parameters instead of PAIR chains, avoiding allocation and unpacking overhead.

Functions are stored in a `funcref` table and called via `call_indirect`. This enables closures (a closure is an environment pointer + table index) and first-class functions.

### JavaScript Interop

When `import js` is detected, the compiler enables a handle-based bridge to JavaScript:

- JS objects are represented as opaque i31 handles (indices into a JS-side object table)
- Reserved handles: `1=document`, `2=window`, `3=console`
- The compiler tracks which variables hold JS handles (`js_handle_vars`) for proper method dispatch
- ~25 common DOM/Canvas methods have specialized WAT wrappers; unrecognized methods fall back to a generic `$js_call_method` path
- Strings are passed to JS as `(offset, length)` pairs from linear memory
- Event handlers use a callback table: closures are registered in WASM, JS calls back with `event_callback(callbackIdx, eventHandle)`

See `js-interop.md` for full details.

## Compiler Context

**Module:** `src/p2w/compiler/context.py`

The `CompilerContext` dataclass carries all compilation state through the codegen phase:

```python
@dataclass
class CompilerContext:
    emitter: WATEmitter

    # Scope tracking
    lexical_env: LexicalEnv          # Compile-time variable resolution
    global_vars: set[str]            # Module-level globals
    current_global_decls: set[str]   # 'global' decls in current function
    current_nonlocal_decls: set[str] # 'nonlocal' decls in current function
    cell_vars: set[str]              # Variables accessed by nested nonlocals
    local_vars: dict[str, str]       # name -> WASM local name

    # Type inference
    type_inferencer: TypeInferencer | None
    native_locals: dict[str, NativeType]  # Unboxed variables
    has_native_value: bool                # Current stack value is unboxed
    current_native_type: NativeType | None

    # Function compilation
    user_funcs: list[StringIO]            # Buffered function code
    spec_func_code: list[StringIO]        # Specialized function code
    func_table: dict[str, int]            # name -> table index
    spec_functions: dict[str, tuple[str, int]]  # name -> (wasm_name, arity)
    func_signatures: dict[str, FunctionSignature]  # For kwargs support

    # Class compilation
    current_class: str | None
    slotted_classes: dict[str, list[str]]  # class -> slot names

    # Generator compilation
    generator_context: GeneratorContext | None

    # JavaScript interop
    js_imported: bool
    js_handle_vars: set[str]

    # Optimizations
    safe_bounds: dict[str, tuple[str, str]]  # Loop bounds elimination
```

## Execution

### Node.js Runner

**Module:** `src/p2w/runner.py`

The `p2w -r` command compiles Python to WAT, assembles to WASM via `wasm-tools`, and runs it under Node.js. The runner generates a JavaScript host module that provides:

- **I/O**: `write_char`, `write_i32`, `write_i64`, `write_f64` — byte-level output
- **Float formatting**: `f64_to_string`, `f64_format_precision` — Python-compatible float repr
- **Math**: `math_pow` — non-integer exponentiation

The host instantiates the WASM module with these imports, calls `_start()`, and captures stdout.

### Browser Runner

**Module:** `src/p2w/browser_runner.py`

For browser demos, a `loader.js` provides the same I/O imports plus DOM/Canvas operations. See `demos/` for working examples.

## Extension Points

### Adding a new Python feature

1. **Analysis**: Add collection functions in `analysis.py` if new locals or scope information are needed
2. **Type inference**: Add type rules in `inference.py` (e.g., new builtin return types)
3. **Expression handler**: Register a new `@compile_expr.register` handler in the appropriate codegen module
4. **Statement handler**: Register a new `@compile_stmt.register` handler
5. **WAT helpers**: Add runtime support functions in `wat/helpers/`

### Adding a new built-in function

1. Add WAT implementation in `wat/builtins/`
2. Add call dispatch in `codegen/calls.py`
3. Add type inference rules in `inference.py`
4. Register the builtin in `compiler/builtins.py`
