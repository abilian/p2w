"""WAT builtin functions: Sequence and iterable functions (len, map, filter, etc.)."""

from __future__ import annotations

LEN_CODE = """
(func $len (param $args (ref null eq)) (param $env (ref null $ENV)) (result (ref null eq))
  (local $val (ref null eq))
  (local $method_result (ref null eq))
  (local $method_name (ref $STRING))
  (local $offset i32)
  ;; Get first argument
  (if (ref.is_null (local.get $args))
    (then
      (return (ref.i31 (i32.const 0)))
    )
  )
  (local.set $val (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))

  ;; Check for OBJECT with __len__ special method
  (if (ref.test (ref $OBJECT) (local.get $val))
    (then
      ;; Create string "__len__" (7 chars: 95,95,108,101,110,95,95)
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

      ;; Call __len__(self) - args = (PAIR self null)
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

  ;; Check type and compute length
  ;; $LIST (array-backed) - O(1)
  (if (ref.test (ref $LIST) (local.get $val))
    (then
      (return (ref.i31 (struct.get $LIST $len (ref.cast (ref $LIST) (local.get $val)))))
    )
  )
  ;; $TUPLE (array-backed) - O(1)
  (if (ref.test (ref $TUPLE) (local.get $val))
    (then
      (return (ref.i31 (struct.get $TUPLE $len (ref.cast (ref $TUPLE) (local.get $val)))))
    )
  )
  ;; $DICT wrapper (hash table count)
  (if (ref.test (ref $DICT) (local.get $val))
    (then
      (return (ref.i31 (struct.get $HASHTABLE $count
        (struct.get $DICT $table (ref.cast (ref $DICT) (local.get $val))))))
    )
  )
  ;; PAIR chain (list/tuple)
  (if (ref.test (ref $PAIR) (local.get $val))
    (then
      (return (ref.i31 (call $list_len (local.get $val))))
    )
  )
  ;; BYTES (check before STRING since they have same structure)
  (if (ref.test (ref $BYTES) (local.get $val))
    (then
      (return (ref.i31 (struct.get $BYTES 1 (ref.cast (ref $BYTES) (local.get $val)))))
    )
  )
  ;; STRING
  (if (ref.test (ref $STRING) (local.get $val))
    (then
      (return (ref.i31 (struct.get $STRING 1 (ref.cast (ref $STRING) (local.get $val)))))
    )
  )
  ;; Unknown type - return 0
  (ref.i31 (i32.const 0))
)
"""

MIN_CODE = """
;; min() - find minimum value in iterable, supports int and float
(func $min (param $args (ref null eq)) (param $env (ref null $ENV)) (result (ref null eq))
  (local $current (ref null eq))
  (local $first_arg (ref null eq))
  (local $elem (ref null eq))
  (local $result (ref null eq))
  (local $first i32)
  (local $arr (ref $ARRAY_ANY))
  (local $len i32)
  (local $i i32)
  (if (ref.is_null (local.get $args))
    (then (return (ref.null eq)))
  )
  ;; Check if single arg that is iterable - if so, iterate over it
  (local.set $first_arg (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))
  (if (ref.is_null (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $args))))
    (then
      ;; Single argument - check type
      ;; Fast path for $LIST (direct array iteration)
      (if (ref.test (ref $LIST) (local.get $first_arg))
        (then
          (local.set $arr (struct.get $LIST $data (ref.cast (ref $LIST) (local.get $first_arg))))
          (local.set $len (struct.get $LIST $len (ref.cast (ref $LIST) (local.get $first_arg))))
          (if (i32.eqz (local.get $len))
            (then (return (ref.null eq)))  ;; Empty list
          )
          (local.set $result (array.get $ARRAY_ANY (local.get $arr) (i32.const 0)))
          (local.set $i (i32.const 1))
          (block $list_done
            (loop $list_loop
              (br_if $list_done (i32.ge_s (local.get $i) (local.get $len)))
              (local.set $elem (array.get $ARRAY_ANY (local.get $arr) (local.get $i)))
              (if (call $numeric_lt (local.get $elem) (local.get $result))
                (then (local.set $result (local.get $elem)))
              )
              (local.set $i (i32.add (local.get $i) (i32.const 1)))
              (br $list_loop)
            )
          )
          (return (local.get $result))
        )
      )
      ;; Fast path for $TUPLE (direct array iteration)
      (if (ref.test (ref $TUPLE) (local.get $first_arg))
        (then
          (local.set $arr (struct.get $TUPLE $data (ref.cast (ref $TUPLE) (local.get $first_arg))))
          (local.set $len (struct.get $TUPLE $len (ref.cast (ref $TUPLE) (local.get $first_arg))))
          (if (i32.eqz (local.get $len))
            (then (return (ref.null eq)))  ;; Empty tuple
          )
          (local.set $result (array.get $ARRAY_ANY (local.get $arr) (i32.const 0)))
          (local.set $i (i32.const 1))
          (block $tuple_done
            (loop $tuple_loop
              (br_if $tuple_done (i32.ge_s (local.get $i) (local.get $len)))
              (local.set $elem (array.get $ARRAY_ANY (local.get $arr) (local.get $i)))
              (if (call $numeric_lt (local.get $elem) (local.get $result))
                (then (local.set $result (local.get $elem)))
              )
              (local.set $i (i32.add (local.get $i) (i32.const 1)))
              (br $tuple_loop)
            )
          )
          (return (local.get $result))
        )
      )
      ;; Slow path: check if iterable (PAIR, etc)
      (if (ref.test (ref $PAIR) (local.get $first_arg))
        (then (local.set $current (local.get $first_arg)))
        (else
          (if (ref.test (ref $EMPTY_LIST) (local.get $first_arg))
            (then (return (ref.null eq)))  ;; Empty list - could raise ValueError
            (else (local.set $current (local.get $args)))
          )
        )
      )
    )
    (else (local.set $current (local.get $args)))
  )
  (local.set $first (i32.const 1))
  (local.set $result (ref.null eq))
  (block $done
    (loop $loop
      (br_if $done (ref.is_null (local.get $current)))
      (br_if $done (i32.eqz (ref.test (ref $PAIR) (local.get $current))))
      (local.set $elem (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $current))))
      (if (local.get $first)
        (then
          (local.set $result (local.get $elem))
          (local.set $first (i32.const 0))
        )
        (else
          ;; Compare elem < result using numeric_lt
          (if (call $numeric_lt (local.get $elem) (local.get $result))
            (then (local.set $result (local.get $elem)))
          )
        )
      )
      (local.set $current (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current))))
      (br $loop)
    )
  )
  (local.get $result)
)
"""

MAX_CODE = """
;; max() - find maximum value in iterable, supports int and float
(func $max (param $args (ref null eq)) (param $env (ref null $ENV)) (result (ref null eq))
  (local $current (ref null eq))
  (local $first_arg (ref null eq))
  (local $elem (ref null eq))
  (local $result (ref null eq))
  (local $first i32)
  (local $arr (ref $ARRAY_ANY))
  (local $len i32)
  (local $i i32)
  (if (ref.is_null (local.get $args))
    (then (return (ref.null eq)))
  )
  ;; Check if single arg that is iterable - if so, iterate over it
  (local.set $first_arg (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))
  (if (ref.is_null (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $args))))
    (then
      ;; Single argument - check type
      ;; Fast path for $LIST (direct array iteration)
      (if (ref.test (ref $LIST) (local.get $first_arg))
        (then
          (local.set $arr (struct.get $LIST $data (ref.cast (ref $LIST) (local.get $first_arg))))
          (local.set $len (struct.get $LIST $len (ref.cast (ref $LIST) (local.get $first_arg))))
          (if (i32.eqz (local.get $len))
            (then (return (ref.null eq)))  ;; Empty list
          )
          (local.set $result (array.get $ARRAY_ANY (local.get $arr) (i32.const 0)))
          (local.set $i (i32.const 1))
          (block $list_done
            (loop $list_loop
              (br_if $list_done (i32.ge_s (local.get $i) (local.get $len)))
              (local.set $elem (array.get $ARRAY_ANY (local.get $arr) (local.get $i)))
              (if (call $numeric_gt (local.get $elem) (local.get $result))
                (then (local.set $result (local.get $elem)))
              )
              (local.set $i (i32.add (local.get $i) (i32.const 1)))
              (br $list_loop)
            )
          )
          (return (local.get $result))
        )
      )
      ;; Fast path for $TUPLE (direct array iteration)
      (if (ref.test (ref $TUPLE) (local.get $first_arg))
        (then
          (local.set $arr (struct.get $TUPLE $data (ref.cast (ref $TUPLE) (local.get $first_arg))))
          (local.set $len (struct.get $TUPLE $len (ref.cast (ref $TUPLE) (local.get $first_arg))))
          (if (i32.eqz (local.get $len))
            (then (return (ref.null eq)))  ;; Empty tuple
          )
          (local.set $result (array.get $ARRAY_ANY (local.get $arr) (i32.const 0)))
          (local.set $i (i32.const 1))
          (block $tuple_done
            (loop $tuple_loop
              (br_if $tuple_done (i32.ge_s (local.get $i) (local.get $len)))
              (local.set $elem (array.get $ARRAY_ANY (local.get $arr) (local.get $i)))
              (if (call $numeric_gt (local.get $elem) (local.get $result))
                (then (local.set $result (local.get $elem)))
              )
              (local.set $i (i32.add (local.get $i) (i32.const 1)))
              (br $tuple_loop)
            )
          )
          (return (local.get $result))
        )
      )
      ;; Slow path: check if iterable (PAIR, etc)
      (if (ref.test (ref $PAIR) (local.get $first_arg))
        (then (local.set $current (local.get $first_arg)))
        (else
          (if (ref.test (ref $EMPTY_LIST) (local.get $first_arg))
            (then (return (ref.null eq)))  ;; Empty list - could raise ValueError
            (else (local.set $current (local.get $args)))
          )
        )
      )
    )
    (else (local.set $current (local.get $args)))
  )
  (local.set $first (i32.const 1))
  (local.set $result (ref.null eq))
  (block $done
    (loop $loop
      (br_if $done (ref.is_null (local.get $current)))
      (br_if $done (i32.eqz (ref.test (ref $PAIR) (local.get $current))))
      (local.set $elem (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $current))))
      (if (local.get $first)
        (then
          (local.set $result (local.get $elem))
          (local.set $first (i32.const 0))
        )
        (else
          ;; Compare elem > result using numeric_gt
          (if (call $numeric_gt (local.get $elem) (local.get $result))
            (then (local.set $result (local.get $elem)))
          )
        )
      )
      (local.set $current (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current))))
      (br $loop)
    )
  )
  (local.get $result)
)
"""

SUM_CODE = """
(func $sum (param $args (ref null eq)) (param $env (ref null $ENV)) (result (ref null eq))
  (local $list (ref null eq))
  (local $current (ref null eq))
  (local $result i32)
  (local $arg2 (ref null eq))
  (local $arr (ref $ARRAY_ANY))
  (local $len i32)
  (local $i i32)
  (if (ref.is_null (local.get $args))
    (then (return (ref.i31 (i32.const 0))))
  )
  ;; Get the iterable argument
  (local.set $list (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))

  ;; Check for optional start argument (default 0)
  (local.set $arg2 (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $args))))
  (if (ref.is_null (local.get $arg2))
    (then (local.set $result (i32.const 0)))
    (else (local.set $result (i31.get_s (ref.cast (ref i31)
      (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $arg2)))))))
  )

  ;; Fast path for $LIST (direct array iteration)
  (if (ref.test (ref $LIST) (local.get $list))
    (then
      (local.set $arr (struct.get $LIST $data (ref.cast (ref $LIST) (local.get $list))))
      (local.set $len (struct.get $LIST $len (ref.cast (ref $LIST) (local.get $list))))
      (local.set $i (i32.const 0))
      (block $list_done
        (loop $list_loop
          (br_if $list_done (i32.ge_s (local.get $i) (local.get $len)))
          (local.set $result (i32.add (local.get $result)
            (i31.get_s (ref.cast (ref i31)
              (array.get $ARRAY_ANY (local.get $arr) (local.get $i))))))
          (local.set $i (i32.add (local.get $i) (i32.const 1)))
          (br $list_loop)
        )
      )
      (return (ref.i31 (local.get $result)))
    )
  )

  ;; Fast path for $TUPLE (direct array iteration)
  (if (ref.test (ref $TUPLE) (local.get $list))
    (then
      (local.set $arr (struct.get $TUPLE $data (ref.cast (ref $TUPLE) (local.get $list))))
      (local.set $len (struct.get $TUPLE $len (ref.cast (ref $TUPLE) (local.get $list))))
      (local.set $i (i32.const 0))
      (block $tuple_done
        (loop $tuple_loop
          (br_if $tuple_done (i32.ge_s (local.get $i) (local.get $len)))
          (local.set $result (i32.add (local.get $result)
            (i31.get_s (ref.cast (ref i31)
              (array.get $ARRAY_ANY (local.get $arr) (local.get $i))))))
          (local.set $i (i32.add (local.get $i) (i32.const 1)))
          (br $tuple_loop)
        )
      )
      (return (ref.i31 (local.get $result)))
    )
  )

  ;; Slow path: Convert to PAIR chain if needed ($GENERATOR, DICT, etc)
  (local.set $list (call $iter_prepare (local.get $list)))
  (local.set $current (local.get $list))
  (block $done
    (loop $loop
      (br_if $done (ref.is_null (local.get $current)))
      (br_if $done (ref.test (ref $EMPTY_LIST) (local.get $current)))
      (local.set $result (i32.add (local.get $result)
        (i31.get_s (ref.cast (ref i31)
          (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $current)))))))
      (local.set $current (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current))))
      (br $loop)
    )
  )
  (ref.i31 (local.get $result))
)
"""

RANGE_BUILTIN_CODE = """
;; range() returns $LIST (array-backed) for O(1) indexed access
(func $range (param $args (ref null eq)) (param $env (ref null $ENV)) (result (ref null eq))
  (local $start i32)
  (local $stop i32)
  (local $step i32)
  (local $len i32)
  (local $current i32)
  (local $i i32)
  (local $arr (ref $ARRAY_ANY))
  (local $arg1 (ref null eq))
  (local $arg2 (ref null eq))
  (local $arg3 (ref null eq))
  ;; Parse arguments
  (if (ref.is_null (local.get $args))
    (then (return (struct.new $EMPTY_LIST)))
  )
  (local.set $arg1 (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))
  (local.set $arg2 (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $args))))
  (if (ref.is_null (local.get $arg2))
    (then
      ;; Single arg: range(stop)
      (local.set $start (i32.const 0))
      (local.set $stop (i31.get_s (ref.cast (ref i31) (local.get $arg1))))
      (local.set $step (i32.const 1))
    )
    (else
      ;; Two or three args
      (local.set $start (i31.get_s (ref.cast (ref i31) (local.get $arg1))))
      (local.set $stop (i31.get_s (ref.cast (ref i31)
        (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $arg2))))))
      (local.set $arg3 (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $arg2))))
      (if (ref.is_null (local.get $arg3))
        (then
          ;; Two args: range(start, stop)
          (local.set $step (i32.const 1))
        )
        (else
          ;; Three args: range(start, stop, step)
          (local.set $step (i31.get_s (ref.cast (ref i31)
            (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $arg3))))))
        )
      )
    )
  )
  ;; Calculate length
  (if (i32.eqz (local.get $step))
    (then (return (struct.new $EMPTY_LIST)))  ;; step=0 is invalid, return empty
  )
  (if (i32.gt_s (local.get $step) (i32.const 0))
    (then
      ;; Positive step: len = max(0, ceil((stop - start) / step))
      (if (i32.ge_s (local.get $start) (local.get $stop))
        (then (local.set $len (i32.const 0)))
        (else
          (local.set $len (i32.div_s
            (i32.add
              (i32.sub (local.get $stop) (local.get $start))
              (i32.sub (local.get $step) (i32.const 1)))
            (local.get $step)))
        )
      )
    )
    (else
      ;; Negative step: len = max(0, ceil((start - stop) / -step))
      (if (i32.le_s (local.get $start) (local.get $stop))
        (then (local.set $len (i32.const 0)))
        (else
          (local.set $len (i32.div_s
            (i32.add
              (i32.sub (local.get $start) (local.get $stop))
              (i32.sub (i32.const 0) (i32.add (local.get $step) (i32.const 1))))
            (i32.sub (i32.const 0) (local.get $step))))
        )
      )
    )
  )
  ;; Return empty list if length is 0
  (if (i32.le_s (local.get $len) (i32.const 0))
    (then (return (struct.new $EMPTY_LIST)))
  )
  ;; Allocate array and fill with values
  (local.set $arr (array.new $ARRAY_ANY (ref.null eq) (local.get $len)))
  (local.set $current (local.get $start))
  (local.set $i (i32.const 0))
  (block $done
    (loop $loop
      (br_if $done (i32.ge_s (local.get $i) (local.get $len)))
      (array.set $ARRAY_ANY (local.get $arr) (local.get $i) (ref.i31 (local.get $current)))
      (local.set $current (i32.add (local.get $current) (local.get $step)))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $loop)
    )
  )
  ;; Return $LIST struct (data, len, cap - cap equals len for range)
  (struct.new $LIST (local.get $arr) (local.get $len) (local.get $len))
)
"""

MAP_CODE = """
(func $map (param $args (ref null eq)) (param $env (ref null $ENV)) (result (ref null eq))
  (local $func (ref null eq))
  (local $iterable (ref null eq))
  (local $current (ref null eq))
  (local $result (ref null eq))
  (local $tail (ref null eq))
  (local $mapped (ref null eq))
  (local $closure (ref null $CLOSURE))
  ;; Get arguments: func, iterable
  (if (ref.is_null (local.get $args))
    (then (return (ref.null eq)))
  )
  (local.set $func (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))
  (local.set $iterable (struct.get $PAIR 0 (ref.cast (ref $PAIR)
    (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $args))))))
  ;; Convert to PAIR chain if needed ($LIST, GENERATOR, TUPLE, DICT)
  (local.set $iterable (call $iter_prepare (local.get $iterable)))
  (local.set $closure (ref.cast (ref $CLOSURE) (local.get $func)))
  ;; Iterate through the iterable and apply func to each
  (local.set $current (local.get $iterable))
  (local.set $result (ref.null eq))
  (block $done
    (loop $loop
      (br_if $done (ref.is_null (local.get $current)))
      ;; Handle EMPTY_LIST
      (br_if $done (ref.test (ref $EMPTY_LIST) (local.get $current)))
      ;; Call func with current element using call_indirect
      (local.set $mapped
        (call_indirect (type $FUNC)
          (struct.new $PAIR
            (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $current)))
            (ref.null eq))
          (struct.get $CLOSURE 0 (local.get $closure))
          (struct.get $CLOSURE 1 (local.get $closure))))
      ;; Append to result
      (if (ref.is_null (local.get $result))
        (then
          (local.set $result (struct.new $PAIR (local.get $mapped) (ref.null eq)))
          (local.set $tail (local.get $result))
        )
        (else
          (struct.set $PAIR 1 (ref.cast (ref $PAIR) (local.get $tail))
            (struct.new $PAIR (local.get $mapped) (ref.null eq)))
          (local.set $tail (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $tail))))
        )
      )
      (local.set $current (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current))))
      (br $loop)
    )
  )
  (local.get $result)
)
"""

FILTER_CODE = """
(func $filter (param $args (ref null eq)) (param $env (ref null $ENV)) (result (ref null eq))
  (local $func (ref null eq))
  (local $iterable (ref null eq))
  (local $current (ref null eq))
  (local $elem (ref null eq))
  (local $result (ref null eq))
  (local $tail (ref null eq))
  (local $test_result (ref null eq))
  (local $closure (ref null $CLOSURE))
  (local $use_func i32)
  ;; Get arguments: func, iterable
  (if (ref.is_null (local.get $args))
    (then (return (ref.null eq)))
  )
  (local.set $func (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))
  (local.set $iterable (struct.get $PAIR 0 (ref.cast (ref $PAIR)
    (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $args))))))
  ;; Convert to PAIR chain if needed ($LIST, GENERATOR, TUPLE, DICT)
  (local.set $iterable (call $iter_prepare (local.get $iterable)))
  ;; Check if func is None (null) - if so, use truthy test on elements directly
  (local.set $use_func (i32.const 0))
  (if (i32.eqz (ref.is_null (local.get $func)))
    (then
      (if (ref.test (ref $CLOSURE) (local.get $func))
        (then
          (local.set $closure (ref.cast (ref $CLOSURE) (local.get $func)))
          (local.set $use_func (i32.const 1))
        )
      )
    )
  )
  ;; Iterate and filter
  (local.set $current (local.get $iterable))
  (local.set $result (ref.null eq))
  (block $done
    (loop $loop
      (br_if $done (ref.is_null (local.get $current)))
      ;; Handle EMPTY_LIST
      (br_if $done (ref.test (ref $EMPTY_LIST) (local.get $current)))
      ;; Get current element
      (local.set $elem (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $current))))
      ;; Get test result - either from calling func or from truthy test on element
      (if (local.get $use_func)
        (then
          ;; Call func with current element using call_indirect
          (local.set $test_result
            (call_indirect (type $FUNC)
              (struct.new $PAIR (local.get $elem) (ref.null eq))
              (struct.get $CLOSURE 0 (local.get $closure))
              (struct.get $CLOSURE 1 (local.get $closure))))
        )
        (else
          ;; func is None - use element itself as test result
          (local.set $test_result (local.get $elem))
        )
      )
      ;; If truthy, include in result
      (if (i32.eqz (call $is_false (local.get $test_result)))
        (then
          (if (ref.is_null (local.get $result))
            (then
              (local.set $result (struct.new $PAIR (local.get $elem) (ref.null eq)))
              (local.set $tail (local.get $result))
            )
            (else
              (struct.set $PAIR 1 (ref.cast (ref $PAIR) (local.get $tail))
                (struct.new $PAIR (local.get $elem) (ref.null eq)))
              (local.set $tail (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $tail))))
            )
          )
        )
      )
      (local.set $current (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current))))
      (br $loop)
    )
  )
  (local.get $result)
)
"""

SORTED_CODE = """
(func $sorted (param $args (ref null eq)) (param $env (ref null $ENV)) (result (ref null eq))
  (local $list (ref null eq))
  (local $result (ref null eq))
  (local $current (ref null eq))
  (local $changed i32)
  (local $a (ref null eq))
  (local $b (ref null eq))
  (local $tmp (ref null eq))
  ;; Get argument
  (if (ref.is_null (local.get $args))
    (then (return (struct.new $EMPTY_LIST)))
  )
  (local.set $list (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))
  ;; Copy list first (sorted returns new list)
  (local.set $result (call $copy_list (local.get $list)))
  ;; Handle empty list - return early
  (if (ref.test (ref $EMPTY_LIST) (local.get $result))
    (then (return (local.get $result)))
  )
  (if (ref.is_null (local.get $result))
    (then (return (struct.new $EMPTY_LIST)))
  )
  ;; Bubble sort
  (local.set $changed (i32.const 1))
  (block $sort_done
    (loop $sort_loop
      (br_if $sort_done (i32.eqz (local.get $changed)))
      (local.set $changed (i32.const 0))
      (local.set $current (local.get $result))
      (block $pass_done
        (loop $pass
          (br_if $pass_done (ref.is_null (local.get $current)))
          (br_if $pass_done (ref.is_null (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current)))))
          (local.set $a (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $current))))
          (local.set $b (struct.get $PAIR 0 (ref.cast (ref $PAIR)
            (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current))))))
          ;; Compare and swap if needed
          (if (call $compare_values (local.get $a) (local.get $b))
            (then
              ;; Swap
              (struct.set $PAIR 0 (ref.cast (ref $PAIR) (local.get $current)) (local.get $b))
              (struct.set $PAIR 0 (ref.cast (ref $PAIR)
                (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current)))) (local.get $a))
              (local.set $changed (i32.const 1))
            )
          )
          (local.set $current (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current))))
          (br $pass)
        )
      )
      (br $sort_loop)
    )
  )
  (local.get $result)
)
"""

ENUMERATE_CODE = """
;; enumerate(iterable, start=0) - return list of (index, value) pairs
(func $enumerate (param $args (ref null eq)) (param $env (ref null $ENV)) (result (ref null eq))
  (local $iterable (ref null eq))
  (local $start i32)
  (local $index i32)
  (local $current (ref null eq))
  (local $result (ref null eq))
  (local $elem (ref null eq))
  (local $tuple (ref null eq))
  (local $tuple_data (ref $ARRAY_ANY))
  (local $arg2 (ref null eq))
  ;; Parse arguments
  (if (ref.is_null (local.get $args))
    (then (return (ref.null eq)))
  )
  (local.set $iterable (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))
  ;; Convert to PAIR chain if needed ($LIST, GENERATOR, TUPLE, DICT)
  (local.set $iterable (call $iter_prepare (local.get $iterable)))
  (local.set $arg2 (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $args))))
  (if (ref.is_null (local.get $arg2))
    (then
      ;; Single arg: enumerate(iterable), start=0
      (local.set $start (i32.const 0))
    )
    (else
      ;; Two args: enumerate(iterable, start)
      (local.set $start (i31.get_s (ref.cast (ref i31)
        (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $arg2))))))
    )
  )
  ;; Build list of (index, value) pairs
  (local.set $index (local.get $start))
  (local.set $result (ref.null eq))
  (local.set $current (local.get $iterable))
  (block $done
    (loop $loop
      (br_if $done (ref.is_null (local.get $current)))
      (if (i32.eqz (ref.test (ref $PAIR) (local.get $current)))
        (then (br $done))
      )
      ;; Get element
      (local.set $elem (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $current))))
      ;; Create tuple (index, value) as array-backed $TUPLE
      (local.set $tuple_data (array.new $ARRAY_ANY (ref.null eq) (i32.const 2)))
      (array.set $ARRAY_ANY (local.get $tuple_data) (i32.const 0) (ref.i31 (local.get $index)))
      (array.set $ARRAY_ANY (local.get $tuple_data) (i32.const 1) (local.get $elem))
      (local.set $tuple (struct.new $TUPLE (local.get $tuple_data) (i32.const 2)))
      ;; Add to result list
      (local.set $result (struct.new $PAIR (local.get $tuple) (local.get $result)))
      ;; Increment index and advance
      (local.set $index (i32.add (local.get $index) (i32.const 1)))
      (local.set $current (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current))))
      (br $loop)
    )
  )
  ;; Reverse to maintain original order
  (call $list_reverse (local.get $result))
)
"""

ZIP_CODE = """
;; zip(*iterables) - return list of tuples, supports 2 or 3 iterables
(func $zip (param $args (ref null eq)) (param $env (ref null $ENV)) (result (ref null eq))
  (local $list_a (ref null eq))
  (local $list_b (ref null eq))
  (local $list_c (ref null eq))
  (local $current_a (ref null eq))
  (local $current_b (ref null eq))
  (local $current_c (ref null eq))
  (local $result (ref null eq))
  (local $elem_a (ref null eq))
  (local $elem_b (ref null eq))
  (local $elem_c (ref null eq))
  (local $tuple (ref null eq))
  (local $tuple_data (ref $ARRAY_ANY))
  (local $arg2 (ref null eq))
  (local $arg3 (ref null eq))
  (local $num_iters i32)

  ;; Parse arguments
  (if (ref.is_null (local.get $args))
    (then (return (ref.null eq)))
  )

  ;; First iterable
  (local.set $list_a (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))
  (local.set $list_a (call $iter_prepare (local.get $list_a)))
  (local.set $num_iters (i32.const 1))

  ;; Second iterable (if present)
  (local.set $arg2 (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $args))))
  (if (i32.eqz (ref.is_null (local.get $arg2)))
    (then
      (local.set $list_b (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $arg2))))
      (local.set $list_b (call $iter_prepare (local.get $list_b)))
      (local.set $num_iters (i32.const 2))

      ;; Third iterable (if present)
      (local.set $arg3 (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $arg2))))
      (if (i32.eqz (ref.is_null (local.get $arg3)))
        (then
          (local.set $list_c (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $arg3))))
          (local.set $list_c (call $iter_prepare (local.get $list_c)))
          (local.set $num_iters (i32.const 3))
        )
      )
    )
  )

  ;; Need at least 2 iterables for zip
  (if (i32.lt_s (local.get $num_iters) (i32.const 2))
    (then (return (ref.null eq)))
  )

  ;; Build result list
  (local.set $result (ref.null eq))
  (local.set $current_a (local.get $list_a))
  (local.set $current_b (local.get $list_b))
  (local.set $current_c (local.get $list_c))

  (block $done
    (loop $loop
      ;; Stop when any list is exhausted
      (br_if $done (ref.is_null (local.get $current_a)))
      (br_if $done (i32.eqz (ref.test (ref $PAIR) (local.get $current_a))))
      (br_if $done (ref.is_null (local.get $current_b)))
      (br_if $done (i32.eqz (ref.test (ref $PAIR) (local.get $current_b))))

      ;; For 3 iterables, also check third
      (if (i32.eq (local.get $num_iters) (i32.const 3))
        (then
          (br_if $done (ref.is_null (local.get $current_c)))
          (br_if $done (i32.eqz (ref.test (ref $PAIR) (local.get $current_c))))
        )
      )

      ;; Get elements
      (local.set $elem_a (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $current_a))))
      (local.set $elem_b (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $current_b))))

      ;; Create tuple based on number of iterables
      ;; All cases use $TUPLE for proper nested tuple unpacking
      (if (i32.eq (local.get $num_iters) (i32.const 2))
        (then
          ;; 2 iterables: create 2-element $TUPLE
          (local.set $tuple_data (array.new $ARRAY_ANY (ref.null eq) (i32.const 2)))
          (array.set $ARRAY_ANY (local.get $tuple_data) (i32.const 0) (local.get $elem_a))
          (array.set $ARRAY_ANY (local.get $tuple_data) (i32.const 1) (local.get $elem_b))
          (local.set $tuple (struct.new $TUPLE (local.get $tuple_data) (i32.const 2)))
        )
        (else
          ;; 3 iterables: create 3-element $TUPLE
          (local.set $elem_c (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $current_c))))
          (local.set $tuple_data (array.new $ARRAY_ANY (ref.null eq) (i32.const 3)))
          (array.set $ARRAY_ANY (local.get $tuple_data) (i32.const 0) (local.get $elem_a))
          (array.set $ARRAY_ANY (local.get $tuple_data) (i32.const 1) (local.get $elem_b))
          (array.set $ARRAY_ANY (local.get $tuple_data) (i32.const 2) (local.get $elem_c))
          (local.set $tuple (struct.new $TUPLE (local.get $tuple_data) (i32.const 3)))
        )
      )

      ;; Add to result list
      (local.set $result (struct.new $PAIR (local.get $tuple) (local.get $result)))

      ;; Advance iterators
      (local.set $current_a (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current_a))))
      (local.set $current_b (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current_b))))
      (if (i32.eq (local.get $num_iters) (i32.const 3))
        (then
          (local.set $current_c (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current_c))))
        )
      )
      (br $loop)
    )
  )

  ;; Reverse to maintain original order
  (call $list_reverse (local.get $result))
)
"""

ANY_CODE = """
;; any(iterable) - return True if any element is truthy
(func $any (param $args (ref null eq)) (param $env (ref null $ENV)) (result (ref null eq))
  (local $iterable (ref null eq))
  (local $current (ref null eq))
  (local $elem (ref null eq))
  (local $arr (ref $ARRAY_ANY))
  (local $len i32)
  (local $i i32)
  ;; Get iterable argument
  (if (ref.is_null (local.get $args))
    (then (return (struct.new $BOOL (i32.const 0))))  ;; any([]) = False
  )
  (local.set $iterable (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))

  ;; Fast path for $LIST (direct array iteration)
  (if (ref.test (ref $LIST) (local.get $iterable))
    (then
      (local.set $arr (struct.get $LIST $data (ref.cast (ref $LIST) (local.get $iterable))))
      (local.set $len (struct.get $LIST $len (ref.cast (ref $LIST) (local.get $iterable))))
      (local.set $i (i32.const 0))
      (block $list_done
        (loop $list_loop
          (br_if $list_done (i32.ge_s (local.get $i) (local.get $len)))
          (local.set $elem (array.get $ARRAY_ANY (local.get $arr) (local.get $i)))
          (if (i32.eqz (call $is_false (local.get $elem)))
            (then (return (struct.new $BOOL (i32.const 1))))
          )
          (local.set $i (i32.add (local.get $i) (i32.const 1)))
          (br $list_loop)
        )
      )
      (return (struct.new $BOOL (i32.const 0)))
    )
  )

  ;; Fast path for $TUPLE (direct array iteration)
  (if (ref.test (ref $TUPLE) (local.get $iterable))
    (then
      (local.set $arr (struct.get $TUPLE $data (ref.cast (ref $TUPLE) (local.get $iterable))))
      (local.set $len (struct.get $TUPLE $len (ref.cast (ref $TUPLE) (local.get $iterable))))
      (local.set $i (i32.const 0))
      (block $tuple_done
        (loop $tuple_loop
          (br_if $tuple_done (i32.ge_s (local.get $i) (local.get $len)))
          (local.set $elem (array.get $ARRAY_ANY (local.get $arr) (local.get $i)))
          (if (i32.eqz (call $is_false (local.get $elem)))
            (then (return (struct.new $BOOL (i32.const 1))))
          )
          (local.set $i (i32.add (local.get $i) (i32.const 1)))
          (br $tuple_loop)
        )
      )
      (return (struct.new $BOOL (i32.const 0)))
    )
  )

  ;; Slow path: Convert to PAIR chain for iteration
  (local.set $iterable (call $iter_prepare (local.get $iterable)))
  ;; Iterate and check for truthy value
  (local.set $current (local.get $iterable))
  (block $done
    (loop $loop
      (br_if $done (ref.is_null (local.get $current)))
      (if (i32.eqz (ref.test (ref $PAIR) (local.get $current)))
        (then (br $done))
      )
      ;; Get element
      (local.set $elem (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $current))))
      ;; If element is truthy, return True immediately
      (if (i32.eqz (call $is_false (local.get $elem)))
        (then (return (struct.new $BOOL (i32.const 1))))
      )
      ;; Advance to next
      (local.set $current (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current))))
      (br $loop)
    )
  )
  ;; No truthy element found
  (struct.new $BOOL (i32.const 0))
)
"""

ALL_CODE = """
;; all(iterable) - return True if all elements are truthy
(func $all (param $args (ref null eq)) (param $env (ref null $ENV)) (result (ref null eq))
  (local $iterable (ref null eq))
  (local $current (ref null eq))
  (local $elem (ref null eq))
  (local $arr (ref $ARRAY_ANY))
  (local $len i32)
  (local $i i32)
  ;; Get iterable argument
  (if (ref.is_null (local.get $args))
    (then (return (struct.new $BOOL (i32.const 1))))  ;; all([]) = True
  )
  (local.set $iterable (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))

  ;; Fast path for $LIST (direct array iteration)
  (if (ref.test (ref $LIST) (local.get $iterable))
    (then
      (local.set $arr (struct.get $LIST $data (ref.cast (ref $LIST) (local.get $iterable))))
      (local.set $len (struct.get $LIST $len (ref.cast (ref $LIST) (local.get $iterable))))
      (local.set $i (i32.const 0))
      (block $list_done
        (loop $list_loop
          (br_if $list_done (i32.ge_s (local.get $i) (local.get $len)))
          (local.set $elem (array.get $ARRAY_ANY (local.get $arr) (local.get $i)))
          (if (call $is_false (local.get $elem))
            (then (return (struct.new $BOOL (i32.const 0))))
          )
          (local.set $i (i32.add (local.get $i) (i32.const 1)))
          (br $list_loop)
        )
      )
      (return (struct.new $BOOL (i32.const 1)))
    )
  )

  ;; Fast path for $TUPLE (direct array iteration)
  (if (ref.test (ref $TUPLE) (local.get $iterable))
    (then
      (local.set $arr (struct.get $TUPLE $data (ref.cast (ref $TUPLE) (local.get $iterable))))
      (local.set $len (struct.get $TUPLE $len (ref.cast (ref $TUPLE) (local.get $iterable))))
      (local.set $i (i32.const 0))
      (block $tuple_done
        (loop $tuple_loop
          (br_if $tuple_done (i32.ge_s (local.get $i) (local.get $len)))
          (local.set $elem (array.get $ARRAY_ANY (local.get $arr) (local.get $i)))
          (if (call $is_false (local.get $elem))
            (then (return (struct.new $BOOL (i32.const 0))))
          )
          (local.set $i (i32.add (local.get $i) (i32.const 1)))
          (br $tuple_loop)
        )
      )
      (return (struct.new $BOOL (i32.const 1)))
    )
  )

  ;; Slow path: Convert to PAIR chain for iteration
  (local.set $iterable (call $iter_prepare (local.get $iterable)))
  ;; Iterate and check for falsy value
  (local.set $current (local.get $iterable))
  (block $done
    (loop $loop
      (br_if $done (ref.is_null (local.get $current)))
      (if (i32.eqz (ref.test (ref $PAIR) (local.get $current)))
        (then (br $done))
      )
      ;; Get element
      (local.set $elem (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $current))))
      ;; If element is falsy, return False immediately
      (if (call $is_false (local.get $elem))
        (then (return (struct.new $BOOL (i32.const 0))))
      )
      ;; Advance to next
      (local.set $current (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current))))
      (br $loop)
    )
  )
  ;; All elements were truthy
  (struct.new $BOOL (i32.const 1))
)
"""

REVERSED_CODE = """
;; reversed(seq) - return reversed list
(func $reversed (param $args (ref null eq)) (param $env (ref null $ENV)) (result (ref null eq))
  (local $seq (ref null eq))
  ;; Get argument
  (if (ref.is_null (local.get $args))
    (then (return (struct.new $EMPTY_LIST)))
  )
  (local.set $seq (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))
  ;; Handle empty list
  (if (i32.or (ref.is_null (local.get $seq)) (ref.test (ref $EMPTY_LIST) (local.get $seq)))
    (then (return (struct.new $EMPTY_LIST)))
  )
  ;; Handle TUPLE - reverse and return as list
  (if (ref.test (ref $TUPLE) (local.get $seq))
    (then (return (call $tuple_reversed (ref.cast (ref $TUPLE) (local.get $seq)))))
  )
  ;; Handle LIST (array-backed)
  (if (ref.test (ref $LIST) (local.get $seq))
    (then (return (call $list_v2_reversed (ref.cast (ref $LIST) (local.get $seq)))))
  )
  ;; Handle STRING - convert to char list (already reversed by string_to_chars building)
  (if (ref.test (ref $STRING) (local.get $seq))
    (then (return (call $string_to_chars_reversed (ref.cast (ref $STRING) (local.get $seq)))))
  )
  ;; Handle PAIR chain
  (call $list_reverse (local.get $seq))
)

;; Helper: reverse a tuple, return as PAIR chain
(func $tuple_reversed (param $t (ref $TUPLE)) (result (ref null eq))
  (local $arr (ref $ARRAY_ANY))
  (local $len i32)
  (local $i i32)
  (local $result (ref null eq))
  (local.set $arr (struct.get $TUPLE $data (local.get $t)))
  (local.set $len (struct.get $TUPLE $len (local.get $t)))
  (if (i32.eqz (local.get $len))
    (then (return (struct.new $EMPTY_LIST)))
  )
  (local.set $result (ref.null eq))
  (local.set $i (i32.const 0))
  (block $done
    (loop $loop
      (br_if $done (i32.ge_s (local.get $i) (local.get $len)))
      (local.set $result (struct.new $PAIR
        (array.get $ARRAY_ANY (local.get $arr) (local.get $i))
        (local.get $result)))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $loop)
    )
  )
  (local.get $result)
)

;; Helper: reverse array-backed list, return as PAIR chain
(func $list_v2_reversed (param $lst (ref $LIST)) (result (ref null eq))
  (local $arr (ref $ARRAY_ANY))
  (local $len i32)
  (local $i i32)
  (local $result (ref null eq))
  (local.set $arr (struct.get $LIST $data (local.get $lst)))
  (local.set $len (struct.get $LIST $len (local.get $lst)))
  (if (i32.eqz (local.get $len))
    (then (return (struct.new $EMPTY_LIST)))
  )
  (local.set $result (ref.null eq))
  (local.set $i (i32.const 0))
  (block $done
    (loop $loop
      (br_if $done (i32.ge_s (local.get $i) (local.get $len)))
      (local.set $result (struct.new $PAIR
        (array.get $ARRAY_ANY (local.get $arr) (local.get $i))
        (local.get $result)))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $loop)
    )
  )
  (local.get $result)
)
"""

NEXT_CODE = """
;; next(iterator[, default]) - get next item from iterator
;; For generators, calls generator_next
;; If default provided and StopIteration occurs, returns default
(func $next (param $args (ref null eq)) (param $env (ref null $ENV)) (result (ref null eq))
  (local $iter (ref null eq))
  (local $default (ref null eq))
  (local $has_default i32)
  (local $result (ref null eq))

  ;; Get iterator (first argument)
  (if (ref.is_null (local.get $args))
    (then
      ;; No argument - return None
      (return (ref.null eq))
    )
  )
  (local.set $iter (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))

  ;; Check for optional default (second argument)
  (local.set $default (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $args))))
  (if (ref.is_null (local.get $default))
    (then
      (local.set $has_default (i32.const 0))
    )
    (else
      (local.set $has_default (i32.const 1))
      (local.set $default (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $default))))
    )
  )

  ;; Check if it's a generator
  (if (ref.test (ref $GENERATOR) (local.get $iter))
    (then
      ;; For generators, try to get next value
      (if (local.get $has_default)
        (then
          ;; With default: catch StopIteration and return default
          (block $stop
            (local.set $result
              (try_table (result (ref null eq)) (catch $StopIteration $stop)
                (call $generator_next (local.get $iter))
              )
            )
            (return (local.get $result))
          )
          ;; StopIteration caught - return default
          (return (local.get $default))
        )
        (else
          ;; Without default: let StopIteration propagate
          (return (call $generator_next (local.get $iter)))
        )
      )
    )
  )

  ;; For non-generators, just throw StopIteration (not fully supported)
  (throw $StopIteration)
)
"""

# Combined code for this module
SEQUENCES_CODE = (
    LEN_CODE
    + MIN_CODE
    + MAX_CODE
    + SUM_CODE
    + RANGE_BUILTIN_CODE
    + MAP_CODE
    + FILTER_CODE
    + SORTED_CODE
    + ENUMERATE_CODE
    + ZIP_CODE
    + ANY_CODE
    + ALL_CODE
    + REVERSED_CODE
    + NEXT_CODE
)
