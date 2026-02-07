"""WAT type definitions for the p2w runtime.

These types represent the core data structures used by the compiler:
- PAIR: Cons cells for lists, dicts, and sets
- BOOL: Boolean values
- FLOAT: 64-bit floating point numbers
- INT64: 64-bit integers (for values exceeding i31 range)
- STRING: Strings stored in linear memory
- ENV: Lexical environment for closures
- CLOSURE: Function closures with captured environment
- FUNC: Function signature type
"""

from __future__ import annotations

TYPES_CODE = """
;; PAIR holds car and cdr (cons cell)
(type $PAIR (struct (field (mut (ref null eq))) (field (mut (ref null eq)))))

;; BOOL: 0 = False, nonzero = True
(type $BOOL (struct (field i32)))

;; FLOAT: 64-bit floating point
(type $FLOAT (struct (field f64)))

;; INT64: 64-bit integer (for values exceeding i31 range: -2^30 to 2^30-1)
(type $INT64 (struct (field i64)))

;; STRING: offset in linear memory + length
(type $STRING (struct (field i32) (field i32)))

;; BYTES: raw bytes in linear memory
;; Has extra tag field to make it structurally distinct from STRING
;; (WASM GC uses structural typing, so identical structures are indistinguishable)
(type $BYTES (struct (field i32) (field i32) (field i32)))

;; ENV: parent reference + values list
(type $ENV (struct (field (ref null $ENV)) (field (ref null eq))))

;; CLOSURE: environment + function table index
(type $CLOSURE (struct (field (ref null $ENV)) (field i32)))

;; FUNC: function signature (PAIR chain args + env)
(type $FUNC (func (param (ref null eq)) (param (ref null $ENV)) (result (ref null eq))))

;; Specialized function types with direct parameters (Phase 4.1 optimization)
;; These bypass PAIR chain construction/unpacking for faster calls
(type $FUNC_SPEC_0 (func (param (ref null $ENV)) (result (ref null eq))))
(type $FUNC_SPEC_1 (func (param (ref null eq)) (param (ref null $ENV)) (result (ref null eq))))
(type $FUNC_SPEC_2 (func (param (ref null eq)) (param (ref null eq)) (param (ref null $ENV)) (result (ref null eq))))
(type $FUNC_SPEC_3 (func (param (ref null eq)) (param (ref null eq)) (param (ref null eq)) (param (ref null $ENV)) (result (ref null eq))))
(type $FUNC_SPEC_4 (func (param (ref null eq)) (param (ref null eq)) (param (ref null eq)) (param (ref null eq)) (param (ref null $ENV)) (result (ref null eq))))
(type $FUNC_SPEC_5 (func (param (ref null eq)) (param (ref null eq)) (param (ref null eq)) (param (ref null eq)) (param (ref null eq)) (param (ref null $ENV)) (result (ref null eq))))

;; EMPTY_LIST: marker for empty list/set/dict (to distinguish from None)
(type $EMPTY_LIST (struct))

;; ELLIPSIS: the Ellipsis singleton (...)
;; Uses f32 field to have unique structure (no other type uses f32)
;; (WASM GC uses structural typing, so we need unique structure)
(type $ELLIPSIS (struct (field f32)))

;; =============================================================================
;; Hash Table Types for O(1) Dict/Set Operations
;; =============================================================================
;; NOTE: These must be defined BEFORE $DICT since $DICT references $HASHTABLE

;; ENTRY: hash table entry (for chaining collision resolution)
;; - hash: cached hash value for faster comparison
;; - key: the key (for dicts and sets)
;; - value: the value (for dicts, null for sets)
;; - next: next entry in chain (for collision resolution)
(type $ENTRY (struct
  (field $hash i32)
  (field $key (ref null eq))
  (field $value (mut (ref null eq)))
  (field $next (mut (ref null $ENTRY)))
))

;; BUCKET_ARRAY: array of entry pointers (hash table buckets)
(type $BUCKET_ARRAY (array (mut (ref null $ENTRY))))

;; HASHTABLE: hash table with separate chaining
;; - buckets: array of entry chains
;; - size: number of buckets (capacity)
;; - count: number of entries (for load factor calculation)
(type $HASHTABLE (struct
  (field $buckets (mut (ref $BUCKET_ARRAY)))
  (field $size i32)
  (field $count (mut i32))
))

;; DICT: dictionary using hash table for O(1) operations
(type $DICT (struct (field $table (ref $HASHTABLE))))

;; DICT_V2: legacy alias for hash table dict (kept for backwards compat)
(type $DICT_V2 (struct (field $table (ref $HASHTABLE))))

;; SET: set using hash table for O(1) operations
(type $SET (struct (field $table (ref $HASHTABLE))))

;; =============================================================================
;; Class and Object Types
;; =============================================================================

;; CLASS: class metadata
;; - name: class name (STRING)
;; - methods: method dict (PAIR chain of name->closure pairs)
;; - base: base class reference (for inheritance, null if none)
(type $CLASS (struct
  (field $name (ref $STRING))
  (field $methods (mut (ref null eq)))
  (field $base (ref null $CLASS))
))

;; INSTANCE_BASE: base type for all class instances (both regular and slotted)
;; This enables isinstance() to work with both OBJECT and SLOTTED_* types
;; Marked as (sub ...) without 'final' to allow extension by OBJECT and slotted types
(type $INSTANCE_BASE (sub (struct
  (field $class (ref $CLASS))
)))

;; OBJECT: instance of a user-defined class (without __slots__)
;; - class: reference to the class
;; - attrs: attribute dict (PAIR chain of name->value pairs)
(type $OBJECT (sub final $INSTANCE_BASE (struct
  (field $class (ref $CLASS))
  (field $attrs (mut (ref null eq)))
)))

;; SUPER: super() proxy for calling parent methods
;; - class: the parent class to look up methods in
;; - self: the object instance to pass as self
(type $SUPER (struct
  (field $class (ref $CLASS))
  (field $self (ref $OBJECT))
))

;; STATICMETHOD: wrapper for static methods (no self parameter)
;; Has extra padding field to distinguish from CLASSMETHOD (WASM GC uses structural typing)
(type $STATICMETHOD (struct (field $closure (ref $CLOSURE)) (field $padding i32)))

;; CLASSMETHOD: wrapper for class methods (receives class as first arg)
;; Has different field order to distinguish from STATICMETHOD (WASM GC uses structural typing)
(type $CLASSMETHOD (struct (field $padding i32) (field $closure (ref $CLOSURE))))

;; PROPERTY: property descriptor with getter, setter, and deleter
;; - getter: the getter closure (called on attribute access)
;; - setter: the setter closure (called on attribute assignment, null if read-only)
;; - deleter: the deleter closure (called on del, null if not deletable)
(type $PROPERTY (struct
  (field $getter (ref null $CLOSURE))
  (field $setter (mut (ref null $CLOSURE)))
  (field $deleter (mut (ref null $CLOSURE)))
))

;; =============================================================================
;; Collection Types
;; =============================================================================

;; ARRAY_ANY: growable array of any values (for array-backed lists)
(type $ARRAY_ANY (array (mut (ref null eq))))

;; LIST: array-backed list with O(1) indexed access
;; - data: the underlying array
;; - len: number of elements currently in use
;; - cap: total capacity of the array
(type $LIST (struct
  (field $data (mut (ref $ARRAY_ANY)))
  (field $len (mut i32))
  (field $cap (mut i32))
))

;; TUPLE: immutable sequence (uses array for O(1) access)
;; Unlike LIST, tuples are immutable so we don't need cap field
(type $TUPLE (struct
  (field $data (ref $ARRAY_ANY))
  (field $len i32)
))

;; =============================================================================
;; Exception Handling Types
;; =============================================================================

;; EXCEPTION: Python exception object
;; - type: exception class name (e.g., "ValueError", "TypeError")
;; - message: error message (can be any value for complex exceptions)
;; - cause: the __cause__ attribute (for exception chaining)
;; - context: the __context__ attribute (implicit chaining)
(type $EXCEPTION (struct
  (field $type (ref $STRING))
  (field $message (ref null eq))
  (field $cause (ref null eq))
  (field $context (ref null eq))
))

;; Exception tag for WASM exception handling
(tag $PyException (param (ref $EXCEPTION)))

;; =============================================================================
;; Generator Types
;; =============================================================================

;; GENERATOR: Python generator object (created by calling a generator function)
;; - state: current state in the state machine (0 = initial, -1 = exhausted)
;; - value: last yielded value
;; - locals: PAIR chain of saved local variables (preserved across yields)
;; - func_idx: function table index of the generator body
;; - env: lexical environment for closures
;; - sent_value: value passed via send() (for "result = yield x" expressions)
(type $GENERATOR (struct
  (field $state (mut i32))
  (field $value (mut (ref null eq)))
  (field $locals (mut (ref null eq)))
  (field $func_idx i32)
  (field $env (ref null $ENV))
  (field $sent_value (mut (ref null eq)))
))

;; StopIteration tag for generator exhaustion
(tag $StopIteration)
"""
