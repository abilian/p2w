"""WAT helper functions: Arithmetic dispatch functions."""

from __future__ import annotations

ARITHMETIC_CODE = """

;; add_dispatch: runtime-dispatch add operation (handles int, float, string, list, tuple)
(func $add_dispatch (param $a (ref null eq)) (param $b (ref null eq)) (result (ref null eq))
  (local $fa f64)
  (local $fb f64)

  ;; Check if both are tuples
  (if (i32.and
        (ref.test (ref $TUPLE) (local.get $a))
        (ref.test (ref $TUPLE) (local.get $b)))
    (then
      (return (call $tuple_concat (local.get $a) (local.get $b)))
    )
  )
  ;; Check if both are lists (PAIRs)
  (if (i32.and
        (ref.test (ref $PAIR) (local.get $a))
        (ref.test (ref $PAIR) (local.get $b)))
    (then
      (return (call $list_concat (local.get $a) (local.get $b)))
    )
  )
  ;; Check if either is a list (PAIR) - list + something or something + list
  (if (ref.test (ref $PAIR) (local.get $a))
    (then
      (return (call $list_concat (local.get $a) (local.get $b)))
    )
  )
  (if (ref.test (ref $PAIR) (local.get $b))
    (then
      (return (call $list_concat (local.get $a) (local.get $b)))
    )
  )
  ;; Check if both are strings
  (if (i32.and
        (ref.test (ref $STRING) (local.get $a))
        (ref.test (ref $STRING) (local.get $b)))
    (then
      (return (call $string_concat
        (ref.cast (ref $STRING) (local.get $a))
        (ref.cast (ref $STRING) (local.get $b))))
    )
  )
  ;; Check if both are floats
  (if (i32.and
        (ref.test (ref $FLOAT) (local.get $a))
        (ref.test (ref $FLOAT) (local.get $b)))
    (then
      (return (struct.new $FLOAT (f64.add
        (struct.get $FLOAT 0 (ref.cast (ref $FLOAT) (local.get $a)))
        (struct.get $FLOAT 0 (ref.cast (ref $FLOAT) (local.get $b))))))
    )
  )
  ;; Check if both are integers (i31 or INT64)
  (if (i32.and (call $is_integer (local.get $a)) (call $is_integer (local.get $b)))
    (then
      (return (call $int_add (local.get $a) (local.get $b)))
    )
  )
  ;; Mixed int/float - convert to float
  (if (ref.test (ref i31) (local.get $a))
    (then (local.set $fa (f64.convert_i32_s (i31.get_s (ref.cast (ref i31) (local.get $a))))))
    (else
      (if (ref.test (ref $INT64) (local.get $a))
        (then (local.set $fa (f64.convert_i64_s (struct.get $INT64 0 (ref.cast (ref $INT64) (local.get $a))))))
        (else
          (if (ref.test (ref $FLOAT) (local.get $a))
            (then (local.set $fa (struct.get $FLOAT 0 (ref.cast (ref $FLOAT) (local.get $a)))))
            (else (return (ref.null eq)))
          )
        )
      )
    )
  )
  (if (ref.test (ref i31) (local.get $b))
    (then (local.set $fb (f64.convert_i32_s (i31.get_s (ref.cast (ref i31) (local.get $b))))))
    (else
      (if (ref.test (ref $INT64) (local.get $b))
        (then (local.set $fb (f64.convert_i64_s (struct.get $INT64 0 (ref.cast (ref $INT64) (local.get $b))))))
        (else
          (if (ref.test (ref $FLOAT) (local.get $b))
            (then (local.set $fb (struct.get $FLOAT 0 (ref.cast (ref $FLOAT) (local.get $b)))))
            (else (return (ref.null eq)))
          )
        )
      )
    )
  )
  (struct.new $FLOAT (f64.add (local.get $fa) (local.get $fb)))
)


;; mult_dispatch: runtime-dispatch multiply operation
(func $mult_dispatch (param $a (ref null eq)) (param $b (ref null eq)) (result (ref null eq))
  (local $fa f64)
  (local $fb f64)

  ;; Check if left is a tuple
  (if (ref.test (ref $TUPLE) (local.get $a))
    (then
      (return (call $tuple_repeat (local.get $a) (local.get $b)))
    )
  )
  ;; Check if left is a list (PAIR)
  (if (ref.test (ref $PAIR) (local.get $a))
    (then
      (return (call $list_repeat (local.get $a) (local.get $b)))
    )
  )
  ;; Check if left is a string
  (if (ref.test (ref $STRING) (local.get $a))
    (then
      (return (call $string_repeat (local.get $a) (local.get $b)))
    )
  )
  ;; Check if both are floats
  (if (i32.and
        (ref.test (ref $FLOAT) (local.get $a))
        (ref.test (ref $FLOAT) (local.get $b)))
    (then
      (return (struct.new $FLOAT (f64.mul
        (struct.get $FLOAT 0 (ref.cast (ref $FLOAT) (local.get $a)))
        (struct.get $FLOAT 0 (ref.cast (ref $FLOAT) (local.get $b))))))
    )
  )
  ;; Check if both are integers (i31 or INT64)
  (if (i32.and (call $is_integer (local.get $a)) (call $is_integer (local.get $b)))
    (then
      (return (call $int_mul (local.get $a) (local.get $b)))
    )
  )
  ;; Mixed int/float - convert to float
  (if (ref.test (ref i31) (local.get $a))
    (then (local.set $fa (f64.convert_i32_s (i31.get_s (ref.cast (ref i31) (local.get $a))))))
    (else
      (if (ref.test (ref $INT64) (local.get $a))
        (then (local.set $fa (f64.convert_i64_s (struct.get $INT64 0 (ref.cast (ref $INT64) (local.get $a))))))
        (else
          (if (ref.test (ref $FLOAT) (local.get $a))
            (then (local.set $fa (struct.get $FLOAT 0 (ref.cast (ref $FLOAT) (local.get $a)))))
            (else (return (ref.null eq)))
          )
        )
      )
    )
  )
  (if (ref.test (ref i31) (local.get $b))
    (then (local.set $fb (f64.convert_i32_s (i31.get_s (ref.cast (ref i31) (local.get $b))))))
    (else
      (if (ref.test (ref $INT64) (local.get $b))
        (then (local.set $fb (f64.convert_i64_s (struct.get $INT64 0 (ref.cast (ref $INT64) (local.get $b))))))
        (else
          (if (ref.test (ref $FLOAT) (local.get $b))
            (then (local.set $fb (struct.get $FLOAT 0 (ref.cast (ref $FLOAT) (local.get $b)))))
            (else (return (ref.null eq)))
          )
        )
      )
    )
  )
  (struct.new $FLOAT (f64.mul (local.get $fa) (local.get $fb)))
)


;; sub_dispatch: runtime-dispatch subtraction operation
(func $sub_dispatch (param $a (ref null eq)) (param $b (ref null eq)) (result (ref null eq))
  (local $fa f64)
  (local $fb f64)

  ;; Check if both are floats
  (if (i32.and
        (ref.test (ref $FLOAT) (local.get $a))
        (ref.test (ref $FLOAT) (local.get $b)))
    (then
      (return (struct.new $FLOAT (f64.sub
        (struct.get $FLOAT 0 (ref.cast (ref $FLOAT) (local.get $a)))
        (struct.get $FLOAT 0 (ref.cast (ref $FLOAT) (local.get $b))))))
    )
  )
  ;; Check if both are integers (i31 or INT64)
  (if (i32.and (call $is_integer (local.get $a)) (call $is_integer (local.get $b)))
    (then
      (return (call $int_sub (local.get $a) (local.get $b)))
    )
  )
  ;; Mixed int/float - convert to float
  (if (ref.test (ref i31) (local.get $a))
    (then (local.set $fa (f64.convert_i32_s (i31.get_s (ref.cast (ref i31) (local.get $a))))))
    (else
      (if (ref.test (ref $INT64) (local.get $a))
        (then (local.set $fa (f64.convert_i64_s (struct.get $INT64 0 (ref.cast (ref $INT64) (local.get $a))))))
        (else
          (if (ref.test (ref $FLOAT) (local.get $a))
            (then (local.set $fa (struct.get $FLOAT 0 (ref.cast (ref $FLOAT) (local.get $a)))))
            (else (return (ref.null eq)))
          )
        )
      )
    )
  )
  (if (ref.test (ref i31) (local.get $b))
    (then (local.set $fb (f64.convert_i32_s (i31.get_s (ref.cast (ref i31) (local.get $b))))))
    (else
      (if (ref.test (ref $INT64) (local.get $b))
        (then (local.set $fb (f64.convert_i64_s (struct.get $INT64 0 (ref.cast (ref $INT64) (local.get $b))))))
        (else
          (if (ref.test (ref $FLOAT) (local.get $b))
            (then (local.set $fb (struct.get $FLOAT 0 (ref.cast (ref $FLOAT) (local.get $b)))))
            (else (return (ref.null eq)))
          )
        )
      )
    )
  )
  (struct.new $FLOAT (f64.sub (local.get $fa) (local.get $fb)))
)


;; div_dispatch: runtime-dispatch division operation (true division, returns float)
(func $div_dispatch (param $a (ref null eq)) (param $b (ref null eq)) (result (ref null eq))
  (local $fa f64)
  (local $fb f64)

  ;; Check if both are floats
  (if (i32.and
        (ref.test (ref $FLOAT) (local.get $a))
        (ref.test (ref $FLOAT) (local.get $b)))
    (then
      (return (struct.new $FLOAT (f64.div
        (struct.get $FLOAT 0 (ref.cast (ref $FLOAT) (local.get $a)))
        (struct.get $FLOAT 0 (ref.cast (ref $FLOAT) (local.get $b))))))
    )
  )
  ;; Convert a to float
  (if (ref.test (ref i31) (local.get $a))
    (then (local.set $fa (f64.convert_i32_s (i31.get_s (ref.cast (ref i31) (local.get $a))))))
    (else
      (if (ref.test (ref $FLOAT) (local.get $a))
        (then (local.set $fa (struct.get $FLOAT 0 (ref.cast (ref $FLOAT) (local.get $a)))))
        (else
          (if (ref.test (ref $INT64) (local.get $a))
            (then (local.set $fa (f64.convert_i64_s (struct.get $INT64 0 (ref.cast (ref $INT64) (local.get $a))))))
            (else (return (ref.null eq)))
          )
        )
      )
    )
  )
  ;; Convert b to float
  (if (ref.test (ref i31) (local.get $b))
    (then (local.set $fb (f64.convert_i32_s (i31.get_s (ref.cast (ref i31) (local.get $b))))))
    (else
      (if (ref.test (ref $FLOAT) (local.get $b))
        (then (local.set $fb (struct.get $FLOAT 0 (ref.cast (ref $FLOAT) (local.get $b)))))
        (else
          (if (ref.test (ref $INT64) (local.get $b))
            (then (local.set $fb (f64.convert_i64_s (struct.get $INT64 0 (ref.cast (ref $INT64) (local.get $b))))))
            (else (return (ref.null eq)))
          )
        )
      )
    )
  )
  (struct.new $FLOAT (f64.div (local.get $fa) (local.get $fb)))
)


;; floordiv_dispatch: runtime-dispatch floor division (returns integer)
(func $floordiv_dispatch (param $a (ref null eq)) (param $b (ref null eq)) (result (ref null eq))
  ;; Integer floor division (handles both i31 and INT64)
  (if (i32.and (call $is_integer (local.get $a)) (call $is_integer (local.get $b)))
    (then
      (return (call $int_div (local.get $a) (local.get $b)))
    )
  )
  ;; For floats, compute floor(a/b)
  (if (i32.or
        (ref.test (ref $FLOAT) (local.get $a))
        (ref.test (ref $FLOAT) (local.get $b)))
    (then
      ;; Convert both to float and do floor division
      (return (struct.new $FLOAT (f64.floor (f64.div
        (call $to_f64 (local.get $a))
        (call $to_f64 (local.get $b))))))
    )
  )
  (ref.null eq)
)


;; mod_dispatch: runtime-dispatch modulo operation
(func $mod_dispatch (param $a (ref null eq)) (param $b (ref null eq)) (result (ref null eq))
  ;; Integer modulo (handles both i31 and INT64)
  (if (i32.and (call $is_integer (local.get $a)) (call $is_integer (local.get $b)))
    (then
      (return (call $int_mod (local.get $a) (local.get $b)))
    )
  )
  ;; For floats, compute Python-style modulo
  (if (i32.or
        (ref.test (ref $FLOAT) (local.get $a))
        (ref.test (ref $FLOAT) (local.get $b)))
    (then
      ;; Python-style: a - floor(a/b) * b
      (return (struct.new $FLOAT (f64.sub
        (call $to_f64 (local.get $a))
        (f64.mul
          (f64.floor (f64.div (call $to_f64 (local.get $a)) (call $to_f64 (local.get $b))))
          (call $to_f64 (local.get $b))))))
    )
  )
  (ref.null eq)
)


;; int_pow: integer power operation (returns int for int operands)
(func $int_pow (param $a (ref null eq)) (param $b (ref null eq)) (result (ref null eq))
  (local $base i64)
  (local $exp i64)
  (local $result i64)
  ;; Check if both are integers (i31 or INT64)
  (if (i32.and (call $is_integer (local.get $a)) (call $is_integer (local.get $b)))
    (then
      ;; Both integers - compute integer power
      (local.set $base (call $to_i64 (local.get $a)))
      (local.set $exp (call $to_i64 (local.get $b)))
      ;; Check for negative exponent - return float
      (if (i64.lt_s (local.get $exp) (i64.const 0))
        (then
          (return (struct.new $FLOAT (call $f64_pow
            (f64.convert_i64_s (local.get $base))
            (f64.convert_i64_s (local.get $exp)))))
        )
      )
      ;; Positive exponent - compute integer result
      (local.set $result (i64.const 1))
      (block $done
        (loop $loop
          (br_if $done (i64.le_s (local.get $exp) (i64.const 0)))
          (if (i32.wrap_i64 (i64.and (local.get $exp) (i64.const 1)))
            (then (local.set $result (i64.mul (local.get $result) (local.get $base))))
          )
          (local.set $base (i64.mul (local.get $base) (local.get $base)))
          (local.set $exp (i64.shr_u (local.get $exp) (i64.const 1)))
          (br $loop)
        )
      )
      (return (call $pack_int (local.get $result)))
    )
  )
  ;; Not both integers - use float power
  (struct.new $FLOAT (call $f64_pow (call $to_f64 (local.get $a)) (call $to_f64 (local.get $b))))
)

;; pow_dispatch: runtime-dispatch power operation (alias for int_pow)
(func $pow_dispatch (param $a (ref null eq)) (param $b (ref null eq)) (result (ref null eq))
  (call $int_pow (local.get $a) (local.get $b))
)


;; matmul_dispatch: runtime-dispatch matrix multiplication (@ operator)
;; Calls __matmul__ on the left operand, or __rmatmul__ on the right if not found
(func $matmul_dispatch (param $a (ref null eq)) (param $b (ref null eq)) (result (ref null eq))
  (local $result (ref null eq))
  (local $method (ref null eq))
  (local $args (ref null eq))

  ;; Check if left operand is an OBJECT
  (if (ref.test (ref $OBJECT) (local.get $a))
    (then
      ;; Build args list: (self, other, null) = (a, b, null)
      (local.set $args (struct.new $PAIR (local.get $a)
        (struct.new $PAIR (local.get $b) (ref.null eq))))
      ;; Call __matmul__ method
      (local.set $result (call $object_call_method
        (local.get $a)
        (call $make_string_matmul)
        (local.get $args)
        (ref.null $ENV)))
      (if (i32.eqz (ref.is_null (local.get $result)))
        (then (return (local.get $result)))
      )
    )
  )

  ;; Try __rmatmul__ on right operand
  (if (ref.test (ref $OBJECT) (local.get $b))
    (then
      ;; Build args list: (self, other, null) = (b, a, null)
      (local.set $args (struct.new $PAIR (local.get $b)
        (struct.new $PAIR (local.get $a) (ref.null eq))))
      ;; Call __rmatmul__ method
      (local.set $result (call $object_call_method
        (local.get $b)
        (call $make_string_rmatmul)
        (local.get $args)
        (ref.null $ENV)))
      (return (local.get $result))
    )
  )

  ;; Unsupported operand types
  (ref.null eq)
)

"""
