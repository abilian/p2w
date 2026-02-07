"""WAT helper functions: List operations (PAIR-based and array-backed)."""

from __future__ import annotations

LISTS_CODE = """

;; ============================================================================

;; list_get: get element at index from PAIR chain (also handles 2-element tuples)
(func $list_get (param $list (ref null eq)) (param $idx i32) (result (ref null eq))
  (local $current (ref null eq))
  (local $cdr (ref null eq))
  (local $i i32)
  (local $len i32)

  ;; Handle negative index
  (if (i32.lt_s (local.get $idx) (i32.const 0))
    (then
      (local.set $len (call $list_len (local.get $list)))
      (local.set $idx (i32.add (local.get $len) (local.get $idx)))
      ;; Still negative means out of bounds
      (if (i32.lt_s (local.get $idx) (i32.const 0))
        (then (return (ref.null eq)))
      )
    )
  )

  (local.set $current (local.get $list))
  (local.set $i (i32.const 0))
  (block $done
    (loop $loop
      (br_if $done (ref.is_null (local.get $current)))
      ;; Check if current is a PAIR
      (if (i32.eqz (ref.test (ref $PAIR) (local.get $current)))
        (then (br $done))
      )
      (if (i32.eq (local.get $i) (local.get $idx))
        (then
          (return (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $current))))
        )
      )
      ;; Get cdr
      (local.set $cdr (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current))))
      ;; For 2-element tuple: if cdr is not PAIR and idx is 1, return cdr
      (if (i32.and
            (i32.eqz (ref.test (ref $PAIR) (local.get $cdr)))
            (i32.eq (i32.add (local.get $i) (i32.const 1)) (local.get $idx)))
        (then
          ;; cdr is not a PAIR but we want index i+1, return cdr (2-element tuple)
          (return (local.get $cdr))
        )
      )
      (local.set $current (local.get $cdr))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $loop)
    )
  )
  ;; Index out of bounds - return null
  (ref.null eq)
)


;; list_len: get length of list (PAIR chain or $LIST)
(func $list_len (param $list (ref null eq)) (result i32)
  (local $current (ref null eq))
  (local $len i32)

  ;; Handle null
  (if (ref.is_null (local.get $list))
    (then (return (i32.const 0)))
  )

  ;; Handle $EMPTY_LIST
  (if (ref.test (ref $EMPTY_LIST) (local.get $list))
    (then (return (i32.const 0)))
  )

  ;; Handle $LIST (array-backed) - O(1) length
  (if (ref.test (ref $LIST) (local.get $list))
    (then
      (return (struct.get $LIST 1 (ref.cast (ref $LIST) (local.get $list))))
    )
  )

  ;; PAIR chain path - O(n) count
  (local.set $current (local.get $list))
  (local.set $len (i32.const 0))
  (block $done
    (loop $loop
      (br_if $done (ref.is_null (local.get $current)))
      (br_if $done (i32.eqz (ref.test (ref $PAIR) (local.get $current))))
      (local.set $len (i32.add (local.get $len) (i32.const 1)))
      (local.set $current (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current))))
      (br $loop)
    )
  )
  (local.get $len)
)


;; list_get_index: get element at index from PAIR chain
(func $list_get_index (param $list (ref null eq)) (param $idx i32) (result (ref null eq))
  (local $current (ref null eq))
  (local $i i32)
  (local $len i32)

  ;; Handle negative index
  (if (i32.lt_s (local.get $idx) (i32.const 0))
    (then
      (local.set $len (call $list_len (local.get $list)))
      (local.set $idx (i32.add (local.get $len) (local.get $idx)))
      (if (i32.lt_s (local.get $idx) (i32.const 0))
        (then (return (ref.null eq)))
      )
    )
  )

  (local.set $current (local.get $list))
  (local.set $i (i32.const 0))
  (block $done
    (loop $loop
      (br_if $done (ref.is_null (local.get $current)))
      (if (i32.eq (local.get $i) (local.get $idx))
        (then (return (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $current)))))
      )
      (local.set $current (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current))))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $loop)
    )
  )
  (ref.null eq)
)


;; list_reverse: reverse a list (returns new PAIR chain)
(func $list_reverse (param $list (ref null eq)) (result (ref null eq))
  (local $current (ref null eq))
  (local $result (ref null eq))
  (local $list_ref (ref null $LIST))
  (local $arr (ref null $ARRAY_ANY))
  (local $len i32)
  (local $i i32)

  ;; Handle null
  (if (ref.is_null (local.get $list))
    (then (return (ref.null eq)))
  )

  ;; Handle $EMPTY_LIST
  (if (ref.test (ref $EMPTY_LIST) (local.get $list))
    (then (return (ref.null eq)))
  )

  ;; Handle $LIST type - build reversed PAIR chain
  (if (ref.test (ref $LIST) (local.get $list))
    (then
      (local.set $list_ref (ref.cast (ref $LIST) (local.get $list)))
      (local.set $arr (struct.get $LIST 0 (ref.cast (ref $LIST) (local.get $list_ref))))
      (local.set $len (struct.get $LIST 1 (ref.cast (ref $LIST) (local.get $list_ref))))
      (if (i32.eqz (local.get $len))
        (then (return (ref.null eq)))
      )
      ;; Build reversed PAIR chain from array
      (local.set $result (ref.null eq))
      (local.set $i (i32.const 0))
      (block $done_arr
        (loop $loop_arr
          (br_if $done_arr (i32.ge_s (local.get $i) (local.get $len)))
          ;; Prepend element at index $i to result (building in reverse naturally)
          (local.set $result (struct.new $PAIR
            (array.get $ARRAY_ANY (ref.cast (ref $ARRAY_ANY) (local.get $arr)) (local.get $i))
            (local.get $result)))
          (local.set $i (i32.add (local.get $i) (i32.const 1)))
          (br $loop_arr)
        )
      )
      (return (local.get $result))
    )
  )

  ;; Handle $TUPLE - convert to reversed PAIR chain
  (if (ref.test (ref $TUPLE) (local.get $list))
    (then
      (local.set $arr (struct.get $TUPLE 0 (ref.cast (ref $TUPLE) (local.get $list))))
      (local.set $len (struct.get $TUPLE 1 (ref.cast (ref $TUPLE) (local.get $list))))
      (if (i32.eqz (local.get $len))
        (then (return (ref.null eq)))
      )
      ;; Build reversed PAIR chain from array
      (local.set $result (ref.null eq))
      (local.set $i (i32.const 0))
      (block $done_tup
        (loop $loop_tup
          (br_if $done_tup (i32.ge_s (local.get $i) (local.get $len)))
          (local.set $result (struct.new $PAIR
            (array.get $ARRAY_ANY (ref.cast (ref $ARRAY_ANY) (local.get $arr)) (local.get $i))
            (local.get $result)))
          (local.set $i (i32.add (local.get $i) (i32.const 1)))
          (br $loop_tup)
        )
      )
      (return (local.get $result))
    )
  )

  ;; PAIR chain path
  (local.set $current (local.get $list))
  (local.set $result (ref.null eq))
  (block $done
    (loop $loop
      (br_if $done (ref.is_null (local.get $current)))
      (br_if $done (ref.test (ref $EMPTY_LIST) (local.get $current)))
      (br_if $done (i32.eqz (ref.test (ref $PAIR) (local.get $current))))
      ;; Prepend current element to result
      (local.set $result (struct.new $PAIR
        (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $current)))
        (local.get $result)))
      (local.set $current (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current))))
      (br $loop)
    )
  )
  (local.get $result)
)


;; copy_list: create a shallow copy of a list (returns PAIR chain)
(func $copy_list (param $list (ref null eq)) (result (ref null eq))
  (local $current (ref null eq))
  (local $result (ref null eq))
  (local $tail (ref null eq))
  (local $tuple_ref (ref $TUPLE))
  (local $arr (ref $ARRAY_ANY))
  (local $len i32)
  (local $i i32)
  ;; Handle null -> return empty list marker
  (if (ref.is_null (local.get $list))
    (then (return (struct.new $EMPTY_LIST)))
  )
  ;; Handle EMPTY_LIST marker -> return new empty list marker
  (if (ref.test (ref $EMPTY_LIST) (local.get $list))
    (then (return (struct.new $EMPTY_LIST)))
  )
  ;; Handle $LIST (array-backed) -> convert to PAIR chain
  (if (ref.test (ref $LIST) (local.get $list))
    (then
      (local.set $arr (struct.get $LIST 0 (ref.cast (ref $LIST) (local.get $list))))
      (local.set $len (struct.get $LIST 1 (ref.cast (ref $LIST) (local.get $list))))
      ;; Empty list -> return empty list marker
      (if (i32.eqz (local.get $len))
        (then (return (struct.new $EMPTY_LIST)))
      )
      ;; Build PAIR chain from array elements (back to front)
      (local.set $result (ref.null eq))
      (local.set $i (i32.sub (local.get $len) (i32.const 1)))
      (block $done_list
        (loop $loop_list
          (br_if $done_list (i32.lt_s (local.get $i) (i32.const 0)))
          ;; Prepend element to result
          (local.set $result
            (struct.new $PAIR
              (array.get $ARRAY_ANY (local.get $arr) (local.get $i))
              (local.get $result)))
          (local.set $i (i32.sub (local.get $i) (i32.const 1)))
          (br $loop_list)
        )
      )
      (return (local.get $result))
    )
  )
  ;; Handle TUPLE -> convert to PAIR chain
  (if (ref.test (ref $TUPLE) (local.get $list))
    (then
      (local.set $tuple_ref (ref.cast (ref $TUPLE) (local.get $list)))
      (local.set $arr (struct.get $TUPLE 0 (local.get $tuple_ref)))
      (local.set $len (struct.get $TUPLE 1 (local.get $tuple_ref)))
      ;; Empty tuple -> return empty list
      (if (i32.eqz (local.get $len))
        (then (return (struct.new $EMPTY_LIST)))
      )
      ;; Build PAIR chain from tuple elements
      (local.set $result (ref.null eq))
      (local.set $i (i32.sub (local.get $len) (i32.const 1)))
      (block $done
        (loop $loop
          (br_if $done (i32.lt_s (local.get $i) (i32.const 0)))
          ;; Prepend element to result
          (local.set $result
            (struct.new $PAIR
              (array.get $ARRAY_ANY (local.get $arr) (local.get $i))
              (local.get $result)))
          (local.set $i (i32.sub (local.get $i) (i32.const 1)))
          (br $loop)
        )
      )
      (return (local.get $result))
    )
  )
  (local.set $current (local.get $list))
  (local.set $result (ref.null eq))
  (block $done
    (loop $loop
      ;; Exit if current is null or not a PAIR
      (br_if $done (ref.is_null (local.get $current)))
      (br_if $done (i32.eqz (ref.test (ref $PAIR) (local.get $current))))
      (if (ref.is_null (local.get $result))
        (then
          (local.set $result (struct.new $PAIR
            (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $current)))
            (ref.null eq)))
          (local.set $tail (local.get $result))
        )
        (else
          (struct.set $PAIR 1 (ref.cast (ref $PAIR) (local.get $tail))
            (struct.new $PAIR
              (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $current)))
              (ref.null eq)))
          (local.set $tail (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $tail))))
        )
      )
      (local.set $current (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current))))
      (br $loop)
    )
  )
  (local.get $result)
)


;; ============================================================================
;; Array-Based List Functions ($LIST type) - O(1) indexed access
;; These provide O(1) random access, O(1) length, and amortized O(1) append
;; ============================================================================

;; list_v2_new: create empty list with initial capacity
(func $list_v2_new (param $cap i32) (result (ref $LIST))
  ;; Ensure minimum capacity of 4
  (if (i32.lt_s (local.get $cap) (i32.const 4))
    (then (local.set $cap (i32.const 4)))
  )
  (struct.new $LIST
    (array.new $ARRAY_ANY (ref.null eq) (local.get $cap))
    (i32.const 0)
    (local.get $cap)
  )
)


;; list_v2_len: O(1) length access
(func $list_v2_len (param $list (ref $LIST)) (result i32)
  (struct.get $LIST $len (local.get $list))
)


;; list_v2_get: O(1) indexed access with negative index support
(func $list_v2_get (param $list (ref $LIST)) (param $idx i32) (result (ref null eq))
  (local $real_idx i32)
  (local $len i32)
  (local.set $len (struct.get $LIST $len (local.get $list)))

  ;; Handle negative index
  (if (i32.lt_s (local.get $idx) (i32.const 0))
    (then (local.set $real_idx (i32.add (local.get $len) (local.get $idx))))
    (else (local.set $real_idx (local.get $idx)))
  )

  ;; Bounds check
  (if (i32.or
        (i32.lt_s (local.get $real_idx) (i32.const 0))
        (i32.ge_s (local.get $real_idx) (local.get $len)))
    (then (return (ref.null eq)))  ;; Out of bounds
  )

  (array.get $ARRAY_ANY
    (struct.get $LIST $data (local.get $list))
    (local.get $real_idx)
  )
)


;; list_v2_delete_at: delete element at index from $LIST (in-place mutation)
(func $list_v2_delete_at (param $list (ref $LIST)) (param $idx i32) (result (ref null eq))
  (local $real_idx i32)
  (local $len i32)
  (local $data (ref $ARRAY_ANY))
  (local $i i32)

  (local.set $len (struct.get $LIST $len (local.get $list)))
  (local.set $data (struct.get $LIST $data (local.get $list)))

  ;; Handle negative index
  (if (i32.lt_s (local.get $idx) (i32.const 0))
    (then (local.set $real_idx (i32.add (local.get $len) (local.get $idx))))
    (else (local.set $real_idx (local.get $idx)))
  )

  ;; Bounds check
  (if (i32.or
        (i32.lt_s (local.get $real_idx) (i32.const 0))
        (i32.ge_s (local.get $real_idx) (local.get $len)))
    (then (return (local.get $list)))  ;; Out of bounds - return unchanged
  )

  ;; Shift elements left to fill the gap
  (local.set $i (local.get $real_idx))
  (block $shift_done
    (loop $shift_loop
      (br_if $shift_done (i32.ge_s (local.get $i) (i32.sub (local.get $len) (i32.const 1))))
      (array.set $ARRAY_ANY (local.get $data) (local.get $i)
        (array.get $ARRAY_ANY (local.get $data) (i32.add (local.get $i) (i32.const 1))))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $shift_loop)
    )
  )

  ;; Decrease length
  (struct.set $LIST $len (local.get $list) (i32.sub (local.get $len) (i32.const 1)))

  (local.get $list)
)


;; ensure_list: convert TUPLE to PAIR chain if needed, pass through other types
;; Used for starred unpacking which always produces a list
(func $ensure_list (param $val (ref null eq)) (result (ref null eq))
  (if (ref.test (ref $TUPLE) (local.get $val))
    (then (return (call $tuple_to_pair (ref.cast (ref $TUPLE) (local.get $val)))))
  )
  (local.get $val)
)


;; list_v2_set: O(1) indexed set with negative index support
(func $list_v2_set (param $list (ref $LIST)) (param $idx i32) (param $val (ref null eq))
  (local $real_idx i32)
  (local $len i32)
  (local.set $len (struct.get $LIST $len (local.get $list)))

  ;; Handle negative index
  (if (i32.lt_s (local.get $idx) (i32.const 0))
    (then (local.set $real_idx (i32.add (local.get $len) (local.get $idx))))
    (else (local.set $real_idx (local.get $idx)))
  )

  ;; Bounds check - silently ignore out of bounds
  (if (i32.and
        (i32.ge_s (local.get $real_idx) (i32.const 0))
        (i32.lt_s (local.get $real_idx) (local.get $len)))
    (then
      (array.set $ARRAY_ANY
        (struct.get $LIST $data (local.get $list))
        (local.get $real_idx)
        (local.get $val)
      )
    )
  )
)


;; list_v2_append: amortized O(1) append with automatic growth
(func $list_v2_append (param $list (ref $LIST)) (param $val (ref null eq)) (result (ref $LIST))
  (local $len i32)
  (local $cap i32)
  (local $new_cap i32)
  (local $new_data (ref $ARRAY_ANY))
  (local $old_data (ref $ARRAY_ANY))
  (local $i i32)

  (local.set $len (struct.get $LIST $len (local.get $list)))
  (local.set $cap (struct.get $LIST $cap (local.get $list)))

  ;; Grow if needed
  (if (i32.ge_s (local.get $len) (local.get $cap))
    (then
      ;; Double capacity
      (local.set $new_cap (i32.mul (local.get $cap) (i32.const 2)))
      (if (i32.eqz (local.get $new_cap))
        (then (local.set $new_cap (i32.const 4)))
      )
      (local.set $new_data (array.new $ARRAY_ANY (ref.null eq) (local.get $new_cap)))
      (local.set $old_data (struct.get $LIST $data (local.get $list)))
      ;; Copy existing elements
      (local.set $i (i32.const 0))
      (block $done
        (loop $copy_loop
          (br_if $done (i32.ge_s (local.get $i) (local.get $len)))
          (array.set $ARRAY_ANY (local.get $new_data) (local.get $i)
            (array.get $ARRAY_ANY (local.get $old_data) (local.get $i)))
          (local.set $i (i32.add (local.get $i) (i32.const 1)))
          (br $copy_loop)
        )
      )
      (struct.set $LIST $data (local.get $list) (local.get $new_data))
      (struct.set $LIST $cap (local.get $list) (local.get $new_cap))
    )
  )

  ;; Append element
  (array.set $ARRAY_ANY
    (struct.get $LIST $data (local.get $list))
    (local.get $len)
    (local.get $val)
  )
  (struct.set $LIST $len (local.get $list) (i32.add (local.get $len) (i32.const 1)))

  (local.get $list)
)


;; list_v2_pop: O(1) remove and return last element
(func $list_v2_pop (param $list (ref $LIST)) (result (ref null eq))
  (local $len i32)
  (local $val (ref null eq))
  (local.set $len (struct.get $LIST $len (local.get $list)))

  ;; Empty list returns null
  (if (i32.eqz (local.get $len))
    (then (return (ref.null eq)))
  )

  ;; Get last element
  (local.set $len (i32.sub (local.get $len) (i32.const 1)))
  (local.set $val (array.get $ARRAY_ANY
    (struct.get $LIST $data (local.get $list))
    (local.get $len)))

  ;; Clear the slot (for GC) and update length
  (array.set $ARRAY_ANY
    (struct.get $LIST $data (local.get $list))
    (local.get $len)
    (ref.null eq))
  (struct.set $LIST $len (local.get $list) (local.get $len))

  (local.get $val)
)


;; list_v2_copy: create a shallow copy
(func $list_v2_copy (param $list (ref $LIST)) (result (ref $LIST))
  (local $len i32)
  (local $new_list (ref $LIST))
  (local $old_data (ref $ARRAY_ANY))
  (local $new_data (ref $ARRAY_ANY))
  (local $i i32)

  (local.set $len (struct.get $LIST $len (local.get $list)))
  (local.set $new_list (call $list_v2_new (local.get $len)))
  (local.set $old_data (struct.get $LIST $data (local.get $list)))
  (local.set $new_data (struct.get $LIST $data (local.get $new_list)))

  ;; Copy elements
  (local.set $i (i32.const 0))
  (block $done
    (loop $copy_loop
      (br_if $done (i32.ge_s (local.get $i) (local.get $len)))
      (array.set $ARRAY_ANY (local.get $new_data) (local.get $i)
        (array.get $ARRAY_ANY (local.get $old_data) (local.get $i)))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $copy_loop)
    )
  )
  (struct.set $LIST $len (local.get $new_list) (local.get $len))

  (local.get $new_list)
)


;; list_v2_to_pair: convert $LIST to PAIR chain (for compatibility)
(func $list_v2_to_pair (param $list (ref $LIST)) (result (ref null eq))
  (local $len i32)
  (local $i i32)
  (local $result (ref null eq))
  (local $data (ref $ARRAY_ANY))

  (local.set $len (struct.get $LIST $len (local.get $list)))
  (if (i32.eqz (local.get $len))
    (then (return (ref.null eq)))
  )

  (local.set $data (struct.get $LIST $data (local.get $list)))
  (local.set $result (ref.null eq))

  ;; Build PAIR chain from end to start
  (local.set $i (local.get $len))
  (block $done
    (loop $build_loop
      (br_if $done (i32.eqz (local.get $i)))
      (local.set $i (i32.sub (local.get $i) (i32.const 1)))
      (local.set $result (struct.new $PAIR
        (array.get $ARRAY_ANY (local.get $data) (local.get $i))
        (local.get $result)))
      (br $build_loop)
    )
  )

  (local.get $result)
)


;; list_v2_equal: compare two $LIST structs for deep equality
(func $list_v2_equal (param $a (ref $LIST)) (param $b (ref $LIST)) (result i32)
  (local $len_a i32)
  (local $len_b i32)
  (local $i i32)
  (local $data_a (ref $ARRAY_ANY))
  (local $data_b (ref $ARRAY_ANY))

  (local.set $len_a (struct.get $LIST 1 (local.get $a)))
  (local.set $len_b (struct.get $LIST 1 (local.get $b)))

  ;; Different lengths -> not equal
  (if (i32.ne (local.get $len_a) (local.get $len_b))
    (then (return (i32.const 0)))
  )

  ;; Both empty -> equal
  (if (i32.eqz (local.get $len_a))
    (then (return (i32.const 1)))
  )

  ;; Compare element by element
  (local.set $data_a (struct.get $LIST 0 (local.get $a)))
  (local.set $data_b (struct.get $LIST 0 (local.get $b)))
  (local.set $i (i32.const 0))

  (block $done
    (loop $compare_loop
      (br_if $done (i32.ge_s (local.get $i) (local.get $len_a)))
      ;; Compare elements using values_equal
      (if (i32.eqz (call $values_equal
            (array.get $ARRAY_ANY (local.get $data_a) (local.get $i))
            (array.get $ARRAY_ANY (local.get $data_b) (local.get $i))))
        (then (return (i32.const 0)))
      )
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $compare_loop)
    )
  )

  (i32.const 1)
)


;; pair_to_list_v2: convert PAIR chain to $LIST
(func $pair_to_list_v2 (param $pair (ref null eq)) (result (ref $LIST))
  (local $len i32)
  (local $list (ref $LIST))
  (local $current (ref null eq))

  ;; First count elements
  (local.set $len (call $list_len (local.get $pair)))
  (local.set $list (call $list_v2_new (local.get $len)))

  ;; Copy elements
  (local.set $current (local.get $pair))
  (block $done
    (loop $copy_loop
      (br_if $done (ref.is_null (local.get $current)))
      (if (i32.eqz (ref.test (ref $PAIR) (local.get $current)))
        (then (br $done))
      )
      (drop (call $list_v2_append (local.get $list)
        (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $current)))))
      (local.set $current (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current))))
      (br $copy_loop)
    )
  )

  (local.get $list)
)


;; list_v2_to_string: convert $LIST to string "[elem, elem, ...]"
(func $list_v2_to_string (param $list (ref $LIST)) (result (ref $STRING))
  (local $i i32)
  (local $len i32)
  (local $result (ref $STRING))
  (local $elem_str (ref $STRING))
  (local $bracket_open (ref $STRING))
  (local $bracket_close (ref $STRING))
  (local $comma_space (ref $STRING))
  (local $offset i32)

  (local.set $len (struct.get $LIST $len (local.get $list)))

  ;; Create "[" (1 char)
  (local.set $offset (global.get $string_heap))
  (i32.store8 (local.get $offset) (i32.const 91))  ;; [
  (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 1)))
  (local.set $bracket_open (struct.new $STRING (local.get $offset) (i32.const 1)))

  ;; Create "]" (1 char)
  (local.set $offset (global.get $string_heap))
  (i32.store8 (local.get $offset) (i32.const 93))  ;; ]
  (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 1)))
  (local.set $bracket_close (struct.new $STRING (local.get $offset) (i32.const 1)))

  ;; Create ", " (2 chars)
  (local.set $offset (global.get $string_heap))
  (i32.store8 (local.get $offset) (i32.const 44))  ;; ,
  (i32.store8 (i32.add (local.get $offset) (i32.const 1)) (i32.const 32))  ;; space
  (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 2)))
  (local.set $comma_space (struct.new $STRING (local.get $offset) (i32.const 2)))

  ;; Start with "["
  (local.set $result (local.get $bracket_open))

  ;; Iterate through elements
  (local.set $i (i32.const 0))
  (block $done
    (loop $loop
      (br_if $done (i32.ge_s (local.get $i) (local.get $len)))

      ;; Add comma before element (except first)
      (if (local.get $i)
        (then
          (local.set $result (call $string_concat (local.get $result) (local.get $comma_space)))
        )
      )

      ;; Add element (with repr-style quoting for strings)
      (local.set $elem_str (call $value_to_string_repr (call $list_v2_get (local.get $list) (local.get $i))))
      (local.set $result (call $string_concat (local.get $result) (local.get $elem_str)))

      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $loop)
    )
  )

  ;; Add "]"
  (call $string_concat (local.get $result) (local.get $bracket_close))
)


;; ============================================================================
;; Unified List Operations (handle both PAIR chains and $LIST)
;; ============================================================================

;; list_len_unified: O(1) for $LIST, O(n) for PAIR chain
(func $list_len_unified (param $container (ref null eq)) (result i32)
  ;; Check if it's the new LIST type
  (if (ref.test (ref $LIST) (local.get $container))
    (then
      (return (call $list_v2_len (ref.cast (ref $LIST) (local.get $container))))
    )
  )
  ;; Fall back to PAIR chain
  (call $list_len (local.get $container))
)


;; list_get_unified: O(1) for $LIST and $TUPLE, O(n) for PAIR chain
(func $list_get_unified (param $container (ref null eq)) (param $idx i32) (result (ref null eq))
  ;; Check if it's the new LIST type
  (if (ref.test (ref $LIST) (local.get $container))
    (then
      (return (call $list_v2_get
        (ref.cast (ref $LIST) (local.get $container))
        (local.get $idx)))
    )
  )
  ;; Check if it's a TUPLE type (array-backed tuple)
  (if (ref.test (ref $TUPLE) (local.get $container))
    (then
      (return (call $tuple_get
        (ref.cast (ref $TUPLE) (local.get $container))
        (local.get $idx)))
    )
  )
  ;; Fall back to PAIR chain
  (call $list_get (local.get $container) (local.get $idx))
)


;; list_set_unified: set element at index, handles both $LIST and PAIR chains
(func $list_set_unified (param $container (ref null eq)) (param $idx i32) (param $val (ref null eq))
  ;; Check if it's the new LIST type
  (if (ref.test (ref $LIST) (local.get $container))
    (then
      (call $list_v2_set
        (ref.cast (ref $LIST) (local.get $container))
        (local.get $idx)
        (local.get $val))
      (return)
    )
  )
  ;; Fall back to PAIR chain - needs boxed index
  (call $list_set (local.get $container) (ref.i31 (local.get $idx)) (local.get $val))
)


;; lists_equal: deep comparison of two lists (PAIR chains)
(func $lists_equal (param $a (ref null eq)) (param $b (ref null eq)) (result i32)
  (local $cur_a (ref null eq))
  (local $cur_b (ref null eq))
  (local.set $cur_a (local.get $a))
  (local.set $cur_b (local.get $b))
  (block $done
    (loop $loop
      ;; Both null/empty - equal
      (if (i32.and
            (i32.or (ref.is_null (local.get $cur_a)) (ref.test (ref $EMPTY_LIST) (local.get $cur_a)))
            (i32.or (ref.is_null (local.get $cur_b)) (ref.test (ref $EMPTY_LIST) (local.get $cur_b)))
          )
        (then (return (i32.const 1)))
      )
      ;; One null/empty, one not - not equal
      (if (i32.or
            (i32.or (ref.is_null (local.get $cur_a)) (ref.test (ref $EMPTY_LIST) (local.get $cur_a)))
            (i32.or (ref.is_null (local.get $cur_b)) (ref.test (ref $EMPTY_LIST) (local.get $cur_b)))
          )
        (then (return (i32.const 0)))
      )
      ;; Both are PAIR - compare car elements recursively
      (if (i32.eqz (call $values_equal
            (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $cur_a)))
            (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $cur_b)))
          ))
        (then (return (i32.const 0)))
      )
      ;; Move to next elements
      (local.set $cur_a (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $cur_a))))
      (local.set $cur_b (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $cur_b))))
      (br $loop)
    )
  )
  (i32.const 1)
)


;; list_contains: check if item is in PAIR chain
(func $list_contains (param $item (ref null eq)) (param $list (ref null eq)) (result i32)
  (local $current (ref null eq))
  (local $i i32)
  (local $len i32)
  (local $list_ref (ref $LIST))
  ;; Handle $LIST (array-backed)
  (if (ref.test (ref $LIST) (local.get $list))
    (then
      (local.set $list_ref (ref.cast (ref $LIST) (local.get $list)))
      (local.set $len (struct.get $LIST $len (local.get $list_ref)))
      (local.set $i (i32.const 0))
      (block $done
        (loop $loop
          (br_if $done (i32.ge_s (local.get $i) (local.get $len)))
          (if (call $values_equal (local.get $item) (call $list_v2_get (local.get $list_ref) (local.get $i)))
            (then (return (i32.const 1)))
          )
          (local.set $i (i32.add (local.get $i) (i32.const 1)))
          (br $loop)
        )
      )
      (return (i32.const 0))
    )
  )
  ;; Handle PAIR chain
  (local.set $current (local.get $list))
  (block $done
    (loop $loop
      (br_if $done (ref.is_null (local.get $current)))
      (if (call $values_equal (local.get $item) (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $current))))
        (then (return (i32.const 1)))
      )
      (local.set $current (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current))))
      (br $loop)
    )
  )
  (i32.const 0)
)


;; list_delete_at: delete element at index from list (PAIR chain)
;; Handles negative indices. Returns the modified list.
(func $list_delete_at (param $list (ref null eq)) (param $idx i32) (result (ref null eq))
  (local $len i32)
  (local $real_idx i32)
  (local $current (ref null eq))
  (local $prev (ref null $PAIR))
  (local $i i32)

  ;; Handle null or empty list
  (if (ref.is_null (local.get $list))
    (then (return (local.get $list)))
  )
  (if (ref.test (ref $EMPTY_LIST) (local.get $list))
    (then (return (local.get $list)))
  )

  ;; Get list length for negative index handling
  (local.set $len (call $list_len (local.get $list)))

  ;; Handle negative indices
  (if (i32.lt_s (local.get $idx) (i32.const 0))
    (then
      (local.set $real_idx (i32.add (local.get $len) (local.get $idx)))
    )
    (else
      (local.set $real_idx (local.get $idx))
    )
  )

  ;; Bounds check
  (if (i32.or
        (i32.lt_s (local.get $real_idx) (i32.const 0))
        (i32.ge_s (local.get $real_idx) (local.get $len)))
    (then (return (local.get $list)))  ;; Out of bounds - return unchanged
  )

  ;; Special case: delete first element
  (if (i32.eqz (local.get $real_idx))
    (then
      (return (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $list))))
    )
  )

  ;; Find the element at index-1 (prev) to unlink element at index
  (local.set $i (i32.const 0))
  (local.set $current (local.get $list))

  (block $done
    (loop $loop
      ;; Stop when we reach index-1
      (if (i32.eq (local.get $i) (i32.sub (local.get $real_idx) (i32.const 1)))
        (then
          ;; current is at index-1, skip the next element
          (local.set $prev (ref.cast (ref $PAIR) (local.get $current)))
          (struct.set $PAIR 1 (local.get $prev)
            (struct.get $PAIR 1
              (ref.cast (ref $PAIR)
                (struct.get $PAIR 1 (local.get $prev)))))
          (br $done)
        )
      )

      ;; Move to next
      (local.set $current (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current))))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))

      (br_if $done (ref.is_null (local.get $current)))
      (br $loop)
    )
  )

  (local.get $list)
)


;; iter_prepare: prepare an iterable for for-loop iteration
;; If iterable is a $DICT wrapper, return keys only
;; If iterable is a $GENERATOR, eagerly consume into list
;; Otherwise return the iterable as-is
(func $iter_prepare (param $iter (ref null eq)) (result (ref null eq))
  ;; Null or empty - return as-is
  (if (ref.is_null (local.get $iter))
    (then (return (local.get $iter)))
  )
  (if (ref.test (ref $EMPTY_LIST) (local.get $iter))
    (then (return (local.get $iter)))
  )
  ;; Check if this is a $LIST (array-backed) - convert to PAIR chain for iteration
  (if (ref.test (ref $LIST) (local.get $iter))
    (then
      (return (call $list_v2_to_pair (ref.cast (ref $LIST) (local.get $iter))))
    )
  )
  ;; Check if this is a $DICT wrapper
  (if (ref.test (ref $DICT) (local.get $iter))
    (then
      ;; This is a dict - convert to keys list
      (return (call $dict_keys (local.get $iter)))
    )
  )
  ;; Check if this is a $TUPLE - convert to PAIR chain
  (if (ref.test (ref $TUPLE) (local.get $iter))
    (then
      (return (call $tuple_to_pair (ref.cast (ref $TUPLE) (local.get $iter))))
    )
  )
  ;; Check if this is a $GENERATOR - eagerly consume into list
  (if (ref.test (ref $GENERATOR) (local.get $iter))
    (then
      (return (call $generator_to_list (local.get $iter)))
    )
  )
  ;; Check if this is a $STRING - convert to list of single-char strings
  (if (ref.test (ref $STRING) (local.get $iter))
    (then
      (return (call $string_to_chars (ref.cast (ref $STRING) (local.get $iter))))
    )
  )
  ;; Not a dict, tuple, generator, string, or $LIST - return as-is (assume PAIR chain)
  (local.get $iter)
)


;; list_repeat: repeat a list n times
(func $list_repeat (param $lst (ref null eq)) (param $n (ref null eq)) (result (ref null eq))
  (local $count i32)
  (local $i i32)
  (local $result (ref null eq))

  ;; Handle null or empty list - return empty list marker
  (if (i32.or (ref.is_null (local.get $lst)) (ref.test (ref $EMPTY_LIST) (local.get $lst)))
    (then (return (struct.new $EMPTY_LIST)))
  )

  (local.set $count (i31.get_s (ref.cast (ref i31) (local.get $n))))
  (if (i32.le_s (local.get $count) (i32.const 0))
    (then (return (struct.new $EMPTY_LIST)))
  )

  ;; Start with a copy of the list
  (local.set $result (call $list_copy (local.get $lst)))
  (local.set $i (i32.const 1))

  ;; Concatenate (count - 1) more copies
  (block $done
    (loop $loop
      (br_if $done (i32.ge_s (local.get $i) (local.get $count)))
      (local.set $result (call $list_concat (local.get $result) (call $list_copy (local.get $lst))))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $loop)
    )
  )
  (local.get $result)
)


;; list_v2_concat: concatenate two $LIST arrays
(func $list_v2_concat (param $a (ref $LIST)) (param $b (ref $LIST)) (result (ref $LIST))
  (local $len_a i32)
  (local $len_b i32)
  (local $total_len i32)
  (local $result (ref null $LIST))
  (local $i i32)
  (local $data_a (ref null $ARRAY_ANY))
  (local $data_b (ref null $ARRAY_ANY))
  (local $data_result (ref null $ARRAY_ANY))

  (local.set $len_a (struct.get $LIST $len (local.get $a)))
  (local.set $len_b (struct.get $LIST $len (local.get $b)))
  (local.set $total_len (i32.add (local.get $len_a) (local.get $len_b)))

  ;; Create new list with combined capacity
  (local.set $result (call $list_v2_new (local.get $total_len)))
  (local.set $data_a (struct.get $LIST $data (local.get $a)))
  (local.set $data_b (struct.get $LIST $data (local.get $b)))
  (local.set $data_result (struct.get $LIST $data (ref.cast (ref $LIST) (local.get $result))))

  ;; Copy elements from first list
  (local.set $i (i32.const 0))
  (block $done_a
    (loop $loop_a
      (br_if $done_a (i32.ge_s (local.get $i) (local.get $len_a)))
      (array.set $ARRAY_ANY (ref.cast (ref $ARRAY_ANY) (local.get $data_result)) (local.get $i)
        (array.get $ARRAY_ANY (ref.cast (ref $ARRAY_ANY) (local.get $data_a)) (local.get $i)))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $loop_a)
    )
  )

  ;; Copy elements from second list
  (local.set $i (i32.const 0))
  (block $done_b
    (loop $loop_b
      (br_if $done_b (i32.ge_s (local.get $i) (local.get $len_b)))
      (array.set $ARRAY_ANY (ref.cast (ref $ARRAY_ANY) (local.get $data_result))
        (i32.add (local.get $len_a) (local.get $i))
        (array.get $ARRAY_ANY (ref.cast (ref $ARRAY_ANY) (local.get $data_b)) (local.get $i)))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $loop_b)
    )
  )

  ;; Set final length
  (struct.set $LIST $len (ref.cast (ref $LIST) (local.get $result)) (local.get $total_len))
  (ref.cast (ref $LIST) (local.get $result))
)


;; list_concat: concatenate two lists (handles both $LIST and PAIR chains)
(func $list_concat (param $a (ref null eq)) (param $b (ref null eq)) (result (ref null eq))
  (local $current (ref null eq))
  (local $result (ref null eq))
  (local $tail (ref null eq))
  (local $list_a (ref null $LIST))
  (local $list_b (ref null $LIST))

  ;; If first list is empty (null or EMPTY_LIST), return second
  (if (i32.or (ref.is_null (local.get $a)) (ref.test (ref $EMPTY_LIST) (local.get $a)))
    (then (return (local.get $b)))
  )
  ;; If second list is empty (null or EMPTY_LIST), return first
  (if (i32.or (ref.is_null (local.get $b)) (ref.test (ref $EMPTY_LIST) (local.get $b)))
    (then (return (local.get $a)))
  )

  ;; Handle $LIST types - convert PAIR to $LIST if needed, then use $list_v2_concat
  (if (i32.or (ref.test (ref $LIST) (local.get $a)) (ref.test (ref $LIST) (local.get $b)))
    (then
      ;; Convert first to $LIST if needed
      (if (ref.test (ref $LIST) (local.get $a))
        (then (local.set $list_a (ref.cast (ref $LIST) (local.get $a))))
        (else (local.set $list_a (call $pair_to_list_v2 (local.get $a))))
      )
      ;; Convert second to $LIST if needed
      (if (ref.test (ref $LIST) (local.get $b))
        (then (local.set $list_b (ref.cast (ref $LIST) (local.get $b))))
        (else (local.set $list_b (call $pair_to_list_v2 (local.get $b))))
      )
      (return (call $list_v2_concat
        (ref.cast (ref $LIST) (local.get $list_a))
        (ref.cast (ref $LIST) (local.get $list_b))))
    )
  )

  ;; PAIR chain fallback - Copy first list
  (local.set $current (local.get $a))
  (block $done1
    (loop $loop1
      (br_if $done1 (ref.is_null (local.get $current)))
      (if (ref.is_null (local.get $result))
        (then
          (local.set $result (struct.new $PAIR
            (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $current)))
            (ref.null eq)))
          (local.set $tail (local.get $result))
        )
        (else
          (struct.set $PAIR 1 (ref.cast (ref $PAIR) (local.get $tail))
            (struct.new $PAIR
              (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $current)))
              (ref.null eq)))
          (local.set $tail (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $tail))))
        )
      )
      (local.set $current (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current))))
      (br $loop1)
    )
  )
  ;; Append second list
  (if (ref.is_null (local.get $tail))
    (then (return (local.get $b)))
  )
  (struct.set $PAIR 1 (ref.cast (ref $PAIR) (local.get $tail)) (local.get $b))
  (local.get $result)
)


;; list_set: set element at index in PAIR chain
(func $list_set (param $list (ref null eq)) (param $key (ref null eq)) (param $val (ref null eq))
  (local $current (ref null eq))
  (local $idx i32)
  (local $i i32)
  (local $len i32)
  ;; Get index as i32
  (local.set $idx (i31.get_s (ref.cast (ref i31) (local.get $key))))

  ;; Handle negative index
  (if (i32.lt_s (local.get $idx) (i32.const 0))
    (then
      (local.set $len (call $list_len (local.get $list)))
      (local.set $idx (i32.add (local.get $len) (local.get $idx)))
      (if (i32.lt_s (local.get $idx) (i32.const 0))
        (then (return))  ;; Out of bounds, do nothing
      )
    )
  )

  (local.set $current (local.get $list))
  (local.set $i (i32.const 0))
  (block $done
    (loop $loop
      (br_if $done (ref.is_null (local.get $current)))
      (if (i32.eq (local.get $i) (local.get $idx))
        (then
          ;; Set the value
          (struct.set $PAIR 0 (ref.cast (ref $PAIR) (local.get $current)) (local.get $val))
          (return)
        )
      )
      (local.set $current (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current))))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $loop)
    )
  )
)


;; list_slice: slice a PAIR chain from lower to upper (exclusive) with step
;; Uses -999999 as sentinel for "use default". Handles negative indices.
(func $list_slice (param $list (ref null eq)) (param $lower i32) (param $upper i32) (param $step i32) (result (ref null eq))
  (local $current (ref null eq))
  (local $i i32)
  (local $result (ref null eq))
  (local $tail (ref null eq))
  (local $len i32)
  (local $step_count i32)
  ;; Get list length
  (local.set $len (call $list_len (local.get $list)))
  ;; Handle negative step (reverse)
  (if (i32.lt_s (local.get $step) (i32.const 0))
    (then
      ;; For negative step, default lower is end-1, default upper is before start
      (if (i32.eq (local.get $lower) (i32.const -999999))
        (then (local.set $lower (i32.sub (local.get $len) (i32.const 1))))
        (else
          ;; Convert negative lower to positive
          (if (i32.lt_s (local.get $lower) (i32.const 0))
            (then (local.set $lower (i32.add (local.get $len) (local.get $lower))))
          )
        )
      )
      (if (i32.eq (local.get $upper) (i32.const -999999))
        (then (local.set $upper (i32.const -1)))  ;; sentinel for "before start"
        (else
          ;; Convert negative upper to positive
          (if (i32.lt_s (local.get $upper) (i32.const 0))
            (then (local.set $upper (i32.add (local.get $len) (local.get $upper))))
          )
        )
      )
      ;; Build reversed list using index-based access
      (local.set $result (ref.null eq))
      (local.set $i (local.get $lower))
      (block $rev_done
        (loop $rev
          (br_if $rev_done (i32.lt_s (local.get $i) (i32.const 0)))
          (if (i32.ne (local.get $upper) (i32.const -1))
            (then (br_if $rev_done (i32.le_s (local.get $i) (local.get $upper))))
          )
          ;; Get element at index i
          (local.set $result (struct.new $PAIR
            (call $list_get_index (local.get $list) (local.get $i))
            (local.get $result)))
          ;; Step backwards
          (local.set $i (i32.add (local.get $i) (local.get $step)))
          (br $rev)
        )
      )
      ;; Reverse the result since we built it backwards
      (local.set $result (call $list_reverse (local.get $result)))
      (return (local.get $result))
    )
  )
  ;; Forward step (positive)
  ;; Handle lower = -999999 sentinel (default to 0) or negative lower
  (if (i32.eq (local.get $lower) (i32.const -999999))
    (then (local.set $lower (i32.const 0)))
    (else
      (if (i32.lt_s (local.get $lower) (i32.const 0))
        (then (local.set $lower (i32.add (local.get $len) (local.get $lower))))
      )
    )
  )
  ;; Handle upper = -999999 sentinel (to end) or negative upper
  (if (i32.eq (local.get $upper) (i32.const -999999))
    (then (local.set $upper (local.get $len)))
    (else
      (if (i32.lt_s (local.get $upper) (i32.const 0))
        (then (local.set $upper (i32.add (local.get $len) (local.get $upper))))
      )
    )
  )
  ;; Skip to lower
  (local.set $current (local.get $list))
  (local.set $i (i32.const 0))
  (block $skip_done
    (loop $skip
      (br_if $skip_done (i32.ge_s (local.get $i) (local.get $lower)))
      (br_if $skip_done (ref.is_null (local.get $current)))
      (local.set $current (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current))))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $skip)
    )
  )
  ;; Build result from lower to upper with step
  (local.set $result (ref.null eq))
  (local.set $tail (ref.null eq))
  (local.set $step_count (i32.const 0))
  (block $build_done
    (loop $build
      (br_if $build_done (i32.ge_s (local.get $i) (local.get $upper)))
      (br_if $build_done (ref.is_null (local.get $current)))
      ;; Only include if step_count == 0
      (if (i32.eq (local.get $step_count) (i32.const 0))
        (then
          (if (ref.is_null (local.get $result))
            (then
              (local.set $result (struct.new $PAIR
                (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $current)))
                (ref.null eq)))
              (local.set $tail (local.get $result))
            )
            (else
              (struct.set $PAIR 1 (ref.cast (ref $PAIR) (local.get $tail))
                (struct.new $PAIR
                  (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $current)))
                  (ref.null eq)))
              (local.set $tail (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $tail))))
            )
          )
        )
      )
      (local.set $current (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current))))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      ;; Update step counter
      (local.set $step_count (i32.add (local.get $step_count) (i32.const 1)))
      (if (i32.ge_s (local.get $step_count) (local.get $step))
        (then (local.set $step_count (i32.const 0)))
      )
      (br $build)
    )
  )
  ;; Return EMPTY_LIST if result is null (empty slice)
  (if (result (ref null eq)) (ref.is_null (local.get $result))
    (then (struct.new $EMPTY_LIST))
    (else (local.get $result))
  )
)


;; list_v2_slice_set: replace elements from lower to upper with new values for $LIST
(func $list_v2_slice_set (param $list (ref $LIST)) (param $lower i32) (param $upper i32) (param $values (ref null eq))
  (local $len i32)
  (local $vals_len i32)
  (local $new_len i32)
  (local $old_data (ref null $ARRAY_ANY))
  (local $new_data (ref null $ARRAY_ANY))
  (local $vals_list (ref null $LIST))
  (local $vals_data (ref null $ARRAY_ANY))
  (local $i i32)
  (local $j i32)

  (local.set $len (struct.get $LIST $len (local.get $list)))
  (local.set $old_data (struct.get $LIST $data (local.get $list)))

  ;; Handle upper = -999999 (to end)
  (if (i32.eq (local.get $upper) (i32.const -999999))
    (then (local.set $upper (local.get $len)))
    (else
      (if (i32.lt_s (local.get $upper) (i32.const 0))
        (then (local.set $upper (i32.add (local.get $len) (local.get $upper))))
      )
    )
  )
  ;; Handle negative lower
  (if (i32.lt_s (local.get $lower) (i32.const 0))
    (then (local.set $lower (i32.add (local.get $len) (local.get $lower))))
  )
  ;; Clamp bounds
  (if (i32.lt_s (local.get $lower) (i32.const 0))
    (then (local.set $lower (i32.const 0)))
  )
  (if (i32.gt_s (local.get $upper) (local.get $len))
    (then (local.set $upper (local.get $len)))
  )

  ;; Get values length - convert to $LIST if needed
  (if (ref.is_null (local.get $values))
    (then (local.set $vals_len (i32.const 0)))
    (else
      (if (ref.test (ref $EMPTY_LIST) (local.get $values))
        (then (local.set $vals_len (i32.const 0)))
        (else
          (if (ref.test (ref $LIST) (local.get $values))
            (then
              (local.set $vals_list (ref.cast (ref $LIST) (local.get $values)))
              (local.set $vals_len (struct.get $LIST $len (local.get $vals_list)))
            )
            (else
              ;; Assume PAIR chain - convert to $LIST
              (local.set $vals_list (call $pair_to_list_v2 (local.get $values)))
              (local.set $vals_len (struct.get $LIST $len (local.get $vals_list)))
            )
          )
        )
      )
    )
  )

  ;; Calculate new length
  (local.set $new_len (i32.add
    (i32.add (local.get $lower) (local.get $vals_len))
    (i32.sub (local.get $len) (local.get $upper))))

  ;; Create new array
  (local.set $new_data (array.new $ARRAY_ANY (ref.null eq) (local.get $new_len)))

  ;; Copy elements before lower
  (local.set $i (i32.const 0))
  (block $before_done
    (loop $before_loop
      (br_if $before_done (i32.ge_s (local.get $i) (local.get $lower)))
      (array.set $ARRAY_ANY (ref.cast (ref $ARRAY_ANY) (local.get $new_data)) (local.get $i)
        (array.get $ARRAY_ANY (ref.cast (ref $ARRAY_ANY) (local.get $old_data)) (local.get $i)))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $before_loop)
    )
  )

  ;; Copy new values
  (if (i32.gt_s (local.get $vals_len) (i32.const 0))
    (then
      (local.set $vals_data (struct.get $LIST $data (ref.cast (ref $LIST) (local.get $vals_list))))
      (local.set $j (i32.const 0))
      (block $vals_done
        (loop $vals_loop
          (br_if $vals_done (i32.ge_s (local.get $j) (local.get $vals_len)))
          (array.set $ARRAY_ANY (ref.cast (ref $ARRAY_ANY) (local.get $new_data))
            (i32.add (local.get $lower) (local.get $j))
            (array.get $ARRAY_ANY (ref.cast (ref $ARRAY_ANY) (local.get $vals_data)) (local.get $j)))
          (local.set $j (i32.add (local.get $j) (i32.const 1)))
          (br $vals_loop)
        )
      )
    )
  )

  ;; Copy elements after upper
  (local.set $i (local.get $upper))
  (block $after_done
    (loop $after_loop
      (br_if $after_done (i32.ge_s (local.get $i) (local.get $len)))
      (array.set $ARRAY_ANY (ref.cast (ref $ARRAY_ANY) (local.get $new_data))
        (i32.add (local.get $lower) (i32.add (local.get $vals_len) (i32.sub (local.get $i) (local.get $upper))))
        (array.get $ARRAY_ANY (ref.cast (ref $ARRAY_ANY) (local.get $old_data)) (local.get $i)))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $after_loop)
    )
  )

  ;; Update the $LIST struct
  (struct.set $LIST $data (local.get $list) (ref.cast (ref $ARRAY_ANY) (local.get $new_data)))
  (struct.set $LIST $len (local.get $list) (local.get $new_len))
  (struct.set $LIST $cap (local.get $list) (local.get $new_len))
)


;; list_slice_set: replace elements from lower to upper with new values
;; a[1:3] = [x, y] replaces elements at indices 1 and 2 with x and y
;; Handles different-sized replacement (e.g., a[2:] = [100] truncates)
(func $list_slice_set (param $list (ref null eq)) (param $lower i32) (param $upper i32) (param $values (ref null eq))
  (local $current (ref null eq))
  (local $before_slice (ref null eq))
  (local $after_slice (ref null eq))
  (local $vals (ref null eq))
  (local $vals_tail (ref null eq))
  (local $i i32)
  (local $len i32)

  ;; Handle $LIST type
  (if (ref.test (ref $LIST) (local.get $list))
    (then
      (call $list_v2_slice_set
        (ref.cast (ref $LIST) (local.get $list))
        (local.get $lower)
        (local.get $upper)
        (local.get $values))
      (return)
    )
  )

  ;; PAIR chain fallback - Get list length
  (local.set $len (call $list_len (local.get $list)))
  ;; Handle upper = -999999 (to end)
  (if (i32.eq (local.get $upper) (i32.const -999999))
    (then (local.set $upper (local.get $len)))
    (else
      (if (i32.lt_s (local.get $upper) (i32.const 0))
        (then (local.set $upper (i32.add (local.get $len) (local.get $upper))))
      )
    )
  )
  ;; Handle negative lower
  (if (i32.lt_s (local.get $lower) (i32.const 0))
    (then (local.set $lower (i32.add (local.get $len) (local.get $lower))))
  )
  ;; Find the PAIR at index lower-1 (before the slice)
  (local.set $current (local.get $list))
  (local.set $before_slice (ref.null eq))
  (local.set $i (i32.const 0))
  (block $find_before
    (loop $loop1
      (br_if $find_before (i32.ge_s (local.get $i) (local.get $lower)))
      (br_if $find_before (ref.is_null (local.get $current)))
      (local.set $before_slice (local.get $current))
      (local.set $current (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current))))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $loop1)
    )
  )
  ;; Find the first element after the slice (at index upper)
  (block $find_after
    (loop $loop2
      (br_if $find_after (i32.ge_s (local.get $i) (local.get $upper)))
      (br_if $find_after (ref.is_null (local.get $current)))
      (local.set $current (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current))))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $loop2)
    )
  )
  (local.set $after_slice (local.get $current))
  ;; Find the tail of the values list
  (local.set $vals (local.get $values))
  (local.set $vals_tail (ref.null eq))
  (block $find_vals_tail
    (loop $loop3
      (br_if $find_vals_tail (ref.is_null (local.get $vals)))
      (local.set $vals_tail (local.get $vals))
      (local.set $vals (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $vals))))
      (br $loop3)
    )
  )
  ;; Connect: before_slice -> values -> after_slice
  ;; If lower == 0, we need to modify the first element differently
  (if (i32.eq (local.get $lower) (i32.const 0))
    (then
      ;; Replace the first element's content and link
      (if (ref.is_null (local.get $values))
        (then
          ;; Empty values, just skip to after_slice (but can't modify head pointer)
          ;; For now, copy after_slice content to head
          (if (ref.is_null (local.get $after_slice))
            (then (nop))  ;; Both empty - leave as is (shouldn't happen)
            (else
              (struct.set $PAIR 0 (ref.cast (ref $PAIR) (local.get $list))
                (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $after_slice))))
              (struct.set $PAIR 1 (ref.cast (ref $PAIR) (local.get $list))
                (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $after_slice))))
            )
          )
        )
        (else
          ;; Copy first value to head and link rest
          (struct.set $PAIR 0 (ref.cast (ref $PAIR) (local.get $list))
            (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $values))))
          (if (ref.is_null (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $values))))
            (then
              ;; Single value, link directly to after_slice
              (struct.set $PAIR 1 (ref.cast (ref $PAIR) (local.get $list)) (local.get $after_slice))
            )
            (else
              ;; Multiple values, link head to rest of values
              (struct.set $PAIR 1 (ref.cast (ref $PAIR) (local.get $list))
                (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $values))))
              ;; Link values tail to after_slice
              (struct.set $PAIR 1 (ref.cast (ref $PAIR) (local.get $vals_tail)) (local.get $after_slice))
            )
          )
        )
      )
    )
    (else
      ;; Normal case: link before_slice to values, values tail to after_slice
      (if (ref.is_null (local.get $values))
        (then
          ;; Empty values, link before_slice directly to after_slice
          (struct.set $PAIR 1 (ref.cast (ref $PAIR) (local.get $before_slice)) (local.get $after_slice))
        )
        (else
          ;; Link before_slice to values
          (struct.set $PAIR 1 (ref.cast (ref $PAIR) (local.get $before_slice)) (local.get $values))
          ;; Link values tail to after_slice
          (struct.set $PAIR 1 (ref.cast (ref $PAIR) (local.get $vals_tail)) (local.get $after_slice))
        )
      )
    )
  )
)


;; $list_slice_delete: delete elements from a list by slice indices
;; Returns the modified list (same reference for mutation)
(func $list_slice_delete (param $list (ref null eq)) (param $lower i32) (param $upper i32) (result (ref null eq))
  (local $current (ref null eq))
  (local $before_slice (ref null eq))
  (local $after_slice (ref null eq))
  (local $i i32)
  (local $len i32)
  (local $list_ref (ref null $LIST))
  (local $data (ref null $ARRAY_ANY))
  (local $new_data (ref null $ARRAY_ANY))
  (local $new_len i32)
  (local $j i32)

  ;; Handle null/empty list
  (if (ref.is_null (local.get $list))
    (then (return (ref.null eq)))
  )
  (if (ref.test (ref $EMPTY_LIST) (local.get $list))
    (then (return (local.get $list)))
  )

  ;; Handle $LIST (array-backed)
  (if (ref.test (ref $LIST) (local.get $list))
    (then
      (local.set $list_ref (ref.cast (ref $LIST) (local.get $list)))
      (local.set $len (struct.get $LIST 1 (ref.cast (ref $LIST) (local.get $list_ref))))
      (local.set $data (struct.get $LIST 0 (ref.cast (ref $LIST) (local.get $list_ref))))

      ;; Handle upper = -999999 (to end)
      (if (i32.eq (local.get $upper) (i32.const -999999))
        (then (local.set $upper (local.get $len)))
        (else
          (if (i32.lt_s (local.get $upper) (i32.const 0))
            (then (local.set $upper (i32.add (local.get $len) (local.get $upper))))
          )
        )
      )

      ;; Handle negative lower
      (if (i32.lt_s (local.get $lower) (i32.const 0))
        (then (local.set $lower (i32.add (local.get $len) (local.get $lower))))
      )

      ;; Clamp bounds
      (if (i32.lt_s (local.get $lower) (i32.const 0))
        (then (local.set $lower (i32.const 0)))
      )
      (if (i32.gt_s (local.get $upper) (local.get $len))
        (then (local.set $upper (local.get $len)))
      )

      ;; Nothing to delete if lower >= upper
      (if (i32.ge_s (local.get $lower) (local.get $upper))
        (then (return (local.get $list)))
      )

      ;; Calculate new length
      (local.set $new_len (i32.sub (local.get $len) (i32.sub (local.get $upper) (local.get $lower))))

      ;; Shift elements in place: copy after_slice to start of slice
      (local.set $i (local.get $lower))
      (local.set $j (local.get $upper))
      (block $shift_done
        (loop $shift_loop
          (br_if $shift_done (i32.ge_s (local.get $j) (local.get $len)))
          (array.set $ARRAY_ANY (ref.cast (ref $ARRAY_ANY) (local.get $data)) (local.get $i)
            (array.get $ARRAY_ANY (ref.cast (ref $ARRAY_ANY) (local.get $data)) (local.get $j)))
          (local.set $i (i32.add (local.get $i) (i32.const 1)))
          (local.set $j (i32.add (local.get $j) (i32.const 1)))
          (br $shift_loop)
        )
      )

      ;; Update length
      (struct.set $LIST 1 (ref.cast (ref $LIST) (local.get $list_ref)) (local.get $new_len))
      (return (local.get $list))
    )
  )

  ;; PAIR chain path
  ;; Get list length
  (local.set $len (call $list_len (local.get $list)))

  ;; Handle upper = -999999 (to end)
  (if (i32.eq (local.get $upper) (i32.const -999999))
    (then (local.set $upper (local.get $len)))
    (else
      (if (i32.lt_s (local.get $upper) (i32.const 0))
        (then (local.set $upper (i32.add (local.get $len) (local.get $upper))))
      )
    )
  )

  ;; Handle negative lower
  (if (i32.lt_s (local.get $lower) (i32.const 0))
    (then (local.set $lower (i32.add (local.get $len) (local.get $lower))))
  )

  ;; Clamp bounds
  (if (i32.lt_s (local.get $lower) (i32.const 0))
    (then (local.set $lower (i32.const 0)))
  )
  (if (i32.gt_s (local.get $upper) (local.get $len))
    (then (local.set $upper (local.get $len)))
  )

  ;; Nothing to delete if lower >= upper
  (if (i32.ge_s (local.get $lower) (local.get $upper))
    (then (return (local.get $list)))
  )

  ;; Find the PAIR at index lower-1 (before the slice)
  (local.set $current (local.get $list))
  (local.set $before_slice (ref.null eq))
  (local.set $i (i32.const 0))
  (block $find_before
    (loop $loop1
      (br_if $find_before (i32.ge_s (local.get $i) (local.get $lower)))
      (br_if $find_before (ref.is_null (local.get $current)))
      (local.set $before_slice (local.get $current))
      (local.set $current (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current))))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $loop1)
    )
  )

  ;; Find the first element after the slice (at index upper)
  (block $find_after
    (loop $loop2
      (br_if $find_after (i32.ge_s (local.get $i) (local.get $upper)))
      (br_if $find_after (ref.is_null (local.get $current)))
      (local.set $current (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current))))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $loop2)
    )
  )
  (local.set $after_slice (local.get $current))

  ;; Connect: before_slice -> after_slice
  (if (i32.eq (local.get $lower) (i32.const 0))
    (then
      ;; Deleting from start - need to modify the head
      (if (ref.is_null (local.get $after_slice))
        (then
          ;; Deleted everything - return empty list marker
          (return (struct.new $EMPTY_LIST))
        )
        (else
          ;; Copy after_slice content to head
          (struct.set $PAIR 0 (ref.cast (ref $PAIR) (local.get $list))
            (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $after_slice))))
          (struct.set $PAIR 1 (ref.cast (ref $PAIR) (local.get $list))
            (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $after_slice))))
        )
      )
    )
    (else
      ;; Normal case: link before_slice directly to after_slice
      (struct.set $PAIR 1 (ref.cast (ref $PAIR) (local.get $before_slice)) (local.get $after_slice))
    )
  )
  (local.get $list)
)


;; list_to_string: convert list to string "[elem, elem, ...]"
(func $list_to_string (param $list (ref null eq)) (result (ref $STRING))
  (local $result (ref $STRING))
  (local $current (ref null eq))
  (local $elem (ref null eq))
  (local $elem_str (ref $STRING))
  (local $first i32)
  (local $offset i32)
  (local $comma_space (ref $STRING))
  (local $bracket_open (ref $STRING))
  (local $bracket_close (ref $STRING))

  ;; Create "[" string
  (local.set $offset (global.get $string_heap))
  (i32.store8 (local.get $offset) (i32.const 91))  ;; [
  (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 1)))
  (local.set $bracket_open (struct.new $STRING (local.get $offset) (i32.const 1)))

  ;; Create "]" string
  (local.set $offset (global.get $string_heap))
  (i32.store8 (local.get $offset) (i32.const 93))  ;; ]
  (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 1)))
  (local.set $bracket_close (struct.new $STRING (local.get $offset) (i32.const 1)))

  ;; Create ", " string
  (local.set $offset (global.get $string_heap))
  (i32.store8 (local.get $offset) (i32.const 44))  ;; ,
  (i32.store8 (i32.add (local.get $offset) (i32.const 1)) (i32.const 32))  ;; space
  (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 2)))
  (local.set $comma_space (struct.new $STRING (local.get $offset) (i32.const 2)))

  ;; Start with "["
  (local.set $result (local.get $bracket_open))
  (local.set $current (local.get $list))
  (local.set $first (i32.const 1))

  (block $done
    (loop $loop
      (br_if $done (ref.is_null (local.get $current)))
      (if (i32.eqz (ref.test (ref $PAIR) (local.get $current)))
        (then (br $done))
      )

      ;; Add ", " before non-first elements
      (if (i32.eqz (local.get $first))
        (then
          (local.set $result (call $string_concat (local.get $result) (local.get $comma_space)))
        )
      )
      (local.set $first (i32.const 0))

      ;; Get element and convert to string
      (local.set $elem (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $current))))
      (local.set $elem_str (call $value_to_string_repr (local.get $elem)))
      (local.set $result (call $string_concat (local.get $result) (local.get $elem_str)))

      ;; Move to next
      (local.set $current (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current))))
      (br $loop)
    )
  )

  ;; Add "]"
  (call $string_concat (local.get $result) (local.get $bracket_close))
)


;; List method: append(item) - add item to end of list (mutates in place)
;; Returns the list (for the compiler to store back in case of initial empty list)
(func $list_append (param $lst (ref null eq)) (param $item (ref null eq)) (result (ref null eq))
  (local $current (ref null eq))
  (local $pair (ref null $PAIR))

  ;; Handle $LIST type - use $list_v2_append
  (if (ref.test (ref $LIST) (local.get $lst))
    (then
      (return (call $list_v2_append
        (ref.cast (ref $LIST) (local.get $lst))
        (local.get $item)))
    )
  )

  ;; Empty list case - create new $LIST with one element
  (if (ref.is_null (local.get $lst))
    (then
      (return (call $list_v2_append
        (call $list_v2_new (i32.const 4))
        (local.get $item)))
    )
  )
  (if (ref.test (ref $EMPTY_LIST) (local.get $lst))
    (then
      (return (call $list_v2_append
        (call $list_v2_new (i32.const 4))
        (local.get $item)))
    )
  )

  ;; PAIR chain fallback - find the last element
  (local.set $current (local.get $lst))
  (block $found_end
    (loop $loop
      (local.set $pair (ref.cast (ref $PAIR) (local.get $current)))
      (br_if $found_end (ref.is_null (struct.get $PAIR 1 (local.get $pair))))
      (local.set $current (struct.get $PAIR 1 (local.get $pair)))
      (br $loop)
    )
  )

  ;; Append new PAIR at the end
  (struct.set $PAIR 1 (local.get $pair) (struct.new $PAIR (local.get $item) (ref.null eq)))
  (local.get $lst)  ;; return the list
)


;; List method: pop() - remove and return last item
(func $list_pop (param $lst (ref null eq)) (result (ref null eq))
  (local $current (ref null eq))
  (local $prev (ref null eq))
  (local $pair (ref null $PAIR))
  (local $result (ref null eq))

  (if (ref.is_null (local.get $lst))
    (then (return (ref.null eq)))
  )
  (if (ref.test (ref $EMPTY_LIST) (local.get $lst))
    (then (return (ref.null eq)))
  )

  ;; Handle $LIST type - use $list_v2_pop
  (if (ref.test (ref $LIST) (local.get $lst))
    (then (return (call $list_v2_pop (ref.cast (ref $LIST) (local.get $lst)))))
  )

  ;; PAIR chain fallback
  ;; Single element case
  (local.set $pair (ref.cast (ref $PAIR) (local.get $lst)))
  (if (ref.is_null (struct.get $PAIR 1 (local.get $pair)))
    (then
      (return (struct.get $PAIR 0 (local.get $pair)))
    )
  )

  ;; Find second-to-last element
  (local.set $prev (local.get $lst))
  (local.set $current (struct.get $PAIR 1 (local.get $pair)))
  (block $found
    (loop $loop
      (local.set $pair (ref.cast (ref $PAIR) (local.get $current)))
      (br_if $found (ref.is_null (struct.get $PAIR 1 (local.get $pair))))
      (local.set $prev (local.get $current))
      (local.set $current (struct.get $PAIR 1 (local.get $pair)))
      (br $loop)
    )
  )

  ;; Get the last element's value
  (local.set $result (struct.get $PAIR 0 (local.get $pair)))

  ;; Remove last element by setting prev's cdr to null
  (struct.set $PAIR 1 (ref.cast (ref $PAIR) (local.get $prev)) (ref.null eq))

  (local.get $result)
)


;; List method: pop(index) - remove and return item at index
(func $list_pop_at (param $lst (ref null eq)) (param $idx (ref null eq)) (result (ref null eq))
  (local $current (ref null eq))
  (local $prev (ref null eq))
  (local $pair (ref null $PAIR))
  (local $result (ref null eq))
  (local $i i32)
  (local $index i32)
  (local $list_v2 (ref null $LIST))
  (local $len i32)
  (local $data (ref null $ARRAY_ANY))

  (if (ref.is_null (local.get $lst))
    (then (return (ref.null eq)))
  )
  (if (ref.test (ref $EMPTY_LIST) (local.get $lst))
    (then (return (ref.null eq)))
  )

  ;; Get index value
  (local.set $index (i31.get_s (ref.cast i31ref (local.get $idx))))

  ;; Handle $LIST type
  (if (ref.test (ref $LIST) (local.get $lst))
    (then
      (local.set $list_v2 (ref.cast (ref $LIST) (local.get $lst)))
      (local.set $len (struct.get $LIST $len (ref.cast (ref $LIST) (local.get $list_v2))))
      (local.set $data (struct.get $LIST $data (ref.cast (ref $LIST) (local.get $list_v2))))

      ;; Handle negative index
      (if (i32.lt_s (local.get $index) (i32.const 0))
        (then (local.set $index (i32.add (local.get $index) (local.get $len))))
      )

      ;; Bounds check
      (if (i32.or
            (i32.lt_s (local.get $index) (i32.const 0))
            (i32.ge_s (local.get $index) (local.get $len)))
        (then (return (ref.null eq)))  ;; Index out of bounds
      )

      ;; Get the value to return
      (local.set $result (array.get $ARRAY_ANY (ref.cast (ref $ARRAY_ANY) (local.get $data)) (local.get $index)))

      ;; Shift elements after index
      (local.set $i (local.get $index))
      (block $shift_done
        (loop $shift_loop
          (br_if $shift_done (i32.ge_s (local.get $i) (i32.sub (local.get $len) (i32.const 1))))
          (array.set $ARRAY_ANY (ref.cast (ref $ARRAY_ANY) (local.get $data)) (local.get $i)
            (array.get $ARRAY_ANY (ref.cast (ref $ARRAY_ANY) (local.get $data)) (i32.add (local.get $i) (i32.const 1))))
          (local.set $i (i32.add (local.get $i) (i32.const 1)))
          (br $shift_loop)
        )
      )

      ;; Clear last element and decrement length
      (array.set $ARRAY_ANY (ref.cast (ref $ARRAY_ANY) (local.get $data))
        (i32.sub (local.get $len) (i32.const 1))
        (ref.null eq))
      (struct.set $LIST $len (ref.cast (ref $LIST) (local.get $list_v2)) (i32.sub (local.get $len) (i32.const 1)))
      (return (local.get $result))
    )
  )

  ;; PAIR chain fallback
  ;; Handle negative index
  (if (i32.lt_s (local.get $index) (i32.const 0))
    (then
      (local.set $index (i32.add (local.get $index) (call $list_len (local.get $lst))))
    )
  )

  ;; Pop at index 0 - special case (remove first element)
  (if (i32.eq (local.get $index) (i32.const 0))
    (then
      (local.set $pair (ref.cast (ref $PAIR) (local.get $lst)))
      (return (struct.get $PAIR 0 (local.get $pair)))
    )
  )

  ;; Find element at index-1 (to unlink element at index)
  (local.set $prev (local.get $lst))
  (local.set $i (i32.const 0))
  (block $done
    (loop $loop
      (br_if $done (i32.ge_s (local.get $i) (i32.sub (local.get $index) (i32.const 1))))
      (local.set $pair (ref.cast (ref $PAIR) (local.get $prev)))
      (local.set $prev (struct.get $PAIR 1 (local.get $pair)))
      (if (ref.is_null (local.get $prev))
        (then (return (ref.null eq)))  ;; Index out of bounds
      )
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $loop)
    )
  )

  ;; Now $prev points to element at index-1
  (local.set $pair (ref.cast (ref $PAIR) (local.get $prev)))
  (local.set $current (struct.get $PAIR 1 (local.get $pair)))

  (if (ref.is_null (local.get $current))
    (then (return (ref.null eq)))  ;; Index out of bounds
  )

  ;; Get the result value
  (local.set $result (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $current))))

  ;; Unlink: set prev's cdr to current's cdr
  (struct.set $PAIR 1 (local.get $pair)
    (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current))))

  (local.get $result)
)


;; List method: pop_at_rest(index) - return list after removing item at index
;; This is used by the compiler to update the list variable after pop(index)
(func $list_pop_at_rest (param $lst (ref null eq)) (param $idx (ref null eq)) (result (ref null eq))
  (local $current (ref null eq))
  (local $prev (ref null eq))
  (local $pair (ref null $PAIR))
  (local $i i32)
  (local $index i32)

  (if (ref.is_null (local.get $lst))
    (then (return (ref.null eq)))
  )
  (if (ref.test (ref $EMPTY_LIST) (local.get $lst))
    (then (return (local.get $lst)))
  )

  ;; Handle $LIST type - the list is mutated in-place by $list_pop_at, just return it
  (if (ref.test (ref $LIST) (local.get $lst))
    (then (return (local.get $lst)))
  )

  ;; PAIR chain fallback
  ;; Get index value
  (local.set $index (i31.get_s (ref.cast i31ref (local.get $idx))))

  ;; Handle negative index
  (if (i32.lt_s (local.get $index) (i32.const 0))
    (then
      (local.set $index (i32.add (local.get $index) (call $list_len (local.get $lst))))
    )
  )

  ;; Pop at index 0 - return cdr (rest of list)
  (if (i32.eq (local.get $index) (i32.const 0))
    (then
      (local.set $pair (ref.cast (ref $PAIR) (local.get $lst)))
      (return (struct.get $PAIR 1 (local.get $pair)))
    )
  )

  ;; For index > 0, the list is already mutated in-place by $list_pop_at
  ;; Just return the original list
  (local.get $lst)
)


;; List method: copy() - shallow copy of list
(func $list_copy (param $lst (ref null eq)) (result (ref null eq))
  (local $current (ref null eq))
  (local $result (ref null eq))
  (local $tail (ref null eq))
  (local $new_pair (ref null $PAIR))

  ;; Handle $LIST type - use $list_v2_copy
  (if (ref.test (ref $LIST) (local.get $lst))
    (then (return (call $list_v2_copy (ref.cast (ref $LIST) (local.get $lst)))))
  )

  ;; Handle null or empty list
  (if (i32.or (ref.is_null (local.get $lst)) (ref.test (ref $EMPTY_LIST) (local.get $lst)))
    (then (return (struct.new $EMPTY_LIST)))
  )

  (local.set $current (local.get $lst))
  (block $done
    (loop $loop
      (br_if $done (ref.is_null (local.get $current)))

      ;; Create new pair
      (local.set $new_pair
        (struct.new $PAIR
          (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $current)))
          (ref.null eq)))

      ;; Link to result
      (if (ref.is_null (local.get $result))
        (then
          (local.set $result (local.get $new_pair))
          (local.set $tail (local.get $new_pair))
        )
        (else
          (struct.set $PAIR 1 (ref.cast (ref $PAIR) (local.get $tail)) (local.get $new_pair))
          (local.set $tail (local.get $new_pair))
        )
      )

      (local.set $current (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current))))
      (br $loop)
    )
  )
  (local.get $result)
)


;; List method: clear() - remove all items
(func $list_clear (param $lst (ref null eq)) (result (ref null eq))
  ;; We can't truly clear a PAIR chain, but we can return empty list
  ;; The original list is left as garbage for GC
  (struct.new $EMPTY_LIST)  ;; return empty list marker
)


;; List method: index(item) - find index of first occurrence
(func $list_index (param $lst (ref null eq)) (param $item (ref null eq)) (result (ref null eq))
  (local $current (ref null eq))
  (local $idx i32)
  (local $elem (ref null eq))
  (local $list_v2 (ref null $LIST))
  (local $len i32)
  (local $data (ref null $ARRAY_ANY))

  (if (ref.is_null (local.get $lst))
    (then (return (ref.i31 (i32.const -1))))
  )
  (if (ref.test (ref $EMPTY_LIST) (local.get $lst))
    (then (return (ref.i31 (i32.const -1))))
  )

  ;; Handle $LIST type
  (if (ref.test (ref $LIST) (local.get $lst))
    (then
      (local.set $list_v2 (ref.cast (ref $LIST) (local.get $lst)))
      (local.set $len (struct.get $LIST $len (ref.cast (ref $LIST) (local.get $list_v2))))
      (local.set $data (struct.get $LIST $data (ref.cast (ref $LIST) (local.get $list_v2))))
      (local.set $idx (i32.const 0))
      (block $found_v2
        (block $not_found_v2
          (loop $loop_v2
            (br_if $not_found_v2 (i32.ge_s (local.get $idx) (local.get $len)))
            (local.set $elem (array.get $ARRAY_ANY (ref.cast (ref $ARRAY_ANY) (local.get $data)) (local.get $idx)))
            (if (call $value_equals (local.get $elem) (local.get $item))
              (then (br $found_v2))
            )
            (local.set $idx (i32.add (local.get $idx) (i32.const 1)))
            (br $loop_v2)
          )
        )
        (return (ref.i31 (i32.const -1)))
      )
      (return (ref.i31 (local.get $idx)))
    )
  )

  ;; PAIR chain fallback
  (local.set $current (local.get $lst))
  (local.set $idx (i32.const 0))
  (block $found
    (block $not_found
      (loop $loop
        (br_if $not_found (ref.is_null (local.get $current)))
        (local.set $elem (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $current))))

        ;; Compare using value_equals
        (if (call $value_equals (local.get $elem) (local.get $item))
          (then (br $found))
        )

        (local.set $current (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current))))
        (local.set $idx (i32.add (local.get $idx) (i32.const 1)))
        (br $loop)
      )
    )
    (return (ref.i31 (i32.const -1)))
  )
  (ref.i31 (local.get $idx))
)


;; List method: index(item, start) - find index of first occurrence starting from start
(func $list_index_from (param $lst (ref null eq)) (param $item (ref null eq)) (param $start (ref null eq)) (result (ref null eq))
  (local $current (ref null eq))
  (local $idx i32)
  (local $start_idx i32)
  (local $elem (ref null eq))
  (local $list_v2 (ref null $LIST))
  (local $len i32)
  (local $data (ref null $ARRAY_ANY))

  (if (ref.is_null (local.get $lst))
    (then (return (ref.i31 (i32.const -1))))
  )
  (if (ref.test (ref $EMPTY_LIST) (local.get $lst))
    (then (return (ref.i31 (i32.const -1))))
  )

  (local.set $start_idx (i31.get_s (ref.cast i31ref (local.get $start))))

  ;; Handle $LIST type
  (if (ref.test (ref $LIST) (local.get $lst))
    (then
      (local.set $list_v2 (ref.cast (ref $LIST) (local.get $lst)))
      (local.set $len (struct.get $LIST $len (ref.cast (ref $LIST) (local.get $list_v2))))
      (local.set $data (struct.get $LIST $data (ref.cast (ref $LIST) (local.get $list_v2))))
      (local.set $idx (local.get $start_idx))
      (block $found_v2
        (block $not_found_v2
          (loop $loop_v2
            (br_if $not_found_v2 (i32.ge_s (local.get $idx) (local.get $len)))
            (local.set $elem (array.get $ARRAY_ANY (ref.cast (ref $ARRAY_ANY) (local.get $data)) (local.get $idx)))
            (if (call $value_equals (local.get $elem) (local.get $item))
              (then (br $found_v2))
            )
            (local.set $idx (i32.add (local.get $idx) (i32.const 1)))
            (br $loop_v2)
          )
        )
        (return (ref.i31 (i32.const -1)))
      )
      (return (ref.i31 (local.get $idx)))
    )
  )

  ;; PAIR chain fallback
  (local.set $current (local.get $lst))
  (local.set $idx (i32.const 0))

  ;; Skip to start index
  (block $done_skip
    (loop $skip
      (br_if $done_skip (i32.ge_s (local.get $idx) (local.get $start_idx)))
      (br_if $done_skip (ref.is_null (local.get $current)))
      (local.set $current (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current))))
      (local.set $idx (i32.add (local.get $idx) (i32.const 1)))
      (br $skip)
    )
  )

  ;; Search from current position
  (block $found
    (block $not_found
      (loop $loop
        (br_if $not_found (ref.is_null (local.get $current)))
        (local.set $elem (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $current))))

        ;; Compare using value_equals
        (if (call $value_equals (local.get $elem) (local.get $item))
          (then (br $found))
        )

        (local.set $current (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current))))
        (local.set $idx (i32.add (local.get $idx) (i32.const 1)))
        (br $loop)
      )
    )
    (return (ref.i31 (i32.const -1)))
  )
  (ref.i31 (local.get $idx))
)


;; List method: count(item) - count occurrences
(func $list_count (param $lst (ref null eq)) (param $item (ref null eq)) (result (ref null eq))
  (local $current (ref null eq))
  (local $count i32)
  (local $elem (ref null eq))
  (local $list_v2 (ref null $LIST))
  (local $len i32)
  (local $data (ref null $ARRAY_ANY))
  (local $i i32)

  (if (ref.is_null (local.get $lst))
    (then (return (ref.i31 (i32.const 0))))
  )
  (if (ref.test (ref $EMPTY_LIST) (local.get $lst))
    (then (return (ref.i31 (i32.const 0))))
  )

  ;; Handle $LIST type
  (if (ref.test (ref $LIST) (local.get $lst))
    (then
      (local.set $list_v2 (ref.cast (ref $LIST) (local.get $lst)))
      (local.set $len (struct.get $LIST $len (ref.cast (ref $LIST) (local.get $list_v2))))
      (local.set $data (struct.get $LIST $data (ref.cast (ref $LIST) (local.get $list_v2))))
      (local.set $count (i32.const 0))
      (local.set $i (i32.const 0))
      (block $done_v2
        (loop $loop_v2
          (br_if $done_v2 (i32.ge_s (local.get $i) (local.get $len)))
          (local.set $elem (array.get $ARRAY_ANY (ref.cast (ref $ARRAY_ANY) (local.get $data)) (local.get $i)))
          (if (call $value_equals (local.get $elem) (local.get $item))
            (then (local.set $count (i32.add (local.get $count) (i32.const 1))))
          )
          (local.set $i (i32.add (local.get $i) (i32.const 1)))
          (br $loop_v2)
        )
      )
      (return (ref.i31 (local.get $count)))
    )
  )

  ;; PAIR chain fallback
  (local.set $current (local.get $lst))
  (local.set $count (i32.const 0))
  (block $done
    (loop $loop
      (br_if $done (ref.is_null (local.get $current)))
      (local.set $elem (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $current))))

      ;; Compare using value_equals
      (if (call $value_equals (local.get $elem) (local.get $item))
        (then (local.set $count (i32.add (local.get $count) (i32.const 1))))
      )

      (local.set $current (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current))))
      (br $loop)
    )
  )
  (ref.i31 (local.get $count))
)


;; List method: extend(other) - add all items from other list
;; Returns the list (for the compiler to store back)
(func $list_extend (param $lst (ref null eq)) (param $other (ref null eq)) (result (ref null eq))
  (local $current (ref null eq))
  (local $pair (ref null $PAIR))
  (local $other_current (ref null eq))
  (local $list_lst (ref null $LIST))
  (local $list_other (ref null $LIST))
  (local $i i32)
  (local $other_len i32)
  (local $other_data (ref null $ARRAY_ANY))

  ;; Empty list to extend - return copy of other
  (if (ref.is_null (local.get $lst))
    (then (return (call $list_copy (local.get $other))))
  )
  (if (ref.test (ref $EMPTY_LIST) (local.get $lst))
    (then (return (call $list_copy (local.get $other))))
  )

  ;; Empty other - return original
  (if (ref.is_null (local.get $other))
    (then (return (local.get $lst)))
  )
  (if (ref.test (ref $EMPTY_LIST) (local.get $other))
    (then (return (local.get $lst)))
  )

  ;; Handle $LIST type - use $list_v2_append for each element
  (if (ref.test (ref $LIST) (local.get $lst))
    (then
      (local.set $list_lst (ref.cast (ref $LIST) (local.get $lst)))
      ;; Convert other to $LIST if needed
      (if (ref.test (ref $LIST) (local.get $other))
        (then (local.set $list_other (ref.cast (ref $LIST) (local.get $other))))
        (else (local.set $list_other (call $pair_to_list_v2 (local.get $other))))
      )
      ;; Append each element from other
      (local.set $other_len (struct.get $LIST $len (ref.cast (ref $LIST) (local.get $list_other))))
      (local.set $other_data (struct.get $LIST $data (ref.cast (ref $LIST) (local.get $list_other))))
      (local.set $i (i32.const 0))
      (block $done
        (loop $loop_extend
          (br_if $done (i32.ge_s (local.get $i) (local.get $other_len)))
          (local.set $list_lst (call $list_v2_append
            (ref.cast (ref $LIST) (local.get $list_lst))
            (array.get $ARRAY_ANY (ref.cast (ref $ARRAY_ANY) (local.get $other_data)) (local.get $i))))
          (local.set $i (i32.add (local.get $i) (i32.const 1)))
          (br $loop_extend)
        )
      )
      (return (local.get $list_lst))
    )
  )

  ;; PAIR chain fallback - Find the last element of lst
  (local.set $current (local.get $lst))
  (block $found_end
    (loop $loop
      (local.set $pair (ref.cast (ref $PAIR) (local.get $current)))
      (br_if $found_end (ref.is_null (struct.get $PAIR 1 (local.get $pair))))
      (local.set $current (struct.get $PAIR 1 (local.get $pair)))
      (br $loop)
    )
  )

  ;; Append copy of other to the end
  (struct.set $PAIR 1 (local.get $pair) (call $list_copy (local.get $other)))
  (local.get $lst)  ;; return the list
)


;; List method: insert(index, item) - insert item at index
(func $list_insert (param $lst (ref null eq)) (param $idx (ref null eq)) (param $item (ref null eq)) (result (ref null eq))
  (local $index i32)
  (local $current (ref null eq))
  (local $prev (ref null eq))
  (local $i i32)
  (local $new_pair (ref null $PAIR))
  (local $list_v2 (ref null $LIST))
  (local $len i32)
  (local $old_data (ref null $ARRAY_ANY))
  (local $new_data (ref null $ARRAY_ANY))

  ;; Get index value
  (if (ref.is_null (local.get $idx))
    (then (local.set $index (i32.const 0)))
    (else (local.set $index (i31.get_s (ref.cast (ref i31) (local.get $idx)))))
  )

  ;; Handle $LIST type
  (if (ref.test (ref $LIST) (local.get $lst))
    (then
      (local.set $list_v2 (ref.cast (ref $LIST) (local.get $lst)))
      (local.set $len (struct.get $LIST $len (ref.cast (ref $LIST) (local.get $list_v2))))
      (local.set $old_data (struct.get $LIST $data (ref.cast (ref $LIST) (local.get $list_v2))))

      ;; Handle negative index
      (if (i32.lt_s (local.get $index) (i32.const 0))
        (then (local.set $index (i32.add (local.get $len) (local.get $index))))
      )
      ;; Clamp to valid range
      (if (i32.lt_s (local.get $index) (i32.const 0))
        (then (local.set $index (i32.const 0)))
      )
      (if (i32.gt_s (local.get $index) (local.get $len))
        (then (local.set $index (local.get $len)))
      )

      ;; Create new array with space for one more element
      (local.set $new_data (array.new $ARRAY_ANY (ref.null eq) (i32.add (local.get $len) (i32.const 1))))

      ;; Copy elements before index
      (local.set $i (i32.const 0))
      (block $before_done
        (loop $before_loop
          (br_if $before_done (i32.ge_s (local.get $i) (local.get $index)))
          (array.set $ARRAY_ANY (ref.cast (ref $ARRAY_ANY) (local.get $new_data)) (local.get $i)
            (array.get $ARRAY_ANY (ref.cast (ref $ARRAY_ANY) (local.get $old_data)) (local.get $i)))
          (local.set $i (i32.add (local.get $i) (i32.const 1)))
          (br $before_loop)
        )
      )

      ;; Insert new element
      (array.set $ARRAY_ANY (ref.cast (ref $ARRAY_ANY) (local.get $new_data)) (local.get $index) (local.get $item))

      ;; Copy elements after index
      (local.set $i (local.get $index))
      (block $after_done
        (loop $after_loop
          (br_if $after_done (i32.ge_s (local.get $i) (local.get $len)))
          (array.set $ARRAY_ANY (ref.cast (ref $ARRAY_ANY) (local.get $new_data))
            (i32.add (local.get $i) (i32.const 1))
            (array.get $ARRAY_ANY (ref.cast (ref $ARRAY_ANY) (local.get $old_data)) (local.get $i)))
          (local.set $i (i32.add (local.get $i) (i32.const 1)))
          (br $after_loop)
        )
      )

      ;; Update the $LIST struct
      (struct.set $LIST $data (ref.cast (ref $LIST) (local.get $list_v2)) (ref.cast (ref $ARRAY_ANY) (local.get $new_data)))
      (struct.set $LIST $len (ref.cast (ref $LIST) (local.get $list_v2)) (i32.add (local.get $len) (i32.const 1)))
      (struct.set $LIST $cap (ref.cast (ref $LIST) (local.get $list_v2)) (i32.add (local.get $len) (i32.const 1)))
      (return (local.get $list_v2))
    )
  )

  ;; Handle EMPTY_LIST
  (if (ref.test (ref $EMPTY_LIST) (local.get $lst))
    (then
      (return (call $list_v2_append (call $list_v2_new (i32.const 4)) (local.get $item)))
    )
  )

  ;; PAIR chain fallback
  ;; Insert at beginning
  (if (i32.le_s (local.get $index) (i32.const 0))
    (then
      (return (struct.new $PAIR (local.get $item) (local.get $lst)))
    )
  )

  ;; Empty list
  (if (ref.is_null (local.get $lst))
    (then
      (return (struct.new $PAIR (local.get $item) (ref.null eq)))
    )
  )

  ;; Find position
  (local.set $current (local.get $lst))
  (local.set $prev (ref.null eq))
  (local.set $i (i32.const 0))
  (block $found
    (loop $loop
      (br_if $found (i32.ge_s (local.get $i) (local.get $index)))
      (br_if $found (ref.is_null (local.get $current)))
      (local.set $prev (local.get $current))
      (local.set $current (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current))))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $loop)
    )
  )

  ;; Insert after prev
  (local.set $new_pair (struct.new $PAIR (local.get $item) (local.get $current)))
  (if (ref.is_null (local.get $prev))
    (then (return (local.get $new_pair)))
    (else
      (struct.set $PAIR 1 (ref.cast (ref $PAIR) (local.get $prev)) (local.get $new_pair))
      (return (local.get $lst))  ;; return the list
    )
  )
  (local.get $lst)  ;; fallback return
)


;; List method: remove(item) - remove first occurrence
;; Returns the list (for the compiler to store back)
(func $list_remove (param $lst (ref null eq)) (param $item (ref null eq)) (result (ref null eq))
  (local $current (ref null eq))
  (local $prev (ref null eq))
  (local $elem (ref null eq))
  (local $list_v2 (ref null $LIST))
  (local $len i32)
  (local $data (ref null $ARRAY_ANY))
  (local $i i32)
  (local $found_idx i32)

  (if (ref.is_null (local.get $lst))
    (then (return (ref.null eq)))
  )
  (if (ref.test (ref $EMPTY_LIST) (local.get $lst))
    (then (return (local.get $lst)))
  )

  ;; Handle $LIST type
  (if (ref.test (ref $LIST) (local.get $lst))
    (then
      (local.set $list_v2 (ref.cast (ref $LIST) (local.get $lst)))
      (local.set $len (struct.get $LIST $len (ref.cast (ref $LIST) (local.get $list_v2))))
      (local.set $data (struct.get $LIST $data (ref.cast (ref $LIST) (local.get $list_v2))))
      (local.set $found_idx (i32.const -1))

      ;; Find the item
      (local.set $i (i32.const 0))
      (block $found_block
        (loop $search_loop
          (br_if $found_block (i32.ge_s (local.get $i) (local.get $len)))
          (if (call $value_equals
                (array.get $ARRAY_ANY (ref.cast (ref $ARRAY_ANY) (local.get $data)) (local.get $i))
                (local.get $item))
            (then
              (local.set $found_idx (local.get $i))
              (br $found_block)
            )
          )
          (local.set $i (i32.add (local.get $i) (i32.const 1)))
          (br $search_loop)
        )
      )

      ;; If not found, return original list
      (if (i32.lt_s (local.get $found_idx) (i32.const 0))
        (then (return (local.get $list_v2)))
      )

      ;; Shift elements after found_idx
      (local.set $i (local.get $found_idx))
      (block $shift_done
        (loop $shift_loop
          (br_if $shift_done (i32.ge_s (local.get $i) (i32.sub (local.get $len) (i32.const 1))))
          (array.set $ARRAY_ANY (ref.cast (ref $ARRAY_ANY) (local.get $data)) (local.get $i)
            (array.get $ARRAY_ANY (ref.cast (ref $ARRAY_ANY) (local.get $data)) (i32.add (local.get $i) (i32.const 1))))
          (local.set $i (i32.add (local.get $i) (i32.const 1)))
          (br $shift_loop)
        )
      )

      ;; Clear last element and decrement length
      (array.set $ARRAY_ANY (ref.cast (ref $ARRAY_ANY) (local.get $data))
        (i32.sub (local.get $len) (i32.const 1))
        (ref.null eq))
      (struct.set $LIST $len (ref.cast (ref $LIST) (local.get $list_v2)) (i32.sub (local.get $len) (i32.const 1)))
      (return (local.get $list_v2))
    )
  )

  ;; PAIR chain fallback
  (local.set $current (local.get $lst))
  (local.set $prev (ref.null eq))
  (block $found
    (block $not_found
      (loop $loop
        (br_if $not_found (ref.is_null (local.get $current)))
        (local.set $elem (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $current))))

        (if (call $value_equals (local.get $elem) (local.get $item))
          (then (br $found))
        )

        (local.set $prev (local.get $current))
        (local.set $current (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current))))
        (br $loop)
      )
    )
    (return (local.get $lst))  ;; Not found - return original list
  )

  ;; Remove current by linking prev to current's next
  (if (ref.is_null (local.get $prev))
    (then
      ;; Removing first element - return rest of list
      (return (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current))))
    )
    (else
      (struct.set $PAIR 1
        (ref.cast (ref $PAIR) (local.get $prev))
        (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current))))
    )
  )
  (local.get $lst)  ;; return the list
)


;; List method: reverse() in place - reverses list by swapping values
(func $list_reverse_inplace (param $lst (ref null eq)) (result (ref null eq))
  (local $len i32)
  (local $i i32)
  (local $current (ref null eq))
  (local $pair (ref null $PAIR))
  (local $front (ref null eq))
  (local $back (ref null eq))
  (local $front_pair (ref null $PAIR))
  (local $back_pair (ref null $PAIR))
  (local $j i32)
  (local $tmp (ref null eq))
  (local $list_v2 (ref null $LIST))
  (local $data (ref null $ARRAY_ANY))

  (if (ref.is_null (local.get $lst))
    (then (return (ref.null eq)))
  )
  (if (ref.test (ref $EMPTY_LIST) (local.get $lst))
    (then (return (local.get $lst)))
  )

  ;; Handle $LIST type
  (if (ref.test (ref $LIST) (local.get $lst))
    (then
      (local.set $list_v2 (ref.cast (ref $LIST) (local.get $lst)))
      (local.set $len (struct.get $LIST $len (ref.cast (ref $LIST) (local.get $list_v2))))
      (local.set $data (struct.get $LIST $data (ref.cast (ref $LIST) (local.get $list_v2))))

      ;; Swap elements from front and back
      (local.set $i (i32.const 0))
      (block $done_v2
        (loop $loop_v2
          (br_if $done_v2 (i32.ge_s (local.get $i) (i32.div_s (local.get $len) (i32.const 2))))
          ;; Swap elements at i and (len - 1 - i)
          (local.set $tmp (array.get $ARRAY_ANY (ref.cast (ref $ARRAY_ANY) (local.get $data)) (local.get $i)))
          (array.set $ARRAY_ANY (ref.cast (ref $ARRAY_ANY) (local.get $data)) (local.get $i)
            (array.get $ARRAY_ANY (ref.cast (ref $ARRAY_ANY) (local.get $data))
              (i32.sub (i32.sub (local.get $len) (i32.const 1)) (local.get $i))))
          (array.set $ARRAY_ANY (ref.cast (ref $ARRAY_ANY) (local.get $data))
            (i32.sub (i32.sub (local.get $len) (i32.const 1)) (local.get $i))
            (local.get $tmp))
          (local.set $i (i32.add (local.get $i) (i32.const 1)))
          (br $loop_v2)
        )
      )
      (return (local.get $list_v2))
    )
  )

  ;; PAIR chain fallback - Get list length
  (local.set $len (call $list_len (local.get $lst)))

  ;; Swap elements from front and back
  (local.set $i (i32.const 0))
  (block $done
    (loop $loop
      ;; Stop when i >= len/2
      (br_if $done (i32.ge_s (local.get $i) (i32.div_s (local.get $len) (i32.const 2))))

      ;; Find element at index i (front)
      (local.set $front (local.get $lst))
      (local.set $j (i32.const 0))
      (block $found_front
        (loop $find_front
          (br_if $found_front (i32.ge_s (local.get $j) (local.get $i)))
          (local.set $front (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $front))))
          (local.set $j (i32.add (local.get $j) (i32.const 1)))
          (br $find_front)
        )
      )
      (local.set $front_pair (ref.cast (ref $PAIR) (local.get $front)))

      ;; Find element at index (len - 1 - i) (back)
      (local.set $back (local.get $lst))
      (local.set $j (i32.const 0))
      (block $found_back
        (loop $find_back
          (br_if $found_back (i32.ge_s (local.get $j) (i32.sub (i32.sub (local.get $len) (i32.const 1)) (local.get $i))))
          (local.set $back (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $back))))
          (local.set $j (i32.add (local.get $j) (i32.const 1)))
          (br $find_back)
        )
      )
      (local.set $back_pair (ref.cast (ref $PAIR) (local.get $back)))

      ;; Swap values
      (local.set $tmp (struct.get $PAIR 0 (local.get $front_pair)))
      (struct.set $PAIR 0 (local.get $front_pair) (struct.get $PAIR 0 (local.get $back_pair)))
      (struct.set $PAIR 0 (local.get $back_pair) (local.get $tmp))

      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $loop)
    )
  )
  (local.get $lst)
)


;; List method: sort() in place - simple bubble sort
(func $list_sort_inplace (param $lst (ref null eq)) (result (ref null eq))
  (local $swapped i32)
  (local $current (ref null eq))
  (local $pair (ref null $PAIR))
  (local $next_pair (ref null $PAIR))
  (local $a (ref null eq))
  (local $b (ref null eq))
  (local $a_val i32)
  (local $b_val i32)
  (local $list_v2 (ref null $LIST))
  (local $len i32)
  (local $data (ref null $ARRAY_ANY))
  (local $i i32)
  (local $tmp (ref null eq))

  (if (ref.is_null (local.get $lst))
    (then (return (ref.null eq)))
  )
  (if (ref.test (ref $EMPTY_LIST) (local.get $lst))
    (then (return (local.get $lst)))
  )

  ;; Handle $LIST type
  (if (ref.test (ref $LIST) (local.get $lst))
    (then
      (local.set $list_v2 (ref.cast (ref $LIST) (local.get $lst)))
      (local.set $len (struct.get $LIST $len (ref.cast (ref $LIST) (local.get $list_v2))))
      (local.set $data (struct.get $LIST $data (ref.cast (ref $LIST) (local.get $list_v2))))

      ;; Bubble sort on array
      (block $done_v2
        (loop $outer_v2
          (local.set $swapped (i32.const 0))
          (local.set $i (i32.const 0))

          (block $inner_done_v2
            (loop $inner_v2
              (br_if $inner_done_v2 (i32.ge_s (local.get $i) (i32.sub (local.get $len) (i32.const 1))))

              (local.set $a (array.get $ARRAY_ANY (ref.cast (ref $ARRAY_ANY) (local.get $data)) (local.get $i)))
              (local.set $b (array.get $ARRAY_ANY (ref.cast (ref $ARRAY_ANY) (local.get $data)) (i32.add (local.get $i) (i32.const 1))))

              ;; Compare integers
              (if (i32.and (ref.test (ref i31) (local.get $a))
                           (ref.test (ref i31) (local.get $b)))
                (then
                  (local.set $a_val (i31.get_s (ref.cast (ref i31) (local.get $a))))
                  (local.set $b_val (i31.get_s (ref.cast (ref i31) (local.get $b))))
                  (if (i32.gt_s (local.get $a_val) (local.get $b_val))
                    (then
                      ;; Swap
                      (array.set $ARRAY_ANY (ref.cast (ref $ARRAY_ANY) (local.get $data)) (local.get $i) (local.get $b))
                      (array.set $ARRAY_ANY (ref.cast (ref $ARRAY_ANY) (local.get $data)) (i32.add (local.get $i) (i32.const 1)) (local.get $a))
                      (local.set $swapped (i32.const 1))
                    )
                  )
                )
              )
              ;; Compare strings
              (if (i32.and (ref.test (ref $STRING) (local.get $a))
                           (ref.test (ref $STRING) (local.get $b)))
                (then
                  (if (i32.gt_s
                        (call $strings_compare
                          (ref.cast (ref $STRING) (local.get $a))
                          (ref.cast (ref $STRING) (local.get $b)))
                        (i32.const 0))
                    (then
                      ;; Swap
                      (array.set $ARRAY_ANY (ref.cast (ref $ARRAY_ANY) (local.get $data)) (local.get $i) (local.get $b))
                      (array.set $ARRAY_ANY (ref.cast (ref $ARRAY_ANY) (local.get $data)) (i32.add (local.get $i) (i32.const 1)) (local.get $a))
                      (local.set $swapped (i32.const 1))
                    )
                  )
                )
              )

              (local.set $i (i32.add (local.get $i) (i32.const 1)))
              (br $inner_v2)
            )
          )

          (br_if $done_v2 (i32.eqz (local.get $swapped)))
          (br $outer_v2)
        )
      )
      (return (local.get $list_v2))
    )
  )

  ;; Bubble sort
  (block $done
    (loop $outer
      (local.set $swapped (i32.const 0))
      (local.set $current (local.get $lst))

      (block $inner_done
        (loop $inner
          (local.set $pair (ref.cast (ref $PAIR) (local.get $current)))
          (br_if $inner_done (ref.is_null (struct.get $PAIR 1 (local.get $pair))))

          (local.set $next_pair (ref.cast (ref $PAIR) (struct.get $PAIR 1 (local.get $pair))))
          (local.set $a (struct.get $PAIR 0 (local.get $pair)))
          (local.set $b (struct.get $PAIR 0 (local.get $next_pair)))

          ;; Compare integers
          (if (i32.and (ref.test (ref i31) (local.get $a))
                       (ref.test (ref i31) (local.get $b)))
            (then
              (local.set $a_val (i31.get_s (ref.cast (ref i31) (local.get $a))))
              (local.set $b_val (i31.get_s (ref.cast (ref i31) (local.get $b))))
              (if (i32.gt_s (local.get $a_val) (local.get $b_val))
                (then
                  ;; Swap
                  (struct.set $PAIR 0 (local.get $pair) (local.get $b))
                  (struct.set $PAIR 0 (local.get $next_pair) (local.get $a))
                  (local.set $swapped (i32.const 1))
                )
              )
            )
          )
          ;; Compare strings
          (if (i32.and (ref.test (ref $STRING) (local.get $a))
                       (ref.test (ref $STRING) (local.get $b)))
            (then
              (if (i32.gt_s
                    (call $strings_compare
                      (ref.cast (ref $STRING) (local.get $a))
                      (ref.cast (ref $STRING) (local.get $b)))
                    (i32.const 0))
                (then
                  ;; Swap
                  (struct.set $PAIR 0 (local.get $pair) (local.get $b))
                  (struct.set $PAIR 0 (local.get $next_pair) (local.get $a))
                  (local.set $swapped (i32.const 1))
                )
              )
            )
          )

          (local.set $current (struct.get $PAIR 1 (local.get $pair)))
          (br $inner)
        )
      )

      (br_if $done (i32.eqz (local.get $swapped)))
      (br $outer)
    )
  )
  (local.get $lst)  ;; Return the sorted list
)


;; List method: sort() in place with key function - Schwartzian transform
;; Takes list and key closure, returns sorted list (also mutates original)
(func $list_sort_with_key (param $lst (ref null eq)) (param $key_fn (ref null eq)) (result (ref null eq))
  (local $swapped i32)
  (local $current (ref null eq))
  (local $pair (ref null $PAIR))
  (local $next_pair (ref null $PAIR))
  (local $a (ref null eq))
  (local $b (ref null eq))
  (local $a_key (ref null eq))
  (local $b_key (ref null eq))
  (local $decorated (ref null eq))
  (local $dec_current (ref null eq))
  (local $orig_current (ref null eq))
  (local $closure (ref $CLOSURE))
  (local $env (ref null $ENV))
  (local $func_idx i32)
  (local $args (ref null eq))
  (local $key_result (ref null eq))
  (local $dec_pair (ref null $PAIR))
  (local $item (ref null eq))
  (local $orig_pair (ref null $PAIR))
  (local $orig_list_v2 (ref null $LIST))
  (local $i i32)
  (local $list_data (ref null $ARRAY_ANY))

  (if (ref.is_null (local.get $lst))
    (then (return (ref.null eq)))
  )
  (if (ref.test (ref $EMPTY_LIST) (local.get $lst))
    (then (return (local.get $lst)))
  )

  ;; Convert $LIST to PAIR chain if needed, keeping reference to original
  (if (ref.test (ref $LIST) (local.get $lst))
    (then
      (local.set $orig_list_v2 (ref.cast (ref $LIST) (local.get $lst)))
      (local.set $lst (call $list_v2_to_pair (ref.cast (ref $LIST) (local.get $orig_list_v2))))
    )
  )

  ;; Extract closure info
  (local.set $closure (ref.cast (ref $CLOSURE) (local.get $key_fn)))
  (local.set $env (struct.get $CLOSURE 0 (local.get $closure)))
  (local.set $func_idx (struct.get $CLOSURE 1 (local.get $closure)))

  ;; Step 1: Decorate - create list of (key, item) pairs
  ;; Build in forward order by appending
  (local.set $decorated (ref.null eq))
  (local.set $current (local.get $lst))
  (block $dec_done
    (loop $dec_loop
      (br_if $dec_done (ref.is_null (local.get $current)))
      (br_if $dec_done (i32.eqz (ref.test (ref $PAIR) (local.get $current))))
      (local.set $pair (ref.cast (ref $PAIR) (local.get $current)))
      (local.set $item (struct.get $PAIR 0 (local.get $pair)))

      ;; Call key function: key(item)
      (local.set $args (struct.new $PAIR (local.get $item) (ref.null eq)))
      (local.set $key_result
        (call_indirect (type $FUNC) (local.get $args) (local.get $env) (local.get $func_idx))
      )

      ;; Create decorated pair: (key_result, item) and append
      (local.set $decorated
        (call $list_append
          (local.get $decorated)
          (struct.new $PAIR (local.get $key_result) (local.get $item))
        )
      )

      (local.set $current (struct.get $PAIR 1 (local.get $pair)))
      (br $dec_loop)
    )
  )

  ;; Convert $decorated to PAIR chain if it became a $LIST
  (if (ref.test (ref $LIST) (local.get $decorated))
    (then
      (local.set $decorated (call $list_v2_to_pair (ref.cast (ref $LIST) (local.get $decorated))))
    )
  )

  ;; Step 2: Sort decorated list by key values (bubble sort)
  (block $sort_done
    (loop $outer
      (local.set $swapped (i32.const 0))
      (local.set $current (local.get $decorated))

      (block $inner_done
        (loop $inner
          (br_if $inner_done (ref.is_null (local.get $current)))
          (local.set $pair (ref.cast (ref $PAIR) (local.get $current)))
          (br_if $inner_done (ref.is_null (struct.get $PAIR 1 (local.get $pair))))

          (local.set $next_pair (ref.cast (ref $PAIR) (struct.get $PAIR 1 (local.get $pair))))

          ;; Get decorated pairs (key, item)
          (local.set $a (struct.get $PAIR 0 (local.get $pair)))
          (local.set $b (struct.get $PAIR 0 (local.get $next_pair)))

          ;; Extract keys from decorated pairs
          (local.set $a_key (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $a))))
          (local.set $b_key (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $b))))

          ;; Compare keys using generic compare
          (if (call $compare_values (local.get $a_key) (local.get $b_key))
            (then
              ;; Swap the decorated pairs
              (struct.set $PAIR 0 (local.get $pair) (local.get $b))
              (struct.set $PAIR 0 (local.get $next_pair) (local.get $a))
              (local.set $swapped (i32.const 1))
            )
          )

          (local.set $current (struct.get $PAIR 1 (local.get $pair)))
          (br $inner)
        )
      )

      (br_if $sort_done (i32.eqz (local.get $swapped)))
      (br $outer)
    )
  )

  ;; Step 3: Copy sorted values back to original list
  ;; If original was a $LIST, copy to its array; otherwise copy to PAIR chain
  (if (ref.is_null (local.get $orig_list_v2))
    (then
      ;; Original was PAIR chain - copy to PAIR chain
      (local.set $dec_current (local.get $decorated))
      (local.set $orig_current (local.get $lst))
      (block $copy_done
        (loop $copy_loop
          (br_if $copy_done (ref.is_null (local.get $dec_current)))
          (br_if $copy_done (ref.is_null (local.get $orig_current)))
          (br_if $copy_done (i32.eqz (ref.test (ref $PAIR) (local.get $dec_current))))
          (br_if $copy_done (i32.eqz (ref.test (ref $PAIR) (local.get $orig_current))))

          (local.set $pair (ref.cast (ref $PAIR) (local.get $dec_current)))
          (local.set $orig_pair (ref.cast (ref $PAIR) (local.get $orig_current)))

          ;; Get decorated pair (key, item) and extract item
          (local.set $dec_pair (ref.cast (ref $PAIR) (struct.get $PAIR 0 (local.get $pair))))
          (local.set $item (struct.get $PAIR 1 (local.get $dec_pair)))

          ;; Copy item to original list
          (struct.set $PAIR 0 (local.get $orig_pair) (local.get $item))

          (local.set $dec_current (struct.get $PAIR 1 (local.get $pair)))
          (local.set $orig_current (struct.get $PAIR 1 (local.get $orig_pair)))
          (br $copy_loop)
        )
      )
      (return (local.get $lst))
    )
    (else
      ;; Original was $LIST - copy to array
      (local.set $list_data (struct.get $LIST $data (local.get $orig_list_v2)))
      (local.set $i (i32.const 0))
      (local.set $dec_current (local.get $decorated))
      (block $copy_done_v2
        (loop $copy_loop_v2
          (br_if $copy_done_v2 (ref.is_null (local.get $dec_current)))
          (br_if $copy_done_v2 (i32.eqz (ref.test (ref $PAIR) (local.get $dec_current))))

          (local.set $pair (ref.cast (ref $PAIR) (local.get $dec_current)))

          ;; Get decorated pair (key, item) and extract item
          (local.set $dec_pair (ref.cast (ref $PAIR) (struct.get $PAIR 0 (local.get $pair))))
          (local.set $item (struct.get $PAIR 1 (local.get $dec_pair)))

          ;; Copy item to array
          (array.set $ARRAY_ANY (local.get $list_data) (local.get $i) (local.get $item))

          (local.set $i (i32.add (local.get $i) (i32.const 1)))
          (local.set $dec_current (struct.get $PAIR 1 (local.get $pair)))
          (br $copy_loop_v2)
        )
      )
      (return (local.get $orig_list_v2))
    )
  )
  (unreachable)
)


;; Convert list to set (removes duplicates)
(func $list_to_set (param $list (ref null eq)) (result (ref null eq))
  (local $current (ref null eq))
  (local $pair (ref null $PAIR))
  (local $result (ref null eq))
  (local $i i32)
  (local $len i32)
  (local $data (ref null $ARRAY_ANY))

  ;; Start with empty set
  (local.set $result (ref.null eq))

  ;; Handle null/empty list
  (if (ref.is_null (local.get $list))
    (then (return (ref.null eq)))
  )
  (if (ref.test (ref $EMPTY_LIST) (local.get $list))
    (then (return (ref.null eq)))
  )

  ;; Handle $LIST (array-backed)
  (if (ref.test (ref $LIST) (local.get $list))
    (then
      (local.set $data (struct.get $LIST 0 (ref.cast (ref $LIST) (local.get $list))))
      (local.set $len (struct.get $LIST 1 (ref.cast (ref $LIST) (local.get $list))))
      (local.set $i (i32.const 0))
      (block $done_list
        (loop $loop_list
          (br_if $done_list (i32.ge_s (local.get $i) (local.get $len)))
          ;; Add element to set (set_add handles duplicates)
          (local.set $result
            (call $set_add (local.get $result)
              (array.get $ARRAY_ANY (ref.cast (ref $ARRAY_ANY) (local.get $data)) (local.get $i))))
          (local.set $i (i32.add (local.get $i) (i32.const 1)))
          (br $loop_list)
        )
      )
      (return (local.get $result))
    )
  )

  ;; Iterate through PAIR chain, adding each element to set
  (local.set $current (local.get $list))
  (block $done
    (loop $loop
      (br_if $done (ref.is_null (local.get $current)))
      (if (i32.eqz (ref.test (ref $PAIR) (local.get $current)))
        (then (br $done))
      )
      (local.set $pair (ref.cast (ref $PAIR) (local.get $current)))
      ;; Add element to set (set_add handles duplicates)
      (local.set $result
        (call $set_add (local.get $result) (struct.get $PAIR 0 (local.get $pair))))
      ;; Move to next element
      (local.set $current (struct.get $PAIR 1 (local.get $pair)))
      (br $loop)
    )
  )
  (local.get $result)
)

"""
