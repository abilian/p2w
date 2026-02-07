"""WAT builtin functions: Math functions (abs, round, pow, etc.)."""

from __future__ import annotations

ABS_CODE = """
(func $abs (param $args (ref null eq)) (param $env (ref null $ENV)) (result (ref null eq))
  (local $val i32)
  (local $fval f64)
  (local $arg (ref null eq))
  (if (ref.is_null (local.get $args))
    (then (return (ref.i31 (i32.const 0))))
  )
  (local.set $arg (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))
  ;; Check if it's a float
  (if (ref.test (ref $FLOAT) (local.get $arg))
    (then
      (local.set $fval (struct.get $FLOAT 0 (ref.cast (ref $FLOAT) (local.get $arg))))
      (return (struct.new $FLOAT (f64.abs (local.get $fval))))
    )
  )
  ;; Integer case
  (local.set $val (i31.get_s (ref.cast (ref i31) (local.get $arg))))
  (if (result (ref null eq)) (i32.lt_s (local.get $val) (i32.const 0))
    (then (ref.i31 (i32.sub (i32.const 0) (local.get $val))))
    (else (ref.i31 (local.get $val)))
  )
)
"""

ROUND_CODE = """
;; round(x, ndigits=None) - round number
;; Returns int if input is int, float if input is float (Python behavior)
(func $round (param $args (ref null eq)) (param $env (ref null $ENV)) (result (ref null eq))
  (local $val (ref null eq))
  (local $arg2 (ref null eq))
  (local $f f64)
  (local $ndigits i32)
  (local $multiplier f64)
  (local $i i32)
  (local $result i32)
  (local $input_is_int i32)
  ;; Get argument
  (if (ref.is_null (local.get $args))
    (then (return (ref.i31 (i32.const 0))))
  )
  (local.set $val (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))
  ;; Check for ndigits argument
  (local.set $arg2 (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $args))))
  (if (ref.is_null (local.get $arg2))
    (then
      ;; No ndigits - round to integer
      ;; Handle integer - already rounded
      (if (ref.test (ref i31) (local.get $val))
        (then (return (local.get $val)))
      )
      ;; Handle float - use f64.nearest for banker's rounding
      (if (ref.test (ref $FLOAT) (local.get $val))
        (then
          (local.set $f (struct.get $FLOAT 0 (ref.cast (ref $FLOAT) (local.get $val))))
          (local.set $result (i32.trunc_f64_s (f64.nearest (local.get $f))))
          (return (ref.i31 (local.get $result)))
        )
      )
      (return (ref.i31 (i32.const 0)))
    )
  )
  ;; ndigits provided - round to that many decimal places
  (local.set $ndigits (i31.get_s (ref.cast (ref i31)
    (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $arg2))))))
  ;; Track if input is integer (affects return type)
  (local.set $input_is_int (i32.const 0))
  ;; Get the float value
  (if (ref.test (ref i31) (local.get $val))
    (then
      (local.set $f (f64.convert_i32_s (i31.get_s (ref.cast (ref i31) (local.get $val)))))
      (local.set $input_is_int (i32.const 1))
    )
    (else
      (if (ref.test (ref $FLOAT) (local.get $val))
        (then (local.set $f (struct.get $FLOAT 0 (ref.cast (ref $FLOAT) (local.get $val)))))
        (else (local.set $f (f64.const 0)))
      )
    )
  )
  ;; Compute multiplier = 10^ndigits
  (local.set $multiplier (f64.const 1.0))
  (local.set $i (i32.const 0))
  (if (i32.gt_s (local.get $ndigits) (i32.const 0))
    (then
      (block $done
        (loop $loop
          (br_if $done (i32.ge_s (local.get $i) (local.get $ndigits)))
          (local.set $multiplier (f64.mul (local.get $multiplier) (f64.const 10.0)))
          (local.set $i (i32.add (local.get $i) (i32.const 1)))
          (br $loop)
        )
      )
    )
    (else
      ;; Negative ndigits: divide multiplier
      (local.set $i (local.get $ndigits))
      (block $done
        (loop $loop
          (br_if $done (i32.ge_s (local.get $i) (i32.const 0)))
          (local.set $multiplier (f64.div (local.get $multiplier) (f64.const 10.0)))
          (local.set $i (i32.add (local.get $i) (i32.const 1)))
          (br $loop)
        )
      )
    )
  )
  ;; round(x * multiplier) / multiplier
  (local.set $f (f64.div (f64.nearest (f64.mul (local.get $f) (local.get $multiplier))) (local.get $multiplier)))
  ;; Return int if input was int, float otherwise
  (if (result (ref null eq)) (local.get $input_is_int)
    (then (ref.i31 (i32.trunc_f64_s (local.get $f))))
    (else (struct.new $FLOAT (local.get $f)))
  )
)
"""

POW_CODE = """
;; pow(base, exp, mod=None) - power function
(func $pow (param $args (ref null eq)) (param $env (ref null $ENV)) (result (ref null eq))
  (local $base (ref null eq))
  (local $exp (ref null eq))
  (local $mod (ref null eq))
  (local $base_i i64)
  (local $exp_i i64)
  (local $mod_i i64)
  (local $result i64)
  (local $arg2 (ref null eq))
  (local $arg3 (ref null eq))
  (local $base_f f64)
  (local $exp_f f64)
  ;; Get arguments
  (if (ref.is_null (local.get $args))
    (then (return (ref.i31 (i32.const 1))))
  )
  (local.set $base (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))
  (local.set $arg2 (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $args))))
  (if (ref.is_null (local.get $arg2))
    (then (return (local.get $base)))
  )
  (local.set $exp (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $arg2))))
  (local.set $arg3 (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $arg2))))
  (if (i32.eqz (ref.is_null (local.get $arg3)))
    (then
      (local.set $mod (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $arg3))))
    )
  )
  ;; Check if base or exp is float - use f64.pow
  (if (i32.or (ref.test (ref $FLOAT) (local.get $base)) (ref.test (ref $FLOAT) (local.get $exp)))
    (then
      ;; Float power
      (if (ref.test (ref $FLOAT) (local.get $base))
        (then (local.set $base_f (struct.get $FLOAT 0 (ref.cast (ref $FLOAT) (local.get $base)))))
        (else (local.set $base_f (f64.convert_i32_s (i31.get_s (ref.cast (ref i31) (local.get $base))))))
      )
      (if (ref.test (ref $FLOAT) (local.get $exp))
        (then (local.set $exp_f (struct.get $FLOAT 0 (ref.cast (ref $FLOAT) (local.get $exp)))))
        (else (local.set $exp_f (f64.convert_i32_s (i31.get_s (ref.cast (ref i31) (local.get $exp))))))
      )
      (return (struct.new $FLOAT (call $f64_pow (local.get $base_f) (local.get $exp_f))))
    )
  )
  ;; Integer power
  (local.set $base_i (i64.extend_i32_s (i31.get_s (ref.cast (ref i31) (local.get $base)))))
  (local.set $exp_i (i64.extend_i32_s (i31.get_s (ref.cast (ref i31) (local.get $exp)))))
  (local.set $result (i64.const 1))
  (block $done
    (loop $loop
      (br_if $done (i64.le_s (local.get $exp_i) (i64.const 0)))
      (if (i32.wrap_i64 (i64.and (local.get $exp_i) (i64.const 1)))
        (then (local.set $result (i64.mul (local.get $result) (local.get $base_i))))
      )
      (local.set $base_i (i64.mul (local.get $base_i) (local.get $base_i)))
      (local.set $exp_i (i64.shr_u (local.get $exp_i) (i64.const 1)))
      (br $loop)
    )
  )
  ;; Apply mod if provided
  (if (i32.eqz (ref.is_null (local.get $mod)))
    (then
      (local.set $mod_i (i64.extend_i32_s (i31.get_s (ref.cast (ref i31) (local.get $mod)))))
      (local.set $result (i64.rem_s (local.get $result) (local.get $mod_i)))
    )
  )
  (ref.i31 (i32.wrap_i64 (local.get $result)))
)

;; f64_pow helper: compute a^b using exp and log
(func $f64_pow (param $a f64) (param $b f64) (result f64)
  (local $result f64)
  (local $exp_i i32)
  (local $is_neg i32)
  ;; Special cases
  (if (f64.eq (local.get $b) (f64.const 0.0))
    (then (return (f64.const 1.0)))
  )
  (if (f64.eq (local.get $a) (f64.const 0.0))
    (then (return (f64.const 0.0)))
  )
  (if (f64.eq (local.get $a) (f64.const 1.0))
    (then (return (f64.const 1.0)))
  )
  ;; Check if exponent is integer
  (if (f64.eq (f64.trunc (local.get $b)) (local.get $b))
    (then
      ;; Integer exponent - use repeated multiplication
      (local.set $is_neg (f64.lt (local.get $b) (f64.const 0.0)))
      (local.set $exp_i (i32.trunc_f64_s (f64.abs (local.get $b))))
      (local.set $result (f64.const 1.0))
      (block $done
        (loop $loop
          (br_if $done (i32.le_s (local.get $exp_i) (i32.const 0)))
          (if (i32.and (local.get $exp_i) (i32.const 1))
            (then (local.set $result (f64.mul (local.get $result) (local.get $a))))
          )
          (local.set $a (f64.mul (local.get $a) (local.get $a)))
          (local.set $exp_i (i32.shr_u (local.get $exp_i) (i32.const 1)))
          (br $loop)
        )
      )
      (if (local.get $is_neg)
        (then (local.set $result (f64.div (f64.const 1.0) (local.get $result))))
      )
      (return (local.get $result))
    )
  )
  ;; Non-integer exponent: use imported Math.pow from JavaScript
  (call $math_pow (local.get $a) (local.get $b))
)
"""

DIVMOD_CODE = """
;; divmod(a, b) - returns (quotient, remainder) as tuple
(func $divmod (param $args (ref null eq)) (param $env (ref null $ENV)) (result (ref null eq))
  (local $a (ref null eq))
  (local $b (ref null eq))
  (local $arg2 (ref null eq))
  (local $a_i i32)
  (local $b_i i32)
  (local $quot i32)
  (local $rem i32)
  ;; Get arguments
  (if (ref.is_null (local.get $args))
    (then (return (ref.null eq)))
  )
  (local.set $a (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))
  (local.set $arg2 (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $args))))
  (if (ref.is_null (local.get $arg2))
    (then (return (ref.null eq)))
  )
  (local.set $b (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $arg2))))
  ;; Get integer values
  (local.set $a_i (i31.get_s (ref.cast (ref i31) (local.get $a))))
  (local.set $b_i (i31.get_s (ref.cast (ref i31) (local.get $b))))
  ;; Compute quotient and remainder (Python semantics: floor division)
  (local.set $quot (i32.div_s (local.get $a_i) (local.get $b_i)))
  (local.set $rem (i32.rem_s (local.get $a_i) (local.get $b_i)))
  ;; Adjust for Python floor division semantics
  (if (i32.and
        (i32.ne (local.get $rem) (i32.const 0))
        (i32.xor (i32.lt_s (local.get $a_i) (i32.const 0))
                 (i32.lt_s (local.get $b_i) (i32.const 0))))
    (then
      (local.set $quot (i32.sub (local.get $quot) (i32.const 1)))
      (local.set $rem (i32.add (local.get $rem) (local.get $b_i)))
    )
  )
  ;; Return tuple (quotient, remainder)
  (struct.new $TUPLE
    (array.new_fixed $ARRAY_ANY 2
      (ref.i31 (local.get $quot))
      (ref.i31 (local.get $rem)))
    (i32.const 2))
)
"""

# Combined code for this module
MATH_CODE = ABS_CODE + ROUND_CODE + POW_CODE + DIVMOD_CODE
