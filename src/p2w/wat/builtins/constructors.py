"""WAT builtin functions: Type constructor functions (int, str, list, etc.)."""

from __future__ import annotations

INT_CODE = """
(func $int (param $args (ref null eq)) (param $env (ref null $ENV)) (result (ref null eq))
  (local $val (ref null eq))
  (local $base i32)
  (local $arg2 (ref null eq))
  (if (ref.is_null (local.get $args))
    (then (return (ref.i31 (i32.const 0))))
  )
  (local.set $val (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))
  ;; Check for second argument (base)
  (local.set $arg2 (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $args))))
  (if (ref.is_null (local.get $arg2))
    (then (local.set $base (i32.const 10)))
    (else (local.set $base (i31.get_s (ref.cast (ref i31)
      (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $arg2)))))))
  )
  ;; Already an integer (ignore base)
  (if (ref.test (ref i31) (local.get $val))
    (then (return (local.get $val)))
  )
  ;; Bool - 0 or 1
  (if (ref.test (ref $BOOL) (local.get $val))
    (then (return (ref.i31 (struct.get $BOOL 0 (ref.cast (ref $BOOL) (local.get $val))))))
  )
  ;; Float - truncate
  (if (ref.test (ref $FLOAT) (local.get $val))
    (then (return (ref.i31 (i32.trunc_f64_s
      (struct.get $FLOAT 0 (ref.cast (ref $FLOAT) (local.get $val)))))))
  )
  ;; String - parse with base
  (if (ref.test (ref $STRING) (local.get $val))
    (then (return (ref.i31 (call $parse_int_base
      (ref.cast (ref $STRING) (local.get $val))
      (local.get $base)))))
  )
  ;; Default return 0
  (ref.i31 (i32.const 0))
)
"""

BOOL_CODE = """
(func $bool (param $args (ref null eq)) (param $env (ref null $ENV)) (result (ref null eq))
  (local $val (ref null eq))
  (if (ref.is_null (local.get $args))
    (then (return (struct.new $BOOL (i32.const 0))))
  )
  (local.set $val (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))
  ;; Use is_false to check truthiness
  (if (result (ref null eq)) (call $is_false (local.get $val))
    (then (struct.new $BOOL (i32.const 0)))
    (else (struct.new $BOOL (i32.const 1)))
  )
)
"""

STR_CODE = """
(func $str (param $args (ref null eq)) (param $env (ref null $ENV)) (result (ref null eq))
  (local $val (ref null eq))
  (local $method_result (ref null eq))
  (local $method_name (ref $STRING))
  (local $offset i32)
  (local $bytes_off i32)
  (local $bytes_len i32)
  (local $i i32)
  (if (ref.is_null (local.get $args))
    (then (return (struct.new $STRING (i32.const 0) (i32.const 0))))
  )
  (local.set $val (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))

  ;; Check for str(bytes, encoding) - decode bytes to string
  ;; If second arg exists and first arg is $BYTES, decode
  (if (i32.eqz (ref.is_null (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $args)))))
    (then
      (if (ref.test (ref $BYTES) (local.get $val))
        (then
          ;; Get bytes offset and length
          (local.set $bytes_off (struct.get $BYTES 0 (ref.cast (ref $BYTES) (local.get $val))))
          (local.set $bytes_len (struct.get $BYTES 1 (ref.cast (ref $BYTES) (local.get $val))))
          ;; Allocate new string and copy bytes (UTF-8 passthrough)
          (local.set $offset (global.get $string_heap))
          (local.set $i (i32.const 0))
          (block $done
            (loop $copy
              (br_if $done (i32.ge_u (local.get $i) (local.get $bytes_len)))
              (i32.store8 (i32.add (local.get $offset) (local.get $i))
                (i32.load8_u (i32.add (local.get $bytes_off) (local.get $i))))
              (local.set $i (i32.add (local.get $i) (i32.const 1)))
              (br $copy)
            )
          )
          (global.set $string_heap (i32.add (local.get $offset) (local.get $bytes_len)))
          (return (struct.new $STRING (local.get $offset) (local.get $bytes_len)))
        )
      )
    )
  )

  ;; Check for OBJECT with __str__ special method
  (if (ref.test (ref $OBJECT) (local.get $val))
    (then
      ;; Create string "__str__" (7 chars: 95,95,115,116,114,95,95)
      (local.set $offset (global.get $string_heap))
      (i32.store8 (local.get $offset) (i32.const 95))  ;; _
      (i32.store8 (i32.add (local.get $offset) (i32.const 1)) (i32.const 95))  ;; _
      (i32.store8 (i32.add (local.get $offset) (i32.const 2)) (i32.const 115))  ;; s
      (i32.store8 (i32.add (local.get $offset) (i32.const 3)) (i32.const 116))  ;; t
      (i32.store8 (i32.add (local.get $offset) (i32.const 4)) (i32.const 114))  ;; r
      (i32.store8 (i32.add (local.get $offset) (i32.const 5)) (i32.const 95))  ;; _
      (i32.store8 (i32.add (local.get $offset) (i32.const 6)) (i32.const 95))  ;; _
      (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 7)))
      (local.set $method_name (struct.new $STRING (local.get $offset) (i32.const 7)))

      ;; Call __str__(self) - args = (PAIR self null)
      (local.set $method_result (call $object_call_method
        (local.get $val)
        (local.get $method_name)
        (struct.new $PAIR (local.get $val) (ref.null eq))
        (local.get $env)
      ))
      ;; If method returned a value, use it
      (if (i32.eqz (ref.is_null (local.get $method_result)))
        (then (return (local.get $method_result)))
      )
    )
  )

  ;; Use value_to_string which handles all types
  (call $value_to_string (local.get $val))
)
"""

FLOAT_CODE = """
(func $float (param $args (ref null eq)) (param $env (ref null $ENV)) (result (ref null eq))
  (local $val (ref null eq))
  (if (ref.is_null (local.get $args))
    (then (return (struct.new $FLOAT (f64.const 0))))
  )
  (local.set $val (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))
  ;; Already a float
  (if (ref.test (ref $FLOAT) (local.get $val))
    (then (return (local.get $val)))
  )
  ;; Integer - convert
  (if (ref.test (ref i31) (local.get $val))
    (then (return (struct.new $FLOAT
      (f64.convert_i32_s (i31.get_s (ref.cast (ref i31) (local.get $val)))))))
  )
  ;; String - parse
  (if (ref.test (ref $STRING) (local.get $val))
    (then (return (struct.new $FLOAT
      (call $parse_float (ref.cast (ref $STRING) (local.get $val))))))
  )
  ;; Default return 0.0
  (struct.new $FLOAT (f64.const 0))
)
"""

LIST_CODE = """
(func $list (param $args (ref null eq)) (param $env (ref null $ENV)) (result (ref null eq))
  (local $val (ref null eq))
  (local $str (ref $STRING))
  (local $off i32)
  (local $len i32)
  (local $i i32)
  (local $char_off i32)
  (local $result (ref null eq))
  ;; No args: return empty list
  (if (ref.is_null (local.get $args))
    (then (return (struct.new $EMPTY_LIST)))
  )
  (local.set $val (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))
  ;; If already a $LIST (array-backed), copy it (preserve $LIST format)
  (if (ref.test (ref $LIST) (local.get $val))
    (then (return (call $list_v2_copy (ref.cast (ref $LIST) (local.get $val)))))
  )
  ;; If already a PAIR chain, convert to $LIST
  (if (ref.test (ref $PAIR) (local.get $val))
    (then (return (call $pair_to_list_v2 (local.get $val))))
  )
  ;; If $EMPTY_LIST, return new empty list
  (if (ref.test (ref $EMPTY_LIST) (local.get $val))
    (then (return (struct.new $EMPTY_LIST)))
  )
  ;; If TUPLE, convert to PAIR chain
  (if (ref.test (ref $TUPLE) (local.get $val))
    (then (return (call $tuple_to_pair (ref.cast (ref $TUPLE) (local.get $val)))))
  )
  ;; If STRING, convert to list of single-character strings
  (if (ref.test (ref $STRING) (local.get $val))
    (then
      (local.set $str (ref.cast (ref $STRING) (local.get $val)))
      (local.set $off (struct.get $STRING 0 (local.get $str)))
      (local.set $len (struct.get $STRING 1 (local.get $str)))
      ;; Empty string -> empty list
      (if (i32.eqz (local.get $len))
        (then (return (struct.new $EMPTY_LIST)))
      )
      ;; Build list from back to front
      (local.set $result (ref.null eq))
      (local.set $i (i32.sub (local.get $len) (i32.const 1)))
      (block $done
        (loop $loop
          (br_if $done (i32.lt_s (local.get $i) (i32.const 0)))
          ;; Create single-char string
          (local.set $char_off (global.get $string_heap))
          (i32.store8 (local.get $char_off)
            (i32.load8_u (i32.add (local.get $off) (local.get $i))))
          (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 1)))
          ;; Prepend to result
          (local.set $result
            (struct.new $PAIR
              (struct.new $STRING (local.get $char_off) (i32.const 1))
              (local.get $result)))
          (local.set $i (i32.sub (local.get $i) (i32.const 1)))
          (br $loop)
        )
      )
      (return (local.get $result))
    )
  )
  ;; If GENERATOR, eagerly consume into list
  (if (ref.test (ref $GENERATOR) (local.get $val))
    (then
      (return (call $generator_to_list (local.get $val)))
    )
  )
  ;; For other types, return empty list
  (struct.new $EMPTY_LIST)
)
"""

DICT_CODE = """
(func $dict (param $args (ref null eq)) (param $env (ref null $ENV)) (result (ref null eq))
  (local $arg (ref null eq))
  ;; dict() with no args -> empty dict (hash table based)
  (if (ref.is_null (local.get $args))
    (then (return (call $dict_new)))
  )
  ;; Get the first argument
  (local.set $arg (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))
  ;; If already a $DICT, copy it
  (if (ref.test (ref $DICT) (local.get $arg))
    (then (return (call $dict_copy (local.get $arg))))
  )
  ;; Otherwise, copy from a PAIR chain or other iterable
  (call $dict_copy (local.get $arg))
)
"""

TUPLE_CODE = """
(func $tuple (param $args (ref null eq)) (param $env (ref null $ENV)) (result (ref null eq))
  (local $val (ref null eq))
  (local $str (ref $STRING))
  (local $off i32)
  (local $len i32)
  (local $i i32)
  (local $char_off i32)
  (local $result (ref null eq))
  ;; No args: return empty tuple (represented as empty list)
  (if (ref.is_null (local.get $args))
    (then (return (struct.new $EMPTY_LIST)))
  )
  (local.set $val (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))
  ;; If $LIST (array-backed), convert to PAIR chain
  (if (ref.test (ref $LIST) (local.get $val))
    (then (return (call $list_v2_to_pair (ref.cast (ref $LIST) (local.get $val)))))
  )
  ;; If already a PAIR chain, copy it
  (if (ref.test (ref $PAIR) (local.get $val))
    (then (return (call $list_copy (local.get $val))))
  )
  ;; If $TUPLE, convert to PAIR chain
  (if (ref.test (ref $TUPLE) (local.get $val))
    (then (return (call $tuple_to_pair (ref.cast (ref $TUPLE) (local.get $val)))))
  )
  ;; If $EMPTY_LIST, return new empty
  (if (ref.test (ref $EMPTY_LIST) (local.get $val))
    (then (return (struct.new $EMPTY_LIST)))
  )
  ;; If STRING, convert to tuple of single-character strings
  (if (ref.test (ref $STRING) (local.get $val))
    (then
      (local.set $str (ref.cast (ref $STRING) (local.get $val)))
      (local.set $off (struct.get $STRING 0 (local.get $str)))
      (local.set $len (struct.get $STRING 1 (local.get $str)))
      ;; Empty string -> empty tuple
      (if (i32.eqz (local.get $len))
        (then (return (struct.new $EMPTY_LIST)))
      )
      ;; Build list from back to front
      (local.set $result (ref.null eq))
      (local.set $i (i32.sub (local.get $len) (i32.const 1)))
      (block $done
        (loop $loop
          (br_if $done (i32.lt_s (local.get $i) (i32.const 0)))
          ;; Create single-char string
          (local.set $char_off (global.get $string_heap))
          (i32.store8 (local.get $char_off)
            (i32.load8_u (i32.add (local.get $off) (local.get $i))))
          (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 1)))
          ;; Prepend to result
          (local.set $result
            (struct.new $PAIR
              (struct.new $STRING (local.get $char_off) (i32.const 1))
              (local.get $result)))
          (local.set $i (i32.sub (local.get $i) (i32.const 1)))
          (br $loop)
        )
      )
      (return (local.get $result))
    )
  )
  ;; For other types, return empty tuple
  (struct.new $EMPTY_LIST)
)
"""

SET_CODE = """
(func $set (param $args (ref null eq)) (param $env (ref null $ENV)) (result (ref null eq))
  (local $val (ref null eq))
  (local $current (ref null eq))
  (local $result (ref null eq))
  (local $elem (ref null eq))
  ;; No args: return empty set
  (if (ref.is_null (local.get $args))
    (then (return (struct.new $EMPTY_LIST)))
  )
  (local.set $val (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))
  ;; If $LIST (array-backed), use list_to_set
  (if (ref.test (ref $LIST) (local.get $val))
    (then (return (call $list_to_set (local.get $val))))
  )
  ;; If already a PAIR chain, deduplicate it
  (if (ref.test (ref $PAIR) (local.get $val))
    (then
      ;; Build deduplicated result by iterating and checking for duplicates
      (local.set $result (ref.null eq))
      (local.set $current (local.get $val))
      (block $done
        (loop $loop
          (br_if $done (ref.is_null (local.get $current)))
          (if (i32.eqz (ref.test (ref $PAIR) (local.get $current)))
            (then (br $done))
          )
          (local.set $elem (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $current))))
          ;; Check if elem is already in result
          (if (i32.eqz (call $list_contains (local.get $elem) (local.get $result)))
            (then
              ;; Add to result
              (local.set $result (struct.new $PAIR (local.get $elem) (local.get $result)))
            )
          )
          (local.set $current (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current))))
          (br $loop)
        )
      )
      ;; Reverse to maintain original order (first occurrence)
      (return (call $list_reverse (local.get $result)))
    )
  )
  ;; If $EMPTY_LIST, return new empty set
  (if (ref.test (ref $EMPTY_LIST) (local.get $val))
    (then (return (struct.new $EMPTY_LIST)))
  )
  ;; For other types, return empty set
  (struct.new $EMPTY_LIST)
)
"""

BYTES_CODE = """
;; bytes() constructor
;; bytes() -> empty bytes
;; bytes(n) -> zero-filled bytes of length n
;; bytes([i1, i2, ...]) -> bytes from list of ints
;; bytes("str", "utf-8") -> bytes from string encoding
(func $bytes (param $args (ref null eq)) (param $env (ref null $ENV)) (result (ref null eq))
  (local $arg1 (ref null eq))
  (local $arg2 (ref null eq))
  (local $offset i32)
  (local $len i32)
  (local $i i32)
  (local $current (ref null eq))
  (local $byte_val i32)
  (local $str_off i32)
  (local $str_len i32)
  ;; No arguments -> empty bytes
  (if (ref.is_null (local.get $args))
    (then (return (struct.new $BYTES (i32.const 0) (i32.const 0) (i32.const 0))))
  )
  (local.set $arg1 (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))

  ;; Check for second argument (encoding)
  (if (i32.eqz (ref.is_null (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $args)))))
    (then
      ;; bytes(str, encoding) - convert string to bytes
      ;; For now, just copy UTF-8 bytes
      (if (ref.test (ref $STRING) (local.get $arg1))
        (then
          (local.set $str_off (struct.get $STRING 0 (ref.cast (ref $STRING) (local.get $arg1))))
          (local.set $str_len (struct.get $STRING 1 (ref.cast (ref $STRING) (local.get $arg1))))
          (local.set $offset (global.get $string_heap))
          ;; Copy bytes
          (local.set $i (i32.const 0))
          (block $done
            (loop $copy
              (br_if $done (i32.ge_u (local.get $i) (local.get $str_len)))
              (i32.store8 (i32.add (local.get $offset) (local.get $i))
                (i32.load8_u (i32.add (local.get $str_off) (local.get $i))))
              (local.set $i (i32.add (local.get $i) (i32.const 1)))
              (br $copy)
            )
          )
          (global.set $string_heap (i32.add (local.get $offset) (local.get $str_len)))
          (return (struct.new $BYTES (local.get $offset) (local.get $str_len) (i32.const 0)))
        )
      )
    )
  )

  ;; bytes(n) - zero-filled bytes
  (if (ref.test (ref i31) (local.get $arg1))
    (then
      (local.set $len (i31.get_s (ref.cast (ref i31) (local.get $arg1))))
      (if (i32.le_s (local.get $len) (i32.const 0))
        (then (return (struct.new $BYTES (i32.const 0) (i32.const 0) (i32.const 0))))
      )
      (local.set $offset (global.get $string_heap))
      ;; Fill with zeros
      (local.set $i (i32.const 0))
      (block $done
        (loop $fill
          (br_if $done (i32.ge_s (local.get $i) (local.get $len)))
          (i32.store8 (i32.add (local.get $offset) (local.get $i)) (i32.const 0))
          (local.set $i (i32.add (local.get $i) (i32.const 1)))
          (br $fill)
        )
      )
      (global.set $string_heap (i32.add (local.get $offset) (local.get $len)))
      (return (struct.new $BYTES (local.get $offset) (local.get $len) (i32.const 0)))
    )
  )

  ;; bytes([i1, i2, ...]) - from list of ints
  (if (ref.test (ref $PAIR) (local.get $arg1))
    (then
      (local.set $len (call $list_len (local.get $arg1)))
      (if (i32.eqz (local.get $len))
        (then (return (struct.new $BYTES (i32.const 0) (i32.const 0) (i32.const 0))))
      )
      (local.set $offset (global.get $string_heap))
      (local.set $current (local.get $arg1))
      (local.set $i (i32.const 0))
      (block $done
        (loop $conv
          (br_if $done (ref.is_null (local.get $current)))
          (br_if $done (i32.eqz (ref.test (ref $PAIR) (local.get $current))))
          ;; Get byte value
          (local.set $byte_val (i31.get_s (ref.cast (ref i31)
            (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $current))))))
          (i32.store8 (i32.add (local.get $offset) (local.get $i)) (local.get $byte_val))
          (local.set $i (i32.add (local.get $i) (i32.const 1)))
          (local.set $current (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current))))
          (br $conv)
        )
      )
      (global.set $string_heap (i32.add (local.get $offset) (local.get $i)))
      (return (struct.new $BYTES (local.get $offset) (local.get $i) (i32.const 0)))
    )
  )

  ;; bytes from $LIST (array-backed)
  (if (ref.test (ref $LIST) (local.get $arg1))
    (then
      (local.set $len (struct.get $LIST $len (ref.cast (ref $LIST) (local.get $arg1))))
      (if (i32.eqz (local.get $len))
        (then (return (struct.new $BYTES (i32.const 0) (i32.const 0) (i32.const 0))))
      )
      (local.set $offset (global.get $string_heap))
      (local.set $i (i32.const 0))
      (block $done
        (loop $conv
          (br_if $done (i32.ge_s (local.get $i) (local.get $len)))
          (local.set $byte_val (i31.get_s (ref.cast (ref i31)
            (call $list_v2_get (ref.cast (ref $LIST) (local.get $arg1)) (local.get $i)))))
          (i32.store8 (i32.add (local.get $offset) (local.get $i)) (local.get $byte_val))
          (local.set $i (i32.add (local.get $i) (i32.const 1)))
          (br $conv)
        )
      )
      (global.set $string_heap (i32.add (local.get $offset) (local.get $len)))
      (return (struct.new $BYTES (local.get $offset) (local.get $len) (i32.const 0)))
    )
  )

  ;; Fallback: empty bytes
  (struct.new $BYTES (i32.const 0) (i32.const 0) (i32.const 0))
)
"""

# Combined code for this module
CONSTRUCTORS_CODE = (
    INT_CODE
    + BOOL_CODE
    + STR_CODE
    + FLOAT_CODE
    + LIST_CODE
    + DICT_CODE
    + TUPLE_CODE
    + SET_CODE
    + BYTES_CODE
)
