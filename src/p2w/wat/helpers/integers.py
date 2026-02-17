"""WAT helper functions: Integer arithmetic operations."""

from __future__ import annotations

INTEGERS_CODE = """

;; =============================================================================
;; Native i32/i64 Python-style floor division and modulo
;; =============================================================================

;; i32_floordiv: Python-style floor division for i32
;; Python's // rounds toward negative infinity, WASM's div_s truncates toward zero
(func $i32_floordiv (param $a i32) (param $b i32) (result i32)
  (local $q i32)
  (local $r i32)
  (local.set $q (i32.div_s (local.get $a) (local.get $b)))
  (local.set $r (i32.rem_s (local.get $a) (local.get $b)))
  ;; If remainder is non-zero and signs of a and b differ, subtract 1
  (if (result i32) (i32.and
        (i32.ne (local.get $r) (i32.const 0))
        (i32.lt_s (i32.xor (local.get $a) (local.get $b)) (i32.const 0)))
    (then (i32.sub (local.get $q) (i32.const 1)))
    (else (local.get $q))
  )
)

;; i32_mod: Python-style modulo for i32
;; Python's % has the sign of the divisor, WASM's rem_s has the sign of the dividend
(func $i32_mod (param $a i32) (param $b i32) (result i32)
  (local $r i32)
  (local.set $r (i32.rem_s (local.get $a) (local.get $b)))
  ;; If remainder is non-zero and signs of r and b differ, add b
  (if (result i32) (i32.and
        (i32.ne (local.get $r) (i32.const 0))
        (i32.lt_s (i32.xor (local.get $r) (local.get $b)) (i32.const 0)))
    (then (i32.add (local.get $r) (local.get $b)))
    (else (local.get $r))
  )
)

;; i64_floordiv: Python-style floor division for i64
(func $i64_floordiv (param $a i64) (param $b i64) (result i64)
  (local $q i64)
  (local $r i64)
  (local.set $q (i64.div_s (local.get $a) (local.get $b)))
  (local.set $r (i64.rem_s (local.get $a) (local.get $b)))
  ;; If remainder is non-zero and signs of a and b differ, subtract 1
  (if (result i64) (i32.and
        (i64.ne (local.get $r) (i64.const 0))
        (i64.lt_s (i64.xor (local.get $a) (local.get $b)) (i64.const 0)))
    (then (i64.sub (local.get $q) (i64.const 1)))
    (else (local.get $q))
  )
)

;; i64_mod: Python-style modulo for i64
(func $i64_mod (param $a i64) (param $b i64) (result i64)
  (local $r i64)
  (local.set $r (i64.rem_s (local.get $a) (local.get $b)))
  ;; If remainder is non-zero and signs of r and b differ, add b
  (if (result i64) (i32.and
        (i64.ne (local.get $r) (i64.const 0))
        (i64.lt_s (i64.xor (local.get $r) (local.get $b)) (i64.const 0)))
    (then (i64.add (local.get $r) (local.get $b)))
    (else (local.get $r))
  )
)

;; =============================================================================
;; Boxed integer operations
;; =============================================================================

;; int_add: safe integer addition with overflow promotion
(func $int_add (param $a (ref null eq)) (param $b (ref null eq)) (result (ref null eq))
  (call $pack_int (i64.add (call $to_i64 (local.get $a)) (call $to_i64 (local.get $b))))
)


;; int_sub: safe integer subtraction with overflow promotion
(func $int_sub (param $a (ref null eq)) (param $b (ref null eq)) (result (ref null eq))
  (call $pack_int (i64.sub (call $to_i64 (local.get $a)) (call $to_i64 (local.get $b))))
)


;; int_mul: safe integer multiplication with overflow promotion
(func $int_mul (param $a (ref null eq)) (param $b (ref null eq)) (result (ref null eq))
  (call $pack_int (i64.mul (call $to_i64 (local.get $a)) (call $to_i64 (local.get $b))))
)


;; int_div: integer division (floor division for negative numbers)
(func $int_div (param $a (ref null eq)) (param $b (ref null eq)) (result (ref null eq))
  (call $pack_int (call $i64_floordiv (call $to_i64 (local.get $a)) (call $to_i64 (local.get $b))))
)


;; int_mod: integer modulo (matches Python semantics)
(func $int_mod (param $a (ref null eq)) (param $b (ref null eq)) (result (ref null eq))
  (call $pack_int (call $i64_mod (call $to_i64 (local.get $a)) (call $to_i64 (local.get $b))))
)


;; int_neg: integer negation
(func $int_neg (param $a (ref null eq)) (result (ref null eq))
  (call $pack_int (i64.sub (i64.const 0) (call $to_i64 (local.get $a))))
)


;; int_cmp: compare two integers, returns -1/0/1
(func $int_cmp (param $a (ref null eq)) (param $b (ref null eq)) (result i32)
  (local $a64 i64)
  (local $b64 i64)
  (local.set $a64 (call $to_i64 (local.get $a)))
  (local.set $b64 (call $to_i64 (local.get $b)))
  (if (result i32) (i64.lt_s (local.get $a64) (local.get $b64))
    (then (i32.const -1))
    (else
      (if (result i32) (i64.gt_s (local.get $a64) (local.get $b64))
        (then (i32.const 1))
        (else (i32.const 0))
      )
    )
  )
)


;; int_eq: check if two integers are equal
(func $int_eq (param $a (ref null eq)) (param $b (ref null eq)) (result i32)
  (i64.eq (call $to_i64 (local.get $a)) (call $to_i64 (local.get $b)))
)


;; i32_pow: integer exponentiation
(func $i32_pow (param $base i32) (param $exp i32) (result i32)
  (local $result i32)
  (local.set $result (i32.const 1))
  (block $done
    (loop $loop
      (br_if $done (i32.le_s (local.get $exp) (i32.const 0)))
      (local.set $result (i32.mul (local.get $result) (local.get $base)))
      (local.set $exp (i32.sub (local.get $exp) (i32.const 1)))
      (br $loop)
    )
  )
  (local.get $result)
)


;; =============================================================================
;; int.to_bytes and int.from_bytes helpers
;; =============================================================================

;; int_to_bytes_big: Convert integer to bytes (big endian, unsigned)
;; Stack: (int_value as i31, length as i31) -> $BYTES
(func $int_to_bytes_big (param $val (ref null eq)) (param $len (ref null eq)) (result (ref null eq))
  (local $int_val i32)
  (local $length i32)
  (local $offset i32)
  (local $i i32)
  (local $shift i32)
  ;; Extract integer value
  (local.set $int_val (i31.get_s (ref.cast (ref i31) (local.get $val))))
  ;; Extract length
  (local.set $length (i31.get_s (ref.cast (ref i31) (local.get $len))))
  ;; Allocate memory for bytes
  (local.set $offset (global.get $string_heap))
  (global.set $string_heap (i32.add (global.get $string_heap) (local.get $length)))
  ;; Write bytes in big-endian order (MSB first)
  (local.set $i (i32.const 0))
  (block $done
    (loop $write
      (br_if $done (i32.ge_u (local.get $i) (local.get $length)))
      ;; Calculate shift: (length - 1 - i) * 8
      (local.set $shift (i32.mul (i32.sub (i32.sub (local.get $length) (i32.const 1)) (local.get $i)) (i32.const 8)))
      ;; Store byte
      (i32.store8 (i32.add (local.get $offset) (local.get $i))
        (i32.and (i32.shr_u (local.get $int_val) (local.get $shift)) (i32.const 255)))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $write)
    )
  )
  (struct.new $BYTES (local.get $offset) (local.get $length) (i32.const 0))
)


;; int_to_bytes_little: Convert integer to bytes (little endian, unsigned)
(func $int_to_bytes_little (param $val (ref null eq)) (param $len (ref null eq)) (result (ref null eq))
  (local $int_val i32)
  (local $length i32)
  (local $offset i32)
  (local $i i32)
  (local $shift i32)
  ;; Extract integer value
  (local.set $int_val (i31.get_s (ref.cast (ref i31) (local.get $val))))
  ;; Extract length
  (local.set $length (i31.get_s (ref.cast (ref i31) (local.get $len))))
  ;; Allocate memory for bytes
  (local.set $offset (global.get $string_heap))
  (global.set $string_heap (i32.add (global.get $string_heap) (local.get $length)))
  ;; Write bytes in little-endian order (LSB first)
  (local.set $i (i32.const 0))
  (block $done
    (loop $write
      (br_if $done (i32.ge_u (local.get $i) (local.get $length)))
      ;; Calculate shift: i * 8
      (local.set $shift (i32.mul (local.get $i) (i32.const 8)))
      ;; Store byte
      (i32.store8 (i32.add (local.get $offset) (local.get $i))
        (i32.and (i32.shr_u (local.get $int_val) (local.get $shift)) (i32.const 255)))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $write)
    )
  )
  (struct.new $BYTES (local.get $offset) (local.get $length) (i32.const 0))
)


;; int_to_bytes_big_signed: Convert signed integer to bytes (big endian)
(func $int_to_bytes_big_signed (param $val (ref null eq)) (param $len (ref null eq)) (result (ref null eq))
  ;; For now, same as unsigned (works for positive values)
  (call $int_to_bytes_big (local.get $val) (local.get $len))
)


;; int_to_bytes_little_signed: Convert signed integer to bytes (little endian)
(func $int_to_bytes_little_signed (param $val (ref null eq)) (param $len (ref null eq)) (result (ref null eq))
  ;; For now, same as unsigned (works for positive values)
  (call $int_to_bytes_little (local.get $val) (local.get $len))
)

"""
