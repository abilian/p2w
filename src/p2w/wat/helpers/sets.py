"""WAT helper functions: Set operations."""

from __future__ import annotations

SETS_CODE = """

;; Set method: add(item) - add item if not already present
(func $set_add (param $set (ref null eq)) (param $item (ref null eq)) (result (ref null eq))
  (local $current (ref null eq))
  (local $pair (ref null $PAIR))

  ;; Handle null or $EMPTY_LIST - create single element set
  (if (ref.is_null (local.get $set))
    (then (return (struct.new $PAIR (local.get $item) (ref.null eq))))
  )
  (if (ref.test (ref $EMPTY_LIST) (local.get $set))
    (then (return (struct.new $PAIR (local.get $item) (ref.null eq))))
  )

  ;; Check if item already exists
  (local.set $current (local.get $set))
  (block $not_found
    (block $found
      (loop $loop
        (br_if $not_found (ref.is_null (local.get $current)))
        ;; Check if it's a PAIR before casting
        (if (i32.eqz (ref.test (ref $PAIR) (local.get $current)))
          (then (br $not_found))
        )
        (local.set $pair (ref.cast (ref $PAIR) (local.get $current)))
        (if (call $value_equals (struct.get $PAIR 0 (local.get $pair)) (local.get $item))
          (then (br $found))
        )
        (local.set $current (struct.get $PAIR 1 (local.get $pair)))
        (br $loop)
      )
    )
    ;; Found - return set unchanged
    (return (local.get $set))
  )

  ;; Not found - prepend item to set
  (struct.new $PAIR (local.get $item) (local.get $set))
)


;; Set method: remove(item) - remove item, error if not present
(func $set_remove (param $set (ref null eq)) (param $item (ref null eq)) (result (ref null eq))
  ;; For simplicity, same as discard (no error on missing)
  (call $set_discard (local.get $set) (local.get $item))
)


;; Set method: discard(item) - remove item if present
(func $set_discard (param $set (ref null eq)) (param $item (ref null eq)) (result (ref null eq))
  (local $current (ref null eq))
  (local $prev (ref null eq))
  (local $pair (ref null $PAIR))

  (if (ref.is_null (local.get $set))
    (then (return (ref.null eq)))
  )

  ;; Check first element
  (local.set $pair (ref.cast (ref $PAIR) (local.get $set)))
  (if (call $value_equals (struct.get $PAIR 0 (local.get $pair)) (local.get $item))
    (then
      ;; Remove first element - return rest
      (return (struct.get $PAIR 1 (local.get $pair)))
    )
  )

  ;; Search rest of set
  (local.set $prev (local.get $set))
  (local.set $current (struct.get $PAIR 1 (local.get $pair)))
  (block $done
    (loop $loop
      (br_if $done (ref.is_null (local.get $current)))
      (local.set $pair (ref.cast (ref $PAIR) (local.get $current)))
      (if (call $value_equals (struct.get $PAIR 0 (local.get $pair)) (local.get $item))
        (then
          ;; Remove by unlinking
          (struct.set $PAIR 1 (ref.cast (ref $PAIR) (local.get $prev))
            (struct.get $PAIR 1 (local.get $pair)))
          (return (local.get $set))
        )
      )
      (local.set $prev (local.get $current))
      (local.set $current (struct.get $PAIR 1 (local.get $pair)))
      (br $loop)
    )
  )
  (local.get $set)
)


;; =============================================================================
;; Set V2 Operations (using hash table)
;; =============================================================================

;; Create empty set with default capacity
(func $set_v2_new (result (ref $SET))
  (struct.new $SET (call $hashtable_new (i32.const 16)))
)


;; Add value to set
(func $set_v2_add (param $set (ref $SET)) (param $value (ref null eq))
  ;; For sets, we store value as both key and value (or just use null for value)
  (call $hashtable_set (struct.get $SET $table (local.get $set)) (local.get $value) (local.get $value))
)


;; Check if value exists in set
(func $set_v2_contains (param $set (ref $SET)) (param $value (ref null eq)) (result i32)
  (call $hashtable_contains (struct.get $SET $table (local.get $set)) (local.get $value))
)


;; Remove value from set
(func $set_v2_remove (param $set (ref $SET)) (param $value (ref null eq)) (result i32)
  (call $hashtable_delete (struct.get $SET $table (local.get $set)) (local.get $value))
)


;; Get set length
(func $set_v2_len (param $set (ref $SET)) (result i32)
  (call $hashtable_len (struct.get $SET $table (local.get $set)))
)

"""
