"""WAT helper functions: Generic container/subscript operations."""

from __future__ import annotations

CONTAINERS_CODE = """

;; ============================================================================
;; Sequence Functions (for pattern matching)
;; ============================================================================

;; sequence_length: get length of any sequence (LIST, TUPLE, PAIR chain, null, or EMPTY_LIST)
;; Returns -1 if not a sequence type
(func $sequence_length (param $seq (ref null eq)) (result i32)
  ;; Check null - represents empty list/sequence
  (if (ref.is_null (local.get $seq))
    (then (return (i32.const 0)))
  )
  ;; Check if it's an EMPTY_LIST (empty list marker)
  (if (ref.test (ref $EMPTY_LIST) (local.get $seq))
    (then (return (i32.const 0)))
  )
  ;; Check if it's a LIST
  (if (ref.test (ref $LIST) (local.get $seq))
    (then
      (return (call $list_v2_len (ref.cast (ref $LIST) (local.get $seq))))
    )
  )
  ;; Check if it's a TUPLE
  (if (ref.test (ref $TUPLE) (local.get $seq))
    (then
      (return (struct.get $TUPLE $len (ref.cast (ref $TUPLE) (local.get $seq))))
    )
  )
  ;; Check if it's a PAIR chain (legacy list)
  (if (ref.test (ref $PAIR) (local.get $seq))
    (then
      (return (call $list_len (local.get $seq)))
    )
  )
  ;; Not a sequence
  (i32.const -1)
)


;; sequence_get: get element at index from any sequence (LIST, TUPLE, or PAIR chain)
;; Returns null if not a sequence or index out of bounds
(func $sequence_get (param $seq (ref null eq)) (param $idx i32) (result (ref null eq))
  ;; Check null
  (if (ref.is_null (local.get $seq))
    (then (return (ref.null eq)))
  )
  ;; Check if it's a LIST
  (if (ref.test (ref $LIST) (local.get $seq))
    (then
      (return (call $list_v2_get
        (ref.cast (ref $LIST) (local.get $seq))
        (local.get $idx)))
    )
  )
  ;; Check if it's a TUPLE
  (if (ref.test (ref $TUPLE) (local.get $seq))
    (then
      (return (call $tuple_get
        (ref.cast (ref $TUPLE) (local.get $seq))
        (local.get $idx)))
    )
  )
  ;; Check if it's a PAIR chain (legacy list)
  (if (ref.test (ref $PAIR) (local.get $seq))
    (then
      (return (call $list_get (local.get $seq) (local.get $idx)))
    )
  )
  ;; Not a sequence
  (ref.null eq)
)


;; subscript_get: unified subscript operation for lists, strings, and dicts
;; Dicts are wrapped in $DICT type to distinguish from lists at runtime
(func $subscript_get (param $container (ref null eq)) (param $key (ref null eq)) (result (ref null eq))
  ;; Check if container is a $DICT wrapper - if so, use dict_get
  (if (ref.test (ref $DICT) (local.get $container))
    (then
      (return (call $dict_get
        (local.get $container)
        (local.get $key)))
    )
  )
  ;; Check container type
  ;; If key is an integer and container is a LIST, PAIR, or STRING, use appropriate get
  (if (ref.test (ref i31) (local.get $key))
    (then
      ;; Integer key
      ;; Check for array-backed $LIST first (O(1) access)
      (if (ref.test (ref $LIST) (local.get $container))
        (then
          (return (call $list_v2_get
            (ref.cast (ref $LIST) (local.get $container))
            (i31.get_s (ref.cast (ref i31) (local.get $key)))))
        )
      )
      (if (ref.test (ref $TUPLE) (local.get $container))
        (then
          (return (call $tuple_get
            (ref.cast (ref $TUPLE) (local.get $container))
            (i31.get_s (ref.cast (ref i31) (local.get $key)))))
        )
      )
      (if (ref.test (ref $PAIR) (local.get $container))
        (then
          ;; PAIR chain list/tuple - use list_get
          (return (call $list_get
            (local.get $container)
            (i31.get_s (ref.cast (ref i31) (local.get $key)))))
        )
      )
      (if (ref.test (ref $BYTES) (local.get $container))
        (then
          ;; Bytes - use bytes_get (returns integer)
          (return (call $bytes_get
            (ref.cast (ref $BYTES) (local.get $container))
            (i31.get_s (ref.cast (ref i31) (local.get $key)))))
        )
      )
      (if (ref.test (ref $STRING) (local.get $container))
        (then
          ;; String - use string_get
          (return (call $string_get
            (ref.cast (ref $STRING) (local.get $container))
            (i31.get_s (ref.cast (ref i31) (local.get $key)))))
        )
      )
    )
  )
  ;; Fallback to dict lookup (for string keys on non-wrapped dicts)
  (call $dict_get (local.get $container) (local.get $key))
)


;; subscript_delete: delete item from container by key
;; Returns the modified container (for dict) or original (for others)
(func $subscript_delete (param $container (ref null eq)) (param $key (ref null eq)) (result (ref null eq))
  ;; Check if container is a $DICT (hash table based)
  (if (ref.test (ref $DICT) (local.get $container))
    (then
      (return (call $dict_delete (local.get $container) (local.get $key)))
    )
  )
  ;; Check if it's an OBJECT with __delitem__ method
  (if (ref.test (ref $OBJECT) (local.get $container))
    (then
      (return (call $object_delitem (local.get $container) (local.get $key)))
    )
  )
  ;; Check if key is an integer and container is a list
  (if (ref.test (ref i31) (local.get $key))
    (then
      ;; Check for $LIST (array-backed)
      (if (ref.test (ref $LIST) (local.get $container))
        (then
          (return (call $list_v2_delete_at
            (ref.cast (ref $LIST) (local.get $container))
            (i31.get_s (ref.cast (ref i31) (local.get $key)))))
        )
      )
      ;; Check for PAIR chain
      (if (ref.test (ref $PAIR) (local.get $container))
        (then
          ;; List - delete by index
          (return (call $list_delete_at
            (local.get $container)
            (i31.get_s (ref.cast (ref i31) (local.get $key)))))
        )
      )
    )
  )
  ;; For raw PAIR chains with non-integer keys (dicts without wrapper), delete directly
  (if (ref.test (ref $PAIR) (local.get $container))
    (then
      (return (call $dict_delete (local.get $container) (local.get $key)))
    )
  )
  ;; Unknown container type - return as-is
  (local.get $container)
)


;; container_contains: unified membership check for lists, strings, and dicts
(func $container_contains (param $item (ref null eq)) (param $container (ref null eq)) (result i32)
  ;; Check if container is a string (substring check)
  (if (ref.test (ref $STRING) (local.get $container))
    (then
      ;; For string, check if item is a substring
      (if (ref.test (ref $STRING) (local.get $item))
        (then
          (return (call $string_contains
            (ref.cast (ref $STRING) (local.get $container))
            (ref.cast (ref $STRING) (local.get $item))))
        )
      )
      (return (i32.const 0))
    )
  )
  ;; Check if it's a dict (PAIR of PAIRs)
  (if (call $is_dict (local.get $container))
    (then
      (return (call $dict_contains (local.get $container) (local.get $item)))
    )
  )
  ;; Check if it's a tuple
  (if (ref.test (ref $TUPLE) (local.get $container))
    (then
      (return (call $tuple_contains (local.get $item) (ref.cast (ref $TUPLE) (local.get $container))))
    )
  )
  ;; Otherwise treat as list
  (call $list_contains (local.get $item) (local.get $container))
)


;; container_set: polymorphic set for lists and dicts
;; If container is $DICT wrapper, use dict_set
;; If container is $LIST (array-backed), use list_v2_set
;; If key is STRING (non-$DICT), treat as dict[key] = val
;; If key is i31 (int), treat as list[index] = val
(func $container_set (param $container (ref null eq)) (param $key (ref null eq)) (param $val (ref null eq)) (result (ref null eq))
  (local $unwrapped (ref null eq))
  ;; If container is $DICT (hash table based), use dict_set directly
  (if (ref.test (ref $DICT) (local.get $container))
    (then
      (return (call $dict_set (local.get $container) (local.get $key) (local.get $val)))
    )
  )
  ;; If container is $LIST (array-backed), use list_v2_set
  (if (ref.test (ref $LIST) (local.get $container))
    (then
      (call $list_v2_set
        (ref.cast (ref $LIST) (local.get $container))
        (i31.get_s (ref.cast (ref i31) (local.get $key)))
        (local.get $val))
      (return (local.get $container))
    )
  )
  ;; If key is STRING, this is dict assignment (legacy support for non-wrapped dicts)
  (if (ref.test (ref $STRING) (local.get $key))
    (then
      ;; Use dict_set which returns the updated dict
      (return (call $dict_set (local.get $container) (local.get $key) (local.get $val)))
    )
  )
  ;; Otherwise treat as PAIR-chain list assignment
  (call $list_set (local.get $container) (local.get $key) (local.get $val))
  (local.get $container)
)


;; slice: unified slice for both lists and strings
(func $slice (param $container (ref null eq)) (param $lower i32) (param $upper i32) (param $step i32) (result (ref null eq))
  ;; Check if container is a string
  (if (ref.test (ref $STRING) (local.get $container))
    (then
      (return (call $string_slice
        (ref.cast (ref $STRING) (local.get $container))
        (local.get $lower)
        (local.get $upper)
        (local.get $step)))
    )
  )
  ;; Check if container is a tuple
  (if (ref.test (ref $TUPLE) (local.get $container))
    (then
      (return (call $tuple_slice
        (ref.cast (ref $TUPLE) (local.get $container))
        (local.get $lower)
        (local.get $upper)
        (local.get $step)))
    )
  )
  ;; Check if container is $LIST (array-backed) - convert to PAIR chain first
  (if (ref.test (ref $LIST) (local.get $container))
    (then
      (return (call $list_slice
        (call $list_v2_to_pair (ref.cast (ref $LIST) (local.get $container)))
        (local.get $lower)
        (local.get $upper)
        (local.get $step)))
    )
  )
  ;; Otherwise assume it's a PAIR chain list
  (call $list_slice (local.get $container) (local.get $lower) (local.get $upper) (local.get $step))
)

"""
