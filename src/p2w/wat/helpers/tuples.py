"""WAT helper functions: Tuple operations."""

from __future__ import annotations

TUPLES_CODE = """

;; tuple_get: O(1) indexed access for $TUPLE with negative index support
(func $tuple_get (param $tup (ref $TUPLE)) (param $idx i32) (result (ref null eq))
  (local $real_idx i32)
  (local $len i32)
  (local.set $len (struct.get $TUPLE $len (local.get $tup)))

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
    (struct.get $TUPLE $data (local.get $tup))
    (local.get $real_idx)
  )
)


;; tuple_slice: slice a tuple, returns a new tuple
(func $tuple_slice (param $tup (ref $TUPLE)) (param $lower i32) (param $upper i32) (param $step i32) (result (ref null eq))
  (local $len i32)
  (local $real_lower i32)
  (local $real_upper i32)
  (local $i i32)
  (local $count i32)
  (local $new_len i32)
  (local $new_data (ref $ARRAY_ANY))
  (local $j i32)
  (local $data (ref $ARRAY_ANY))

  (local.set $len (struct.get $TUPLE $len (local.get $tup)))
  (local.set $data (struct.get $TUPLE $data (local.get $tup)))

  ;; Handle sentinel value -999999 for upper (means "to end")
  (if (i32.eq (local.get $upper) (i32.const -999999))
    (then (local.set $real_upper (local.get $len)))
    (else
      (if (i32.lt_s (local.get $upper) (i32.const 0))
        (then (local.set $real_upper (i32.add (local.get $len) (local.get $upper))))
        (else (local.set $real_upper (local.get $upper)))
      )
    )
  )

  ;; Handle negative lower
  (if (i32.lt_s (local.get $lower) (i32.const 0))
    (then (local.set $real_lower (i32.add (local.get $len) (local.get $lower))))
    (else (local.set $real_lower (local.get $lower)))
  )

  ;; Clamp bounds
  (if (i32.lt_s (local.get $real_lower) (i32.const 0))
    (then (local.set $real_lower (i32.const 0)))
  )
  (if (i32.gt_s (local.get $real_upper) (local.get $len))
    (then (local.set $real_upper (local.get $len)))
  )

  ;; Calculate new length (assuming step = 1 for now)
  (local.set $new_len (i32.sub (local.get $real_upper) (local.get $real_lower)))
  (if (i32.lt_s (local.get $new_len) (i32.const 0))
    (then (local.set $new_len (i32.const 0)))
  )

  ;; Empty result
  (if (i32.eqz (local.get $new_len))
    (then
      (return (struct.new $TUPLE
        (array.new_default $ARRAY_ANY (i32.const 0))
        (i32.const 0)))
    )
  )

  ;; Create new array and copy elements
  (local.set $new_data (array.new_default $ARRAY_ANY (local.get $new_len)))
  (local.set $i (local.get $real_lower))
  (local.set $j (i32.const 0))
  (block $done
    (loop $copy
      (br_if $done (i32.ge_s (local.get $i) (local.get $real_upper)))
      (array.set $ARRAY_ANY (local.get $new_data) (local.get $j)
        (array.get $ARRAY_ANY (local.get $data) (local.get $i)))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (local.set $j (i32.add (local.get $j) (i32.const 1)))
      (br $copy)
    )
  )

  (struct.new $TUPLE (local.get $new_data) (local.get $new_len))
)


;; tuple_concat: concatenate two tuples, returns new tuple
(func $tuple_concat (param $a (ref null eq)) (param $b (ref null eq)) (result (ref null eq))
  (local $tup_a (ref $TUPLE))
  (local $tup_b (ref $TUPLE))
  (local $len_a i32)
  (local $len_b i32)
  (local $new_len i32)
  (local $data_a (ref $ARRAY_ANY))
  (local $data_b (ref $ARRAY_ANY))
  (local $new_data (ref $ARRAY_ANY))
  (local $i i32)

  (local.set $tup_a (ref.cast (ref $TUPLE) (local.get $a)))
  (local.set $tup_b (ref.cast (ref $TUPLE) (local.get $b)))
  (local.set $len_a (struct.get $TUPLE $len (local.get $tup_a)))
  (local.set $len_b (struct.get $TUPLE $len (local.get $tup_b)))
  (local.set $data_a (struct.get $TUPLE $data (local.get $tup_a)))
  (local.set $data_b (struct.get $TUPLE $data (local.get $tup_b)))
  (local.set $new_len (i32.add (local.get $len_a) (local.get $len_b)))

  ;; Create new array
  (local.set $new_data (array.new_default $ARRAY_ANY (local.get $new_len)))

  ;; Copy elements from first tuple
  (local.set $i (i32.const 0))
  (block $done_a
    (loop $copy_a
      (br_if $done_a (i32.ge_s (local.get $i) (local.get $len_a)))
      (array.set $ARRAY_ANY (local.get $new_data) (local.get $i)
        (array.get $ARRAY_ANY (local.get $data_a) (local.get $i)))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $copy_a)
    )
  )

  ;; Copy elements from second tuple
  (local.set $i (i32.const 0))
  (block $done_b
    (loop $copy_b
      (br_if $done_b (i32.ge_s (local.get $i) (local.get $len_b)))
      (array.set $ARRAY_ANY (local.get $new_data) (i32.add (local.get $len_a) (local.get $i))
        (array.get $ARRAY_ANY (local.get $data_b) (local.get $i)))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $copy_b)
    )
  )

  (struct.new $TUPLE (local.get $new_data) (local.get $new_len))
)


;; tuple_repeat: repeat a tuple n times, returns new tuple
(func $tuple_repeat (param $tup (ref null eq)) (param $n (ref null eq)) (result (ref null eq))
  (local $tuple_ref (ref $TUPLE))
  (local $count i32)
  (local $old_len i32)
  (local $new_len i32)
  (local $old_data (ref $ARRAY_ANY))
  (local $new_data (ref $ARRAY_ANY))
  (local $i i32)
  (local $j i32)

  (if (ref.is_null (local.get $tup))
    (then (return (struct.new $TUPLE (array.new_default $ARRAY_ANY (i32.const 0)) (i32.const 0))))
  )

  (local.set $tuple_ref (ref.cast (ref $TUPLE) (local.get $tup)))
  (local.set $count (i31.get_s (ref.cast (ref i31) (local.get $n))))

  (if (i32.le_s (local.get $count) (i32.const 0))
    (then (return (struct.new $TUPLE (array.new_default $ARRAY_ANY (i32.const 0)) (i32.const 0))))
  )

  (local.set $old_len (struct.get $TUPLE $len (local.get $tuple_ref)))
  (local.set $old_data (struct.get $TUPLE $data (local.get $tuple_ref)))
  (local.set $new_len (i32.mul (local.get $old_len) (local.get $count)))

  ;; Create new array
  (local.set $new_data (array.new_default $ARRAY_ANY (local.get $new_len)))

  ;; Copy elements n times
  (local.set $j (i32.const 0))
  (block $done_outer
    (loop $repeat
      (br_if $done_outer (i32.ge_s (local.get $j) (local.get $count)))
      (local.set $i (i32.const 0))
      (block $done_inner
        (loop $copy
          (br_if $done_inner (i32.ge_s (local.get $i) (local.get $old_len)))
          (array.set $ARRAY_ANY (local.get $new_data)
            (i32.add (i32.mul (local.get $j) (local.get $old_len)) (local.get $i))
            (array.get $ARRAY_ANY (local.get $old_data) (local.get $i)))
          (local.set $i (i32.add (local.get $i) (i32.const 1)))
          (br $copy)
        )
      )
      (local.set $j (i32.add (local.get $j) (i32.const 1)))
      (br $repeat)
    )
  )

  (struct.new $TUPLE (local.get $new_data) (local.get $new_len))
)


;; make_tuple_1: create a single-element tuple containing the given value
(func $make_tuple_1 (param $val (ref null eq)) (result (ref $TUPLE))
  (local $data (ref $ARRAY_ANY))
  ;; Create array with 1 element
  (local.set $data (array.new $ARRAY_ANY (local.get $val) (i32.const 1)))
  ;; Create and return TUPLE
  (struct.new $TUPLE (local.get $data) (i32.const 1))
)


;; tuple_contains: check if item is in tuple
(func $tuple_contains (param $item (ref null eq)) (param $tup (ref $TUPLE)) (result i32)
  (local $data (ref $ARRAY_ANY))
  (local $len i32)
  (local $i i32)

  (local.set $data (struct.get $TUPLE $data (local.get $tup)))
  (local.set $len (struct.get $TUPLE $len (local.get $tup)))

  (block $done
    (loop $check
      (br_if $done (i32.ge_s (local.get $i) (local.get $len)))
      (if (call $values_equal (local.get $item) (array.get $ARRAY_ANY (local.get $data) (local.get $i)))
        (then (return (i32.const 1)))
      )
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $check)
    )
  )
  (i32.const 0)
)


;; tuple_to_pair: convert $TUPLE to PAIR chain for iteration
(func $tuple_to_pair (param $tup (ref $TUPLE)) (result (ref null eq))
  (local $data (ref $ARRAY_ANY))
  (local $len i32)
  (local $i i32)
  (local $result (ref null eq))

  (local.set $data (struct.get $TUPLE $data (local.get $tup)))
  (local.set $len (struct.get $TUPLE $len (local.get $tup)))

  ;; Empty tuple -> null
  (if (i32.eq (local.get $len) (i32.const 0))
    (then (return (ref.null eq)))
  )

  ;; Build PAIR chain in reverse order (start from end)
  (local.set $i (i32.sub (local.get $len) (i32.const 1)))
  (local.set $result (ref.null eq))

  (block $done
    (loop $build
      (br_if $done (i32.lt_s (local.get $i) (i32.const 0)))
      (local.set $result
        (struct.new $PAIR
          (array.get $ARRAY_ANY (local.get $data) (local.get $i))
          (local.get $result)))
      (local.set $i (i32.sub (local.get $i) (i32.const 1)))
      (br $build)
    )
  )
  (local.get $result)
)


;; tuple_to_string: convert $TUPLE to string "(elem, elem, ...)" or "(elem,)" for single
(func $tuple_to_string (param $tup (ref null eq)) (result (ref $STRING))
  (local $result (ref $STRING))
  (local $tuple_ref (ref $TUPLE))
  (local $data (ref $ARRAY_ANY))
  (local $len i32)
  (local $i i32)
  (local $elem (ref null eq))
  (local $elem_str (ref $STRING))
  (local $offset i32)
  (local $comma_space (ref $STRING))
  (local $paren_open (ref $STRING))
  (local $paren_close (ref $STRING))
  (local $trailing_comma (ref $STRING))

  (local.set $tuple_ref (ref.cast (ref $TUPLE) (local.get $tup)))
  (local.set $data (struct.get $TUPLE $data (local.get $tuple_ref)))
  (local.set $len (struct.get $TUPLE $len (local.get $tuple_ref)))

  ;; Create "(" string
  (local.set $offset (global.get $string_heap))
  (i32.store8 (local.get $offset) (i32.const 40))  ;; (
  (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 1)))
  (local.set $paren_open (struct.new $STRING (local.get $offset) (i32.const 1)))

  ;; Create ")" string
  (local.set $offset (global.get $string_heap))
  (i32.store8 (local.get $offset) (i32.const 41))  ;; )
  (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 1)))
  (local.set $paren_close (struct.new $STRING (local.get $offset) (i32.const 1)))

  ;; Create ", " string
  (local.set $offset (global.get $string_heap))
  (i32.store8 (local.get $offset) (i32.const 44))  ;; ,
  (i32.store8 (i32.add (local.get $offset) (i32.const 1)) (i32.const 32))  ;; space
  (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 2)))
  (local.set $comma_space (struct.new $STRING (local.get $offset) (i32.const 2)))

  ;; Create ",)" string for single-element tuple
  (local.set $offset (global.get $string_heap))
  (i32.store8 (local.get $offset) (i32.const 44))  ;; ,
  (i32.store8 (i32.add (local.get $offset) (i32.const 1)) (i32.const 41))  ;; )
  (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 2)))
  (local.set $trailing_comma (struct.new $STRING (local.get $offset) (i32.const 2)))

  ;; Start with "("
  (local.set $result (local.get $paren_open))
  (local.set $i (i32.const 0))

  (block $done
    (loop $loop
      (br_if $done (i32.ge_s (local.get $i) (local.get $len)))

      ;; Add ", " before non-first elements
      (if (i32.gt_s (local.get $i) (i32.const 0))
        (then
          (local.set $result (call $string_concat (local.get $result) (local.get $comma_space)))
        )
      )

      ;; Get element and convert to string
      (local.set $elem (array.get $ARRAY_ANY (local.get $data) (local.get $i)))
      (local.set $elem_str (call $value_to_string_repr (local.get $elem)))
      (local.set $result (call $string_concat (local.get $result) (local.get $elem_str)))

      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $loop)
    )
  )

  ;; For single-element tuple, add trailing comma before closing paren
  (if (i32.eq (local.get $len) (i32.const 1))
    (then
      (return (call $string_concat (local.get $result) (local.get $trailing_comma)))
    )
  )

  ;; Add ")"
  (call $string_concat (local.get $result) (local.get $paren_close))
)

"""
