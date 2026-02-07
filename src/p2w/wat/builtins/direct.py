"""Direct-call builtin functions (no PAIR chain unpacking).

These are optimized versions of common builtins that take arguments
directly on the stack instead of unpacking from a PAIR chain.
This avoids allocation overhead for the most frequently used builtins.
"""

from __future__ import annotations

# Direct len: takes argument directly
# This is a simplified version that handles the most common cases
LEN_DIRECT_CODE = """
;; len_1: direct single-arg len (no PAIR unpacking)
(func $len_1 (param $val (ref null eq)) (result (ref null eq))
  (local $method_result (ref null eq))
  (local $method_name (ref $STRING))
  (local $offset i32)
  ;; Check for null
  (if (ref.is_null (local.get $val))
    (then (return (ref.i31 (i32.const 0))))
  )
  ;; $LIST length (array-backed) - O(1)
  (if (ref.test (ref $LIST) (local.get $val))
    (then
      (return (ref.i31 (struct.get $LIST $len (ref.cast (ref $LIST) (local.get $val)))))
    )
  )
  ;; TUPLE length (array-backed) - O(1)
  (if (ref.test (ref $TUPLE) (local.get $val))
    (then
      (return (ref.i31 (struct.get $TUPLE $len (ref.cast (ref $TUPLE) (local.get $val)))))
    )
  )
  ;; DICT wrapper - count entries (hash table count)
  (if (ref.test (ref $DICT) (local.get $val))
    (then
      (return (ref.i31 (struct.get $HASHTABLE $count
        (struct.get $DICT $table (ref.cast (ref $DICT) (local.get $val))))))
    )
  )
  ;; PAIR chain (list/tuple)
  (if (ref.test (ref $PAIR) (local.get $val))
    (then (return (ref.i31 (call $list_len (local.get $val)))))
  )
  ;; Bytes length (check before STRING)
  (if (ref.test (ref $BYTES) (local.get $val))
    (then
      (return (ref.i31 (struct.get $BYTES 1 (ref.cast (ref $BYTES) (local.get $val)))))
    )
  )
  ;; String length
  (if (ref.test (ref $STRING) (local.get $val))
    (then
      (return (ref.i31 (struct.get $STRING 1 (ref.cast (ref $STRING) (local.get $val)))))
    )
  )
  ;; SET length (hash table count)
  (if (ref.test (ref $SET) (local.get $val))
    (then
      (return (ref.i31 (struct.get $HASHTABLE $count
        (struct.get $SET $table (ref.cast (ref $SET) (local.get $val))))))
    )
  )
  ;; EMPTY_LIST marker
  (if (ref.test (ref $EMPTY_LIST) (local.get $val))
    (then (return (ref.i31 (i32.const 0))))
  )
  ;; OBJECT: try __len__ method
  (if (ref.test (ref $OBJECT) (local.get $val))
    (then
      ;; Create string "__len__"
      (local.set $offset (global.get $string_heap))
      (i32.store8 (local.get $offset) (i32.const 95))  ;; _
      (i32.store8 (i32.add (local.get $offset) (i32.const 1)) (i32.const 95))  ;; _
      (i32.store8 (i32.add (local.get $offset) (i32.const 2)) (i32.const 108))  ;; l
      (i32.store8 (i32.add (local.get $offset) (i32.const 3)) (i32.const 101))  ;; e
      (i32.store8 (i32.add (local.get $offset) (i32.const 4)) (i32.const 110))  ;; n
      (i32.store8 (i32.add (local.get $offset) (i32.const 5)) (i32.const 95))  ;; _
      (i32.store8 (i32.add (local.get $offset) (i32.const 6)) (i32.const 95))  ;; _
      (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 7)))
      (local.set $method_name (struct.new $STRING (local.get $offset) (i32.const 7)))
      ;; Try to call __len__ method
      (local.set $method_result (call $object_call_method
        (local.get $val)
        (local.get $method_name)
        (struct.new $PAIR (local.get $val) (ref.null eq))
        (ref.null $ENV)
      ))
      (if (i32.eqz (ref.is_null (local.get $method_result)))
        (then (return (local.get $method_result)))
      )
    )
  )
  ;; Default: 0
  (ref.i31 (i32.const 0))
)
"""

# Direct abs: takes argument directly
ABS_DIRECT_CODE = """
;; abs_1: direct single-arg abs (no PAIR unpacking)
(func $abs_1 (param $arg (ref null eq)) (result (ref null eq))
  (local $val i32)
  (local $fval f64)
  (if (ref.is_null (local.get $arg))
    (then (return (ref.i31 (i32.const 0))))
  )
  ;; Check if it's a float
  (if (ref.test (ref $FLOAT) (local.get $arg))
    (then
      (local.set $fval (struct.get $FLOAT 0 (ref.cast (ref $FLOAT) (local.get $arg))))
      (return (struct.new $FLOAT (f64.abs (local.get $fval))))
    )
  )
  ;; Integer case
  (if (ref.test (ref i31) (local.get $arg))
    (then
      (local.set $val (i31.get_s (ref.cast (ref i31) (local.get $arg))))
      (if (result (ref null eq)) (i32.lt_s (local.get $val) (i32.const 0))
        (then (ref.i31 (i32.sub (i32.const 0) (local.get $val))))
        (else (ref.i31 (local.get $val)))
      )
      (return)
    )
  )
  ;; Default: return 0
  (ref.i31 (i32.const 0))
)
"""

# Direct bool: takes argument directly
BOOL_DIRECT_CODE = """
;; bool_1: direct single-arg bool conversion (no PAIR unpacking)
(func $bool_1 (param $val (ref null eq)) (result (ref null eq))
  ;; Use is_false helper (returns i32: 1 if false, 0 if true)
  (if (result (ref null eq)) (call $is_false (local.get $val))
    (then (struct.new $BOOL (i32.const 0)))  ;; is_false=1 means value is falsy
    (else (struct.new $BOOL (i32.const 1)))  ;; is_false=0 means value is truthy
  )
)
"""

# Direct ord: takes argument directly
ORD_DIRECT_CODE = """
;; ord_1: direct single-arg ord (no PAIR unpacking)
(func $ord_1 (param $val (ref null eq)) (result (ref null eq))
  (local $offset i32)
  ;; Get first byte of string
  (if (ref.test (ref $STRING) (local.get $val))
    (then
      (local.set $offset (struct.get $STRING 0 (ref.cast (ref $STRING) (local.get $val))))
      (return (ref.i31 (i32.load8_u (local.get $offset))))
    )
  )
  ;; Error case - return 0
  (ref.i31 (i32.const 0))
)
"""

# Direct chr: takes argument directly
CHR_DIRECT_CODE = """
;; chr_1: direct single-arg chr (no PAIR unpacking)
(func $chr_1 (param $val (ref null eq)) (result (ref null eq))
  (local $code i32)
  (local $offset i32)
  ;; Get integer code point
  (if (ref.test (ref i31) (local.get $val))
    (then
      (local.set $code (i31.get_s (ref.cast (ref i31) (local.get $val))))
      (local.set $offset (global.get $string_heap))
      (i32.store8 (local.get $offset) (local.get $code))
      (global.set $string_heap (i32.add (local.get $offset) (i32.const 1)))
      (return (struct.new $STRING (local.get $offset) (i32.const 1)))
    )
  )
  ;; Error case - return empty string
  (local.set $offset (global.get $string_heap))
  (struct.new $STRING (local.get $offset) (i32.const 0))
)
"""

# Direct callable: takes argument directly
CALLABLE_DIRECT_CODE = """
;; callable_1: direct single-arg callable check (no PAIR unpacking)
(func $callable_1 (param $val (ref null eq)) (result (ref null eq))
  ;; Check if it's a closure or class
  (if (ref.test (ref $CLOSURE) (local.get $val))
    (then (return (struct.new $BOOL (i32.const 1))))
  )
  (if (ref.test (ref $CLASS) (local.get $val))
    (then (return (struct.new $BOOL (i32.const 1))))
  )
  ;; For OBJECT, check if it has __call__ method (simplified: just return false for now)
  (struct.new $BOOL (i32.const 0))
)
"""

# Combine all direct builtin code
DIRECT_BUILTINS_CODE = (
    LEN_DIRECT_CODE
    + ABS_DIRECT_CODE
    + BOOL_DIRECT_CODE
    + ORD_DIRECT_CODE
    + CHR_DIRECT_CODE
    + CALLABLE_DIRECT_CODE
)

# Map of builtin names to their direct call function names and arity
# Only include builtins that have simple, reliable implementations
# Note: chr is excluded because it requires UTF-8 encoding for values >= 128
DIRECT_BUILTINS = {
    "len": ("$len_1", 1),
    "abs": ("$abs_1", 1),
    "bool": ("$bool_1", 1),
    "ord": ("$ord_1", 1),
    "callable": ("$callable_1", 1),
}
