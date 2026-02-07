"""WAT helper functions: Value comparison and equality."""

from __future__ import annotations

COMPARISONS_CODE = """

;; ============================================================================
;; End of Array-Based List Functions
;; ============================================================================

;; compare_values: return 1 if a > b (for sorting)
(func $compare_values (param $a (ref null eq)) (param $b (ref null eq)) (result i32)
  (local $fa f64)
  (local $fb f64)
  ;; Handle null
  (if (ref.is_null (local.get $a))
    (then (return (i32.const 0)))  ;; null <= anything
  )
  (if (ref.is_null (local.get $b))
    (then (return (i32.const 1)))  ;; anything > null
  )
  ;; Both i31 (integers)
  (if (i32.and (ref.test (ref i31) (local.get $a)) (ref.test (ref i31) (local.get $b)))
    (then
      (return (i32.gt_s
        (i31.get_s (ref.cast (ref i31) (local.get $a)))
        (i31.get_s (ref.cast (ref i31) (local.get $b)))))
    )
  )
  ;; Both floats
  (if (i32.and (ref.test (ref $FLOAT) (local.get $a)) (ref.test (ref $FLOAT) (local.get $b)))
    (then
      (return (f64.gt
        (struct.get $FLOAT 0 (ref.cast (ref $FLOAT) (local.get $a)))
        (struct.get $FLOAT 0 (ref.cast (ref $FLOAT) (local.get $b)))))
    )
  )
  ;; Both strings - use lexicographic comparison
  (if (i32.and (ref.test (ref $STRING) (local.get $a)) (ref.test (ref $STRING) (local.get $b)))
    (then
      ;; $strings_compare returns -1/0/1; we want 1 if a > b
      (return (i32.gt_s
        (call $strings_compare
          (ref.cast (ref $STRING) (local.get $a))
          (ref.cast (ref $STRING) (local.get $b)))
        (i32.const 0)))
    )
  )
  ;; Mixed int/float
  (if (ref.test (ref i31) (local.get $a))
    (then (local.set $fa (f64.convert_i32_s (i31.get_s (ref.cast (ref i31) (local.get $a))))))
    (else
      (if (ref.test (ref $FLOAT) (local.get $a))
        (then (local.set $fa (struct.get $FLOAT 0 (ref.cast (ref $FLOAT) (local.get $a)))))
        (else (return (i32.const 0)))
      )
    )
  )
  (if (ref.test (ref i31) (local.get $b))
    (then (local.set $fb (f64.convert_i32_s (i31.get_s (ref.cast (ref i31) (local.get $b))))))
    (else
      (if (ref.test (ref $FLOAT) (local.get $b))
        (then (local.set $fb (struct.get $FLOAT 0 (ref.cast (ref $FLOAT) (local.get $b)))))
        (else (return (i32.const 1)))
      )
    )
  )
  (f64.gt (local.get $fa) (local.get $fb))
)


;; values_equal: compare two values for equality
(func $values_equal (param $a (ref null eq)) (param $b (ref null eq)) (result i32)
  (local $cdr_a (ref null eq))
  (local $cdr_b (ref null eq))
  (local $a_is_list i32)
  (local $b_is_list i32)
  (local $eq_result (ref null eq))
  (local $method_name (ref $STRING))
  (local $offset i32)
  ;; Both null
  (if (i32.and (ref.is_null (local.get $a)) (ref.is_null (local.get $b)))
    (then (return (i32.const 1)))
  )
  ;; One null, one not
  (if (i32.or (ref.is_null (local.get $a)) (ref.is_null (local.get $b)))
    (then (return (i32.const 0)))
  )
  ;; Both i31 (integers)
  (if (i32.and (ref.test (ref i31) (local.get $a)) (ref.test (ref i31) (local.get $b)))
    (then
      (return (i32.eq
        (i31.get_s (ref.cast (ref i31) (local.get $a)))
        (i31.get_s (ref.cast (ref i31) (local.get $b)))
      ))
    )
  )
  ;; Both INT64 (large integers)
  (if (i32.and (ref.test (ref $INT64) (local.get $a)) (ref.test (ref $INT64) (local.get $b)))
    (then
      (return (i64.eq
        (struct.get $INT64 0 (ref.cast (ref $INT64) (local.get $a)))
        (struct.get $INT64 0 (ref.cast (ref $INT64) (local.get $b)))
      ))
    )
  )
  ;; i31 compared with INT64 (use $int_eq helper)
  (if (i32.and (ref.test (ref i31) (local.get $a)) (ref.test (ref $INT64) (local.get $b)))
    (then
      (return (call $int_eq (local.get $a) (local.get $b)))
    )
  )
  ;; INT64 compared with i31 (use $int_eq helper)
  (if (i32.and (ref.test (ref $INT64) (local.get $a)) (ref.test (ref i31) (local.get $b)))
    (then
      (return (call $int_eq (local.get $a) (local.get $b)))
    )
  )
  ;; Both BOOL
  (if (i32.and (ref.test (ref $BOOL) (local.get $a)) (ref.test (ref $BOOL) (local.get $b)))
    (then
      (return (i32.eq
        (struct.get $BOOL 0 (ref.cast (ref $BOOL) (local.get $a)))
        (struct.get $BOOL 0 (ref.cast (ref $BOOL) (local.get $b)))
      ))
    )
  )
  ;; i31 (int) compared with BOOL - Python: 0 == False, 1 == True
  (if (i32.and (ref.test (ref i31) (local.get $a)) (ref.test (ref $BOOL) (local.get $b)))
    (then
      (return (i32.eq
        (i31.get_s (ref.cast (ref i31) (local.get $a)))
        (struct.get $BOOL 0 (ref.cast (ref $BOOL) (local.get $b)))
      ))
    )
  )
  ;; BOOL compared with i31 (int) - same as above, reversed
  (if (i32.and (ref.test (ref $BOOL) (local.get $a)) (ref.test (ref i31) (local.get $b)))
    (then
      (return (i32.eq
        (struct.get $BOOL 0 (ref.cast (ref $BOOL) (local.get $a)))
        (i31.get_s (ref.cast (ref i31) (local.get $b)))
      ))
    )
  )
  ;; INT64 compared with BOOL - Python: 0 == False, 1 == True
  (if (i32.and (ref.test (ref $INT64) (local.get $a)) (ref.test (ref $BOOL) (local.get $b)))
    (then
      (return (i64.eq
        (struct.get $INT64 0 (ref.cast (ref $INT64) (local.get $a)))
        (i64.extend_i32_s (struct.get $BOOL 0 (ref.cast (ref $BOOL) (local.get $b))))
      ))
    )
  )
  ;; BOOL compared with INT64 - same as above, reversed
  (if (i32.and (ref.test (ref $BOOL) (local.get $a)) (ref.test (ref $INT64) (local.get $b)))
    (then
      (return (i64.eq
        (i64.extend_i32_s (struct.get $BOOL 0 (ref.cast (ref $BOOL) (local.get $a))))
        (struct.get $INT64 0 (ref.cast (ref $INT64) (local.get $b)))
      ))
    )
  )
  ;; Both FLOAT
  (if (i32.and (ref.test (ref $FLOAT) (local.get $a)) (ref.test (ref $FLOAT) (local.get $b)))
    (then
      (return (f64.eq
        (struct.get $FLOAT 0 (ref.cast (ref $FLOAT) (local.get $a)))
        (struct.get $FLOAT 0 (ref.cast (ref $FLOAT) (local.get $b)))
      ))
    )
  )
  ;; FLOAT compared with i31 (int) - Python: 1.0 == 1
  (if (i32.and (ref.test (ref $FLOAT) (local.get $a)) (ref.test (ref i31) (local.get $b)))
    (then
      (return (f64.eq
        (struct.get $FLOAT 0 (ref.cast (ref $FLOAT) (local.get $a)))
        (f64.convert_i32_s (i31.get_s (ref.cast (ref i31) (local.get $b))))
      ))
    )
  )
  ;; i31 (int) compared with FLOAT - same as above, reversed
  (if (i32.and (ref.test (ref i31) (local.get $a)) (ref.test (ref $FLOAT) (local.get $b)))
    (then
      (return (f64.eq
        (f64.convert_i32_s (i31.get_s (ref.cast (ref i31) (local.get $a))))
        (struct.get $FLOAT 0 (ref.cast (ref $FLOAT) (local.get $b)))
      ))
    )
  )
  ;; INT64 compared with FLOAT - Python: 2000000000 == 2000000000.0
  (if (i32.and (ref.test (ref $INT64) (local.get $a)) (ref.test (ref $FLOAT) (local.get $b)))
    (then
      (return (f64.eq
        (f64.convert_i64_s (struct.get $INT64 0 (ref.cast (ref $INT64) (local.get $a))))
        (struct.get $FLOAT 0 (ref.cast (ref $FLOAT) (local.get $b)))
      ))
    )
  )
  ;; FLOAT compared with INT64 - same as above, reversed
  (if (i32.and (ref.test (ref $FLOAT) (local.get $a)) (ref.test (ref $INT64) (local.get $b)))
    (then
      (return (f64.eq
        (struct.get $FLOAT 0 (ref.cast (ref $FLOAT) (local.get $a)))
        (f64.convert_i64_s (struct.get $INT64 0 (ref.cast (ref $INT64) (local.get $b))))
      ))
    )
  )
  ;; Both strings
  (if (i32.and (ref.test (ref $STRING) (local.get $a)) (ref.test (ref $STRING) (local.get $b)))
    (then
      (return (call $strings_equal
        (ref.cast (ref $STRING) (local.get $a))
        (ref.cast (ref $STRING) (local.get $b))))
    )
  )
  ;; Both $EMPTY_LIST
  (if (i32.and (ref.test (ref $EMPTY_LIST) (local.get $a)) (ref.test (ref $EMPTY_LIST) (local.get $b)))
    (then (return (i32.const 1)))
  )
  ;; Both $DICT wrappers - compare contents using dicts_equal
  (if (i32.and (ref.test (ref $DICT) (local.get $a)) (ref.test (ref $DICT) (local.get $b)))
    (then
      (return (call $dicts_equal
        (local.get $a)
        (local.get $b)))
    )
  )
  ;; Both $LIST (array-backed lists) - compare element by element
  (if (i32.and (ref.test (ref $LIST) (local.get $a)) (ref.test (ref $LIST) (local.get $b)))
    (then
      (return (call $list_v2_equal
        (ref.cast (ref $LIST) (local.get $a))
        (ref.cast (ref $LIST) (local.get $b))))
    )
  )
  ;; $LIST compared with $EMPTY_LIST - only equal if $LIST is empty
  (if (i32.and (ref.test (ref $LIST) (local.get $a)) (ref.test (ref $EMPTY_LIST) (local.get $b)))
    (then
      (return (i32.eqz (struct.get $LIST 1 (ref.cast (ref $LIST) (local.get $a)))))
    )
  )
  (if (i32.and (ref.test (ref $EMPTY_LIST) (local.get $a)) (ref.test (ref $LIST) (local.get $b)))
    (then
      (return (i32.eqz (struct.get $LIST 1 (ref.cast (ref $LIST) (local.get $b)))))
    )
  )
  ;; $LIST compared with PAIR chain - convert and compare
  (if (i32.and (ref.test (ref $LIST) (local.get $a)) (ref.test (ref $PAIR) (local.get $b)))
    (then
      ;; Convert $LIST to PAIR chain and compare
      (return (call $lists_equal
        (call $list_v2_to_pair (ref.cast (ref $LIST) (local.get $a)))
        (local.get $b)))
    )
  )
  (if (i32.and (ref.test (ref $PAIR) (local.get $a)) (ref.test (ref $LIST) (local.get $b)))
    (then
      ;; Convert $LIST to PAIR chain and compare
      (return (call $lists_equal
        (local.get $a)
        (call $list_v2_to_pair (ref.cast (ref $LIST) (local.get $b)))))
    )
  )
  ;; Both PAIR - need to distinguish list vs 2-element tuple
  ;; List: cdr is PAIR, null, or $EMPTY_LIST
  ;; Tuple: cdr is a value (not PAIR/null/$EMPTY_LIST)
  (if (i32.and (ref.test (ref $PAIR) (local.get $a)) (ref.test (ref $PAIR) (local.get $b)))
    (then
      (local.set $cdr_a (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $a))))
      (local.set $cdr_b (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $b))))
      ;; Check if a is list (cdr is PAIR, null, or EMPTY_LIST)
      (local.set $a_is_list
        (i32.or
          (i32.or (ref.is_null (local.get $cdr_a)) (ref.test (ref $PAIR) (local.get $cdr_a)))
          (ref.test (ref $EMPTY_LIST) (local.get $cdr_a))
        )
      )
      ;; Check if b is list
      (local.set $b_is_list
        (i32.or
          (i32.or (ref.is_null (local.get $cdr_b)) (ref.test (ref $PAIR) (local.get $cdr_b)))
          (ref.test (ref $EMPTY_LIST) (local.get $cdr_b))
        )
      )
      ;; Both lists - deep comparison
      (if (i32.and (local.get $a_is_list) (local.get $b_is_list))
        (then (return (call $lists_equal (local.get $a) (local.get $b))))
      )
      ;; Both tuples - compare car and cdr with values_equal
      (if (i32.and (i32.eqz (local.get $a_is_list)) (i32.eqz (local.get $b_is_list)))
        (then
          (return (i32.and
            (call $values_equal
              (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $a)))
              (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $b)))
            )
            (call $values_equal (local.get $cdr_a) (local.get $cdr_b))
          ))
        )
      )
      ;; One is list, one is tuple - not equal
      (return (i32.const 0))
    )
  )
  ;; One is $EMPTY_LIST, other is PAIR - not equal
  (if (i32.or
        (i32.and (ref.test (ref $EMPTY_LIST) (local.get $a)) (ref.test (ref $PAIR) (local.get $b)))
        (i32.and (ref.test (ref $PAIR) (local.get $a)) (ref.test (ref $EMPTY_LIST) (local.get $b)))
      )
    (then (return (i32.const 0)))
  )

  ;; Check for OBJECT with __eq__ special method
  (if (ref.test (ref $OBJECT) (local.get $a))
    (then
      ;; Create string "__eq__" (6 chars: 95,95,101,113,95,95)
      (local.set $offset (global.get $string_heap))
      (i32.store8 (local.get $offset) (i32.const 95))  ;; _
      (i32.store8 (i32.add (local.get $offset) (i32.const 1)) (i32.const 95))  ;; _
      (i32.store8 (i32.add (local.get $offset) (i32.const 2)) (i32.const 101))  ;; e
      (i32.store8 (i32.add (local.get $offset) (i32.const 3)) (i32.const 113))  ;; q
      (i32.store8 (i32.add (local.get $offset) (i32.const 4)) (i32.const 95))  ;; _
      (i32.store8 (i32.add (local.get $offset) (i32.const 5)) (i32.const 95))  ;; _
      (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 6)))
      (local.set $method_name (struct.new $STRING (local.get $offset) (i32.const 6)))

      ;; Call __eq__(self, other) - args = (PAIR self (PAIR other null))
      (local.set $eq_result (call $object_call_method
        (local.get $a)
        (local.get $method_name)
        (struct.new $PAIR
          (local.get $a)
          (struct.new $PAIR (local.get $b) (ref.null eq))
        )
        (ref.null $ENV)
      ))

      ;; If method returned a value, convert to i32
      (if (i32.eqz (ref.is_null (local.get $eq_result)))
        (then
          ;; Check if result is BOOL
          (if (ref.test (ref $BOOL) (local.get $eq_result))
            (then
              (return (struct.get $BOOL 0 (ref.cast (ref $BOOL) (local.get $eq_result))))
            )
          )
          ;; Check if result is i31 (truthy check)
          (if (ref.test (ref i31) (local.get $eq_result))
            (then
              (return (i32.ne (i31.get_s (ref.cast (ref i31) (local.get $eq_result))) (i32.const 0)))
            )
          )
          ;; Non-null non-bool result is truthy
          (return (i32.const 1))
        )
      )
    )
  )

  ;; Reference equality for other types
  (ref.eq (local.get $a) (local.get $b))
)


;; compare_lt: compare two values for less than, dispatching to __lt__ for objects
(func $compare_lt (param $a (ref null eq)) (param $b (ref null eq)) (result i32)
  (local $result (ref null eq))
  (local $method_name (ref $STRING))
  (local $offset i32)

  ;; Check for OBJECT with __lt__ special method
  (if (ref.test (ref $OBJECT) (local.get $a))
    (then
      ;; Create string "__lt__" (6 chars: 95,95,108,116,95,95)
      (local.set $offset (global.get $string_heap))
      (i32.store8 (local.get $offset) (i32.const 95))  ;; _
      (i32.store8 (i32.add (local.get $offset) (i32.const 1)) (i32.const 95))  ;; _
      (i32.store8 (i32.add (local.get $offset) (i32.const 2)) (i32.const 108))  ;; l
      (i32.store8 (i32.add (local.get $offset) (i32.const 3)) (i32.const 116))  ;; t
      (i32.store8 (i32.add (local.get $offset) (i32.const 4)) (i32.const 95))  ;; _
      (i32.store8 (i32.add (local.get $offset) (i32.const 5)) (i32.const 95))  ;; _
      (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 6)))
      (local.set $method_name (struct.new $STRING (local.get $offset) (i32.const 6)))

      ;; Call __lt__(self, other)
      (local.set $result (call $object_call_method
        (local.get $a)
        (local.get $method_name)
        (struct.new $PAIR
          (local.get $a)
          (struct.new $PAIR (local.get $b) (ref.null eq))
        )
        (ref.null $ENV)
      ))

      ;; If method returned a value, convert to i32
      (if (i32.eqz (ref.is_null (local.get $result)))
        (then
          (if (ref.test (ref $BOOL) (local.get $result))
            (then
              (return (struct.get $BOOL 0 (ref.cast (ref $BOOL) (local.get $result))))
            )
          )
          (if (ref.test (ref i31) (local.get $result))
            (then
              (return (i32.ne (i31.get_s (ref.cast (ref i31) (local.get $result))) (i32.const 0)))
            )
          )
          (return (i32.const 1))
        )
      )
    )
  )

  ;; String comparison
  (if (i32.and (ref.test (ref $STRING) (local.get $a)) (ref.test (ref $STRING) (local.get $b)))
    (then
      (return (i32.eq (call $strings_compare
        (ref.cast (ref $STRING) (local.get $a))
        (ref.cast (ref $STRING) (local.get $b))) (i32.const -1)))
    )
  )

  ;; Fall back to numeric comparison (supports i31, INT64, and FLOAT)
  (if (i32.and (call $is_integer (local.get $a)) (call $is_integer (local.get $b)))
    (then
      (return (i64.lt_s (call $to_i64 (local.get $a)) (call $to_i64 (local.get $b))))
    )
  )
  ;; Float comparison
  (if (i32.or (ref.test (ref $FLOAT) (local.get $a)) (ref.test (ref $FLOAT) (local.get $b)))
    (then
      (return (f64.lt (call $to_f64 (local.get $a)) (call $to_f64 (local.get $b))))
    )
  )
  ;; Default i31 comparison (should not reach here normally)
  (i32.lt_s
    (i31.get_s (ref.cast (ref i31) (local.get $a)))
    (i31.get_s (ref.cast (ref i31) (local.get $b)))
  )
)


;; compare_gt: compare two values for greater than, dispatching to __gt__ for objects
(func $compare_gt (param $a (ref null eq)) (param $b (ref null eq)) (result i32)
  (local $result (ref null eq))
  (local $method_name (ref $STRING))
  (local $offset i32)

  ;; Check for OBJECT with __gt__ special method
  (if (ref.test (ref $OBJECT) (local.get $a))
    (then
      ;; Create string "__gt__" (6 chars: 95,95,103,116,95,95)
      (local.set $offset (global.get $string_heap))
      (i32.store8 (local.get $offset) (i32.const 95))  ;; _
      (i32.store8 (i32.add (local.get $offset) (i32.const 1)) (i32.const 95))  ;; _
      (i32.store8 (i32.add (local.get $offset) (i32.const 2)) (i32.const 103))  ;; g
      (i32.store8 (i32.add (local.get $offset) (i32.const 3)) (i32.const 116))  ;; t
      (i32.store8 (i32.add (local.get $offset) (i32.const 4)) (i32.const 95))  ;; _
      (i32.store8 (i32.add (local.get $offset) (i32.const 5)) (i32.const 95))  ;; _
      (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 6)))
      (local.set $method_name (struct.new $STRING (local.get $offset) (i32.const 6)))

      ;; Call __gt__(self, other)
      (local.set $result (call $object_call_method
        (local.get $a)
        (local.get $method_name)
        (struct.new $PAIR
          (local.get $a)
          (struct.new $PAIR (local.get $b) (ref.null eq))
        )
        (ref.null $ENV)
      ))

      ;; If method returned a value, convert to i32
      (if (i32.eqz (ref.is_null (local.get $result)))
        (then
          (if (ref.test (ref $BOOL) (local.get $result))
            (then
              (return (struct.get $BOOL 0 (ref.cast (ref $BOOL) (local.get $result))))
            )
          )
          (if (ref.test (ref i31) (local.get $result))
            (then
              (return (i32.ne (i31.get_s (ref.cast (ref i31) (local.get $result))) (i32.const 0)))
            )
          )
          (return (i32.const 1))
        )
      )
    )
  )

  ;; String comparison
  (if (i32.and (ref.test (ref $STRING) (local.get $a)) (ref.test (ref $STRING) (local.get $b)))
    (then
      (return (i32.eq (call $strings_compare
        (ref.cast (ref $STRING) (local.get $a))
        (ref.cast (ref $STRING) (local.get $b))) (i32.const 1)))
    )
  )

  ;; Fall back to numeric comparison (supports i31, INT64, and FLOAT)
  (if (i32.and (call $is_integer (local.get $a)) (call $is_integer (local.get $b)))
    (then
      (return (i64.gt_s (call $to_i64 (local.get $a)) (call $to_i64 (local.get $b))))
    )
  )
  ;; Float comparison
  (if (i32.or (ref.test (ref $FLOAT) (local.get $a)) (ref.test (ref $FLOAT) (local.get $b)))
    (then
      (return (f64.gt (call $to_f64 (local.get $a)) (call $to_f64 (local.get $b))))
    )
  )
  ;; Default i31 comparison
  (i32.gt_s
    (i31.get_s (ref.cast (ref i31) (local.get $a)))
    (i31.get_s (ref.cast (ref i31) (local.get $b)))
  )
)


;; compare_le: compare two values for less than or equal, dispatching to __le__ for objects
(func $compare_le (param $a (ref null eq)) (param $b (ref null eq)) (result i32)
  (local $result (ref null eq))
  (local $method_name (ref $STRING))
  (local $offset i32)

  ;; Check for OBJECT with __le__ special method
  (if (ref.test (ref $OBJECT) (local.get $a))
    (then
      ;; Create string "__le__" (6 chars: 95,95,108,101,95,95)
      (local.set $offset (global.get $string_heap))
      (i32.store8 (local.get $offset) (i32.const 95))  ;; _
      (i32.store8 (i32.add (local.get $offset) (i32.const 1)) (i32.const 95))  ;; _
      (i32.store8 (i32.add (local.get $offset) (i32.const 2)) (i32.const 108))  ;; l
      (i32.store8 (i32.add (local.get $offset) (i32.const 3)) (i32.const 101))  ;; e
      (i32.store8 (i32.add (local.get $offset) (i32.const 4)) (i32.const 95))  ;; _
      (i32.store8 (i32.add (local.get $offset) (i32.const 5)) (i32.const 95))  ;; _
      (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 6)))
      (local.set $method_name (struct.new $STRING (local.get $offset) (i32.const 6)))

      ;; Call __le__(self, other)
      (local.set $result (call $object_call_method
        (local.get $a)
        (local.get $method_name)
        (struct.new $PAIR
          (local.get $a)
          (struct.new $PAIR (local.get $b) (ref.null eq))
        )
        (ref.null $ENV)
      ))

      ;; If method returned a value, convert to i32
      (if (i32.eqz (ref.is_null (local.get $result)))
        (then
          (if (ref.test (ref $BOOL) (local.get $result))
            (then
              (return (struct.get $BOOL 0 (ref.cast (ref $BOOL) (local.get $result))))
            )
          )
          (if (ref.test (ref i31) (local.get $result))
            (then
              (return (i32.ne (i31.get_s (ref.cast (ref i31) (local.get $result))) (i32.const 0)))
            )
          )
          (return (i32.const 1))
        )
      )
    )
  )

  ;; String comparison
  (if (i32.and (ref.test (ref $STRING) (local.get $a)) (ref.test (ref $STRING) (local.get $b)))
    (then
      (return (i32.le_s (call $strings_compare
        (ref.cast (ref $STRING) (local.get $a))
        (ref.cast (ref $STRING) (local.get $b))) (i32.const 0)))
    )
  )

  ;; Fall back to numeric comparison (supports i31, INT64, and FLOAT)
  (if (i32.and (call $is_integer (local.get $a)) (call $is_integer (local.get $b)))
    (then
      (return (i64.le_s (call $to_i64 (local.get $a)) (call $to_i64 (local.get $b))))
    )
  )
  ;; Float comparison
  (if (i32.or (ref.test (ref $FLOAT) (local.get $a)) (ref.test (ref $FLOAT) (local.get $b)))
    (then
      (return (f64.le (call $to_f64 (local.get $a)) (call $to_f64 (local.get $b))))
    )
  )
  ;; Default i31 comparison
  (i32.le_s
    (i31.get_s (ref.cast (ref i31) (local.get $a)))
    (i31.get_s (ref.cast (ref i31) (local.get $b)))
  )
)


;; compare_ge: compare two values for greater than or equal, dispatching to __ge__ for objects
(func $compare_ge (param $a (ref null eq)) (param $b (ref null eq)) (result i32)
  (local $result (ref null eq))
  (local $method_name (ref $STRING))
  (local $offset i32)

  ;; Check for OBJECT with __ge__ special method
  (if (ref.test (ref $OBJECT) (local.get $a))
    (then
      ;; Create string "__ge__" (6 chars: 95,95,103,101,95,95)
      (local.set $offset (global.get $string_heap))
      (i32.store8 (local.get $offset) (i32.const 95))  ;; _
      (i32.store8 (i32.add (local.get $offset) (i32.const 1)) (i32.const 95))  ;; _
      (i32.store8 (i32.add (local.get $offset) (i32.const 2)) (i32.const 103))  ;; g
      (i32.store8 (i32.add (local.get $offset) (i32.const 3)) (i32.const 101))  ;; e
      (i32.store8 (i32.add (local.get $offset) (i32.const 4)) (i32.const 95))  ;; _
      (i32.store8 (i32.add (local.get $offset) (i32.const 5)) (i32.const 95))  ;; _
      (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 6)))
      (local.set $method_name (struct.new $STRING (local.get $offset) (i32.const 6)))

      ;; Call __ge__(self, other)
      (local.set $result (call $object_call_method
        (local.get $a)
        (local.get $method_name)
        (struct.new $PAIR
          (local.get $a)
          (struct.new $PAIR (local.get $b) (ref.null eq))
        )
        (ref.null $ENV)
      ))

      ;; If method returned a value, convert to i32
      (if (i32.eqz (ref.is_null (local.get $result)))
        (then
          (if (ref.test (ref $BOOL) (local.get $result))
            (then
              (return (struct.get $BOOL 0 (ref.cast (ref $BOOL) (local.get $result))))
            )
          )
          (if (ref.test (ref i31) (local.get $result))
            (then
              (return (i32.ne (i31.get_s (ref.cast (ref i31) (local.get $result))) (i32.const 0)))
            )
          )
          (return (i32.const 1))
        )
      )
    )
  )

  ;; String comparison
  (if (i32.and (ref.test (ref $STRING) (local.get $a)) (ref.test (ref $STRING) (local.get $b)))
    (then
      (return (i32.ge_s (call $strings_compare
        (ref.cast (ref $STRING) (local.get $a))
        (ref.cast (ref $STRING) (local.get $b))) (i32.const 0)))
    )
  )

  ;; Fall back to numeric comparison (supports i31, INT64, and FLOAT)
  (if (i32.and (call $is_integer (local.get $a)) (call $is_integer (local.get $b)))
    (then
      (return (i64.ge_s (call $to_i64 (local.get $a)) (call $to_i64 (local.get $b))))
    )
  )
  ;; Float comparison
  (if (i32.or (ref.test (ref $FLOAT) (local.get $a)) (ref.test (ref $FLOAT) (local.get $b)))
    (then
      (return (f64.ge (call $to_f64 (local.get $a)) (call $to_f64 (local.get $b))))
    )
  )
  ;; Default i31 comparison
  (i32.ge_s
    (i31.get_s (ref.cast (ref i31) (local.get $a)))
    (i31.get_s (ref.cast (ref i31) (local.get $b)))
  )
)


;; dicts_equal: compare two dict PAIR chains for equality
;; Dicts are equal if they have the same keys with equal values (order-independent)
(func $dicts_equal (param $a (ref null eq)) (param $b (ref null eq)) (result i32)
  (local $current_a (ref null eq))
  (local $entry_a (ref null eq))
  (local $key_a (ref null eq))
  (local $val_a (ref null eq))
  (local $val_b (ref null eq))
  (local $len_a i32)
  (local $len_b i32)
  (local $entries (ref null eq))

  ;; Both null = equal (both empty)
  (if (i32.and (ref.is_null (local.get $a)) (ref.is_null (local.get $b)))
    (then (return (i32.const 1)))
  )
  ;; One null, one not = not equal
  (if (i32.or (ref.is_null (local.get $a)) (ref.is_null (local.get $b)))
    (then (return (i32.const 0)))
  )

  ;; Handle $DICT (hash table based)
  (if (i32.and (ref.test (ref $DICT) (local.get $a)) (ref.test (ref $DICT) (local.get $b)))
    (then
      ;; Compare lengths first (using hash table count)
      (local.set $len_a (struct.get $HASHTABLE $count
        (struct.get $DICT $table (ref.cast (ref $DICT) (local.get $a)))))
      (local.set $len_b (struct.get $HASHTABLE $count
        (struct.get $DICT $table (ref.cast (ref $DICT) (local.get $b)))))
      (if (i32.ne (local.get $len_a) (local.get $len_b))
        (then (return (i32.const 0)))
      )

      ;; Get entries from dict a
      (local.set $entries (call $hashtable_entries
        (struct.get $DICT $table (ref.cast (ref $DICT) (local.get $a)))))

      ;; For each entry in a, check that b has the same key with equal value
      (local.set $current_a (local.get $entries))
      (block $done
        (loop $loop
          (br_if $done (ref.is_null (local.get $current_a)))
          (if (i32.eqz (ref.test (ref $PAIR) (local.get $current_a)))
            (then (br $done))
          )
          (local.set $entry_a (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $current_a))))
          (local.set $key_a (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $entry_a))))
          (local.set $val_a (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $entry_a))))
          ;; Look up key_a in b
          (local.set $val_b (call $dict_get (local.get $b) (local.get $key_a)))
          ;; Check if values are equal
          (if (i32.eqz (call $values_equal (local.get $val_a) (local.get $val_b)))
            (then (return (i32.const 0)))
          )
          (local.set $current_a (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current_a))))
          (br $loop)
        )
      )
      (return (i32.const 1))
    )
  )

  ;; Legacy: handle PAIR chain dicts
  (local.set $len_a (call $list_len (local.get $a)))
  (local.set $len_b (call $list_len (local.get $b)))
  (if (i32.ne (local.get $len_a) (local.get $len_b))
    (then (return (i32.const 0)))
  )
  ;; For each key in a, check that b has the same key with equal value
  (local.set $current_a (local.get $a))
  (block $done
    (loop $loop
      (br_if $done (ref.is_null (local.get $current_a)))
      (local.set $entry_a (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $current_a))))
      (local.set $key_a (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $entry_a))))
      (local.set $val_a (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $entry_a))))
      ;; Look up key_a in b
      (local.set $val_b (call $dict_get (local.get $b) (local.get $key_a)))
      (if (i32.eqz (call $values_equal (local.get $val_a) (local.get $val_b)))
        (then (return (i32.const 0)))
      )
      (local.set $current_a (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current_a))))
      (br $loop)
    )
  )
  ;; All keys matched with equal values
  (i32.const 1)
)


;; numeric_lt: compare two numeric values (a < b), returns i32 boolean
;; Works with i31, INT64, and FLOAT types
(func $numeric_lt (param $a (ref null eq)) (param $b (ref null eq)) (result i32)
  (f64.lt (call $to_f64 (local.get $a)) (call $to_f64 (local.get $b)))
)


;; numeric_gt: compare two numeric values (a > b), returns i32 boolean
;; Works with i31, INT64, and FLOAT types
(func $numeric_gt (param $a (ref null eq)) (param $b (ref null eq)) (result i32)
  (f64.gt (call $to_f64 (local.get $a)) (call $to_f64 (local.get $b)))
)


;; Helper: value_equals - compare two values for equality
(func $value_equals (param $a (ref null eq)) (param $b (ref null eq)) (result i32)
  ;; Both null
  (if (i32.and (ref.is_null (local.get $a)) (ref.is_null (local.get $b)))
    (then (return (i32.const 1)))
  )
  ;; One null
  (if (i32.or (ref.is_null (local.get $a)) (ref.is_null (local.get $b)))
    (then (return (i32.const 0)))
  )
  ;; Both i31 (integers)
  (if (i32.and (ref.test (ref i31) (local.get $a)) (ref.test (ref i31) (local.get $b)))
    (then
      (return (i32.eq
        (i31.get_s (ref.cast (ref i31) (local.get $a)))
        (i31.get_s (ref.cast (ref i31) (local.get $b)))))
    )
  )
  ;; Both strings
  (if (i32.and (ref.test (ref $STRING) (local.get $a)) (ref.test (ref $STRING) (local.get $b)))
    (then
      (return (call $string_equals
        (ref.cast (ref $STRING) (local.get $a))
        (ref.cast (ref $STRING) (local.get $b))))
    )
  )
  ;; Reference equality for other types
  (ref.eq (local.get $a) (local.get $b))
)

"""
