"""WAT builtin functions: I/O functions (print)."""

from __future__ import annotations

PRINT_CODE = """
(func $print (param $args (ref null eq)) (param $env (ref null $ENV)) (result (ref null eq))
  (local $current (ref null eq))
  (local $val (ref null eq))
  (local $first i32)
  ;; Handle no arguments - just print newline
  (if (ref.is_null (local.get $args))
    (then
      (call $write_char (i32.const 10))  ;; just newline
      (return (ref.null eq))
    )
  )
  ;; Iterate through all arguments, separated by spaces
  (local.set $current (local.get $args))
  (local.set $first (i32.const 1))
  (block $done
    (loop $loop
      (br_if $done (ref.is_null (local.get $current)))
      ;; Check if current is a PAIR
      (if (i32.eqz (ref.test (ref $PAIR) (local.get $current)))
        (then (br $done))
      )
      ;; Print space before non-first arguments
      (if (i32.eqz (local.get $first))
        (then (call $write_char (i32.const 32)))  ;; space
      )
      (local.set $first (i32.const 0))
      ;; Get and print the value
      (local.set $val (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $current))))
      (call $emit_value (local.get $val))
      ;; Move to next argument
      (local.set $current (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current))))
      (br $loop)
    )
  )
  (call $write_char (i32.const 10))  ;; newline
  (ref.null eq)
)

;; print_with_sep_end: print with custom separator and end
(func $print_with_sep_end (param $args (ref null eq)) (param $sep (ref null eq)) (param $end (ref null eq)) (result (ref null eq))
  (local $current (ref null eq))
  (local $val (ref null eq))
  (local $first i32)
  ;; Handle no arguments - just print end
  (if (ref.is_null (local.get $args))
    (then
      (if (ref.test (ref $STRING) (local.get $end))
        (then (call $emit_string (ref.cast (ref $STRING) (local.get $end))))
      )
      (return (ref.null eq))
    )
  )
  ;; Iterate through all arguments, separated by sep
  (local.set $current (local.get $args))
  (local.set $first (i32.const 1))
  (block $done
    (loop $loop
      (br_if $done (ref.is_null (local.get $current)))
      (if (i32.eqz (ref.test (ref $PAIR) (local.get $current)))
        (then (br $done))
      )
      ;; Print sep before non-first arguments
      (if (i32.eqz (local.get $first))
        (then
          (if (ref.test (ref $STRING) (local.get $sep))
            (then (call $emit_string (ref.cast (ref $STRING) (local.get $sep))))
          )
        )
      )
      (local.set $first (i32.const 0))
      ;; Get and print the value
      (local.set $val (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $current))))
      (call $emit_value (local.get $val))
      ;; Move to next argument
      (local.set $current (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current))))
      (br $loop)
    )
  )
  ;; Print end
  (if (ref.test (ref $STRING) (local.get $end))
    (then (call $emit_string (ref.cast (ref $STRING) (local.get $end))))
  )
  (ref.null eq)
)

;; emit_value: print a value
(func $emit_value (param $v (ref null eq))
  ;; null (None)
  (if (ref.is_null (local.get $v))
    (then
      ;; print "None"
      (call $write_char (i32.const 78))   ;; N
      (call $write_char (i32.const 111))  ;; o
      (call $write_char (i32.const 110))  ;; n
      (call $write_char (i32.const 101))  ;; e
      (return)
    )
  )
  ;; $EMPTY_LIST - print "[]"
  (if (ref.test (ref $EMPTY_LIST) (local.get $v))
    (then
      (call $write_char (i32.const 91))   ;; [
      (call $write_char (i32.const 93))   ;; ]
      (return)
    )
  )
  ;; $ELLIPSIS - print "Ellipsis"
  (if (ref.test (ref $ELLIPSIS) (local.get $v))
    (then
      (call $write_char (i32.const 69))   ;; E
      (call $write_char (i32.const 108))  ;; l
      (call $write_char (i32.const 108))  ;; l
      (call $write_char (i32.const 105))  ;; i
      (call $write_char (i32.const 112))  ;; p
      (call $write_char (i32.const 115))  ;; s
      (call $write_char (i32.const 105))  ;; i
      (call $write_char (i32.const 115))  ;; s
      (return)
    )
  )
  ;; integer (i31)
  (if (ref.test (ref i31) (local.get $v))
    (then
      (call $write_i32 (i31.get_s (ref.cast (ref i31) (local.get $v))))
      (return)
    )
  )
  ;; large integer (INT64)
  (if (ref.test (ref $INT64) (local.get $v))
    (then
      (call $emit_i64 (struct.get $INT64 0 (ref.cast (ref $INT64) (local.get $v))))
      (return)
    )
  )
  ;; bool
  (if (ref.test (ref $BOOL) (local.get $v))
    (then
      (if (struct.get $BOOL 0 (ref.cast (ref $BOOL) (local.get $v)))
        (then
          ;; True
          (call $write_char (i32.const 84))   ;; T
          (call $write_char (i32.const 114))  ;; r
          (call $write_char (i32.const 117))  ;; u
          (call $write_char (i32.const 101))  ;; e
        )
        (else
          ;; False
          (call $write_char (i32.const 70))   ;; F
          (call $write_char (i32.const 97))   ;; a
          (call $write_char (i32.const 108))  ;; l
          (call $write_char (i32.const 115))  ;; s
          (call $write_char (i32.const 101))  ;; e
        )
      )
      (return)
    )
  )
  ;; float
  (if (ref.test (ref $FLOAT) (local.get $v))
    (then
      (call $write_f64 (struct.get $FLOAT 0 (ref.cast (ref $FLOAT) (local.get $v))))
      (return)
    )
  )
  ;; string
  (if (ref.test (ref $STRING) (local.get $v))
    (then
      (call $emit_string (ref.cast (ref $STRING) (local.get $v)))
      (return)
    )
  )
  ;; $LIST (array-backed) - print as list
  (if (ref.test (ref $LIST) (local.get $v))
    (then
      (call $emit_list_v2 (ref.cast (ref $LIST) (local.get $v)))
      (return)
    )
  )
  ;; $TUPLE (array-backed) - print as tuple
  (if (ref.test (ref $TUPLE) (local.get $v))
    (then
      (call $emit_tuple_v2 (ref.cast (ref $TUPLE) (local.get $v)))
      (return)
    )
  )
  ;; PAIR - could be list or tuple
  (if (ref.test (ref $PAIR) (local.get $v))
    (then
      ;; Check if it's a tuple (cdr is not PAIR and not null)
      (if (call $is_list_pair (local.get $v))
        (then
          ;; It's a list
          (call $emit_list (local.get $v))
        )
        (else
          ;; It's a 2-element tuple
          (call $emit_tuple (ref.cast (ref $PAIR) (local.get $v)))
        )
      )
      (return)
    )
  )
  ;; $DICT - print {key: value, ...}
  (if (ref.test (ref $DICT) (local.get $v))
    (then
      (call $emit_dict (struct.get $DICT 0 (ref.cast (ref $DICT) (local.get $v))))
      (return)
    )
  )
  ;; $CLOSURE - print as type (for type() builtin)
  (if (ref.test (ref $CLOSURE) (local.get $v))
    (then
      (call $emit_type_name (struct.get $CLOSURE 1 (ref.cast (ref $CLOSURE) (local.get $v))))
      (return)
    )
  )
  ;; $CLASS - print <class 'ClassName'>
  (if (ref.test (ref $CLASS) (local.get $v))
    (then
      (call $emit_class_type (ref.cast (ref $CLASS) (local.get $v)))
      (return)
    )
  )
  ;; unknown - print ?
  (call $write_char (i32.const 63))
)

;; emit_type_name: print type name based on builtin function index
;; Indices: 6=int, 7=bool, 8=str, 11=float, 13=list, 18=dict, 19=tuple, 30=bytes
(func $emit_type_name (param $idx i32)
  ;; Print "<class '"
  (call $write_char (i32.const 60))   ;; <
  (call $write_char (i32.const 99))   ;; c
  (call $write_char (i32.const 108))  ;; l
  (call $write_char (i32.const 97))   ;; a
  (call $write_char (i32.const 115))  ;; s
  (call $write_char (i32.const 115))  ;; s
  (call $write_char (i32.const 32))   ;; space
  (call $write_char (i32.const 39))   ;; '
  ;; Print type name based on index
  (if (i32.eq (local.get $idx) (i32.const 6))
    (then
      (call $write_char (i32.const 105))  ;; i
      (call $write_char (i32.const 110))  ;; n
      (call $write_char (i32.const 116))  ;; t
    )
  )
  (if (i32.eq (local.get $idx) (i32.const 7))
    (then
      (call $write_char (i32.const 98))   ;; b
      (call $write_char (i32.const 111))  ;; o
      (call $write_char (i32.const 111))  ;; o
      (call $write_char (i32.const 108))  ;; l
    )
  )
  (if (i32.eq (local.get $idx) (i32.const 8))
    (then
      (call $write_char (i32.const 115))  ;; s
      (call $write_char (i32.const 116))  ;; t
      (call $write_char (i32.const 114))  ;; r
    )
  )
  (if (i32.eq (local.get $idx) (i32.const 11))
    (then
      (call $write_char (i32.const 102))  ;; f
      (call $write_char (i32.const 108))  ;; l
      (call $write_char (i32.const 111))  ;; o
      (call $write_char (i32.const 97))   ;; a
      (call $write_char (i32.const 116))  ;; t
    )
  )
  (if (i32.eq (local.get $idx) (i32.const 13))
    (then
      (call $write_char (i32.const 108))  ;; l
      (call $write_char (i32.const 105))  ;; i
      (call $write_char (i32.const 115))  ;; s
      (call $write_char (i32.const 116))  ;; t
    )
  )
  (if (i32.eq (local.get $idx) (i32.const 18))
    (then
      (call $write_char (i32.const 100))  ;; d
      (call $write_char (i32.const 105))  ;; i
      (call $write_char (i32.const 99))   ;; c
      (call $write_char (i32.const 116))  ;; t
    )
  )
  (if (i32.eq (local.get $idx) (i32.const 19))
    (then
      (call $write_char (i32.const 116))  ;; t
      (call $write_char (i32.const 117))  ;; u
      (call $write_char (i32.const 112))  ;; p
      (call $write_char (i32.const 108))  ;; l
      (call $write_char (i32.const 101))  ;; e
    )
  )
  (if (i32.eq (local.get $idx) (i32.const 30))
    (then
      (call $write_char (i32.const 98))   ;; b
      (call $write_char (i32.const 121))  ;; y
      (call $write_char (i32.const 116))  ;; t
      (call $write_char (i32.const 101))  ;; e
      (call $write_char (i32.const 115))  ;; s
    )
  )
  ;; Print "'>"
  (call $write_char (i32.const 39))   ;; '
  (call $write_char (i32.const 62))   ;; >
)

;; emit_class_type: print <class 'ClassName'> for user-defined classes
(func $emit_class_type (param $cls (ref $CLASS))
  (local $name (ref $STRING))
  ;; Print "<class '"
  (call $write_char (i32.const 60))   ;; <
  (call $write_char (i32.const 99))   ;; c
  (call $write_char (i32.const 108))  ;; l
  (call $write_char (i32.const 97))   ;; a
  (call $write_char (i32.const 115))  ;; s
  (call $write_char (i32.const 115))  ;; s
  (call $write_char (i32.const 32))   ;; space
  (call $write_char (i32.const 39))   ;; '
  ;; Print class name
  (local.set $name (struct.get $CLASS 0 (local.get $cls)))
  (call $emit_string (local.get $name))
  ;; Print "'>"
  (call $write_char (i32.const 39))   ;; '
  (call $write_char (i32.const 62))   ;; >
)

;; is_list_pair: check if PAIR is a list element (cdr is PAIR or null)
(func $is_list_pair (param $p (ref null eq)) (result i32)
  (local $cdr (ref null eq))
  (if (ref.is_null (local.get $p))
    (then (return (i32.const 0)))
  )
  (if (i32.eqz (ref.test (ref $PAIR) (local.get $p)))
    (then (return (i32.const 0)))
  )
  (local.set $cdr (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $p))))
  ;; List if cdr is null or PAIR
  (i32.or
    (ref.is_null (local.get $cdr))
    (ref.test (ref $PAIR) (local.get $cdr))
  )
)

;; emit_tuple: print a 2-element tuple (a, b)
(func $emit_tuple (param $pair (ref $PAIR))
  (call $write_char (i32.const 40))  ;; (
  (call $emit_value_repr (struct.get $PAIR 0 (local.get $pair)))
  (call $write_char (i32.const 44))  ;; ,
  (call $write_char (i32.const 32))  ;; space
  (call $emit_value_repr (struct.get $PAIR 1 (local.get $pair)))
  (call $write_char (i32.const 41))  ;; )
)

;; emit_list: print a list [a, b, c]
(func $emit_list (param $list (ref null eq))
  (local $current (ref null eq))
  (local $first i32)
  (local $elem (ref null eq))
  (local $cdr (ref null eq))
  (call $write_char (i32.const 91))  ;; [
  (local.set $current (local.get $list))
  (local.set $first (i32.const 1))
  (block $done
    (loop $loop
      (br_if $done (ref.is_null (local.get $current)))
      ;; Check if current is a PAIR (could be EMPTY_LIST at end)
      (if (i32.eqz (ref.test (ref $PAIR) (local.get $current)))
        (then (br $done))
      )
      (if (i32.eqz (local.get $first))
        (then
          (call $write_char (i32.const 44))  ;; ,
          (call $write_char (i32.const 32))  ;; space
        )
      )
      (local.set $first (i32.const 0))
      ;; Get the element
      (local.set $elem (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $current))))
      ;; Check if element is a tuple-like PAIR (cdr is not PAIR and not null)
      (if (i32.and
            (ref.test (ref $PAIR) (local.get $elem))
            (i32.eqz (call $is_list_pair (local.get $elem))))
        (then
          ;; It's a tuple - print as (a, b)
          (call $emit_tuple (ref.cast (ref $PAIR) (local.get $elem)))
        )
        (else
          ;; Regular element - use repr style (strings with quotes)
          (call $emit_value_repr (local.get $elem))
        )
      )
      (local.set $current (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current))))
      (br $loop)
    )
  )
  (call $write_char (i32.const 93))  ;; ]
)

;; emit_list_v2: print array-backed list [a, b, c]
(func $emit_list_v2 (param $list (ref $LIST))
  (local $data (ref $ARRAY_ANY))
  (local $len i32)
  (local $i i32)
  (local $first i32)
  (local $elem (ref null eq))

  (call $write_char (i32.const 91))  ;; [
  (local.set $data (struct.get $LIST $data (local.get $list)))
  (local.set $len (struct.get $LIST $len (local.get $list)))
  (local.set $i (i32.const 0))
  (local.set $first (i32.const 1))

  (block $done
    (loop $loop
      (br_if $done (i32.ge_s (local.get $i) (local.get $len)))
      (if (i32.eqz (local.get $first))
        (then
          (call $write_char (i32.const 44))  ;; ,
          (call $write_char (i32.const 32))  ;; space
        )
      )
      (local.set $first (i32.const 0))
      (local.set $elem (array.get $ARRAY_ANY (local.get $data) (local.get $i)))
      ;; Print element in repr style (strings with quotes)
      (call $emit_value_repr (local.get $elem))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $loop)
    )
  )
  (call $write_char (i32.const 93))  ;; ]
)

;; emit_tuple_v2: print array-backed tuple (a, b, c) with trailing comma for single
(func $emit_tuple_v2 (param $tup (ref $TUPLE))
  (local $data (ref $ARRAY_ANY))
  (local $len i32)
  (local $i i32)
  (local $first i32)
  (local $elem (ref null eq))

  (call $write_char (i32.const 40))  ;; (
  (local.set $data (struct.get $TUPLE $data (local.get $tup)))
  (local.set $len (struct.get $TUPLE $len (local.get $tup)))
  (local.set $i (i32.const 0))
  (local.set $first (i32.const 1))

  (block $done
    (loop $loop
      (br_if $done (i32.ge_s (local.get $i) (local.get $len)))
      (if (i32.eqz (local.get $first))
        (then
          (call $write_char (i32.const 44))  ;; ,
          (call $write_char (i32.const 32))  ;; space
        )
      )
      (local.set $first (i32.const 0))
      (local.set $elem (array.get $ARRAY_ANY (local.get $data) (local.get $i)))
      (call $emit_value_repr (local.get $elem))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $loop)
    )
  )
  ;; For single-element tuple, add trailing comma
  (if (i32.eq (local.get $len) (i32.const 1))
    (then (call $write_char (i32.const 44)))  ;; ,
  )
  (call $write_char (i32.const 41))  ;; )
)

;; emit_dict: print a dict {key: value, ...}
(func $emit_dict (param $dict (ref null eq))
  (local $current (ref null eq))
  (local $first i32)
  (local $entry_raw (ref null eq))
  (local $entry_arr (ref $ARRAY_ANY))
  (call $write_char (i32.const 123))  ;; {
  (local.set $current (local.get $dict))
  (local.set $first (i32.const 1))
  (block $done
    (loop $loop
      (br_if $done (ref.is_null (local.get $current)))
      (if (i32.eqz (ref.test (ref $PAIR) (local.get $current)))
        (then (br $done))
      )
      (if (i32.eqz (local.get $first))
        (then
          (call $write_char (i32.const 44))  ;; ,
          (call $write_char (i32.const 32))  ;; space
        )
      )
      (local.set $first (i32.const 0))
      ;; Get the key-value entry
      (local.set $entry_raw (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $current))))
      ;; Handle $TUPLE entries (from zip with array-backed tuples)
      (if (ref.test (ref $TUPLE) (local.get $entry_raw))
        (then
          (local.set $entry_arr (struct.get $TUPLE 0 (ref.cast (ref $TUPLE) (local.get $entry_raw))))
          ;; Print key in repr style
          (call $emit_value_repr (array.get $ARRAY_ANY (local.get $entry_arr) (i32.const 0)))
          (call $write_char (i32.const 58))  ;; :
          (call $write_char (i32.const 32))  ;; space
          ;; Print value in repr style
          (call $emit_value_repr (array.get $ARRAY_ANY (local.get $entry_arr) (i32.const 1)))
        )
        (else
          ;; Handle PAIR entries (classic format)
          ;; Print key in repr style
          (call $emit_value_repr (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $entry_raw))))
          (call $write_char (i32.const 58))  ;; :
          (call $write_char (i32.const 32))  ;; space
          ;; Print value in repr style
          (call $emit_value_repr (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $entry_raw))))
        )
      )
      (local.set $current (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current))))
      (br $loop)
    )
  )
  (call $write_char (i32.const 125))  ;; }
)

;; emit_i64: print a 64-bit integer
(func $emit_i64 (param $val i64)
  (call $write_i64 (local.get $val))
)

;; emit_string: print string bytes
(func $emit_string (param $s (ref $STRING))
  (local $offset i32)
  (local $len i32)
  (local $i i32)
  (local.set $offset (struct.get $STRING 0 (local.get $s)))
  (local.set $len (struct.get $STRING 1 (local.get $s)))
  (local.set $i (i32.const 0))
  (block $break
    (loop $loop
      (br_if $break (i32.ge_u (local.get $i) (local.get $len)))
      (call $write_char (i32.load8_u (i32.add (local.get $offset) (local.get $i))))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $loop)
    )
  )
)

;; emit_string_repr: print string with quotes (for repr in lists)
(func $emit_string_repr (param $s (ref $STRING))
  (call $write_char (i32.const 39))  ;; '
  (call $emit_string (local.get $s))
  (call $write_char (i32.const 39))  ;; '
)

;; emit_value_repr: print a value in repr style (strings with quotes)
(func $emit_value_repr (param $v (ref null eq))
  ;; null (None)
  (if (ref.is_null (local.get $v))
    (then
      (call $write_char (i32.const 78))   ;; N
      (call $write_char (i32.const 111))  ;; o
      (call $write_char (i32.const 110))  ;; n
      (call $write_char (i32.const 101))  ;; e
      (return)
    )
  )
  ;; $EMPTY_LIST - print "[]"
  (if (ref.test (ref $EMPTY_LIST) (local.get $v))
    (then
      (call $write_char (i32.const 91))   ;; [
      (call $write_char (i32.const 93))   ;; ]
      (return)
    )
  )
  ;; string - print with quotes
  (if (ref.test (ref $STRING) (local.get $v))
    (then
      (call $emit_string_repr (ref.cast (ref $STRING) (local.get $v)))
      (return)
    )
  )
  ;; For all other types, use regular emit_value
  (call $emit_value (local.get $v))
)
"""

# Combined code for this module
IO_CODE = PRINT_CODE
