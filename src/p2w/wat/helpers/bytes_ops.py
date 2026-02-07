"""WAT helper functions: Bytes operations."""

from __future__ import annotations

BYTES_OPS_CODE = """

;; bytes_get: get byte at index from bytes (returns integer)
(func $bytes_get (param $b (ref $BYTES)) (param $idx i32) (result (ref null eq))
  (local $offset i32)
  (local $len i32)
  (local.set $offset (struct.get $BYTES 0 (local.get $b)))
  (local.set $len (struct.get $BYTES 1 (local.get $b)))

  ;; Handle negative index
  (if (i32.lt_s (local.get $idx) (i32.const 0))
    (then
      (local.set $idx (i32.add (local.get $len) (local.get $idx)))
    )
  )

  ;; Bounds check
  (if (i32.or (i32.lt_s (local.get $idx) (i32.const 0)) (i32.ge_s (local.get $idx) (local.get $len)))
    (then (return (ref.null eq)))
  )
  ;; Return byte value as i31 integer
  (ref.i31 (i32.load8_u (i32.add (local.get $offset) (local.get $idx))))
)


;; reverse_bytes: reverse bytes in-place
(func $reverse_bytes (param $offset i32) (param $len i32)
  (local $i i32)
  (local $j i32)
  (local $tmp i32)
  (local.set $i (i32.const 0))
  (local.set $j (i32.sub (local.get $len) (i32.const 1)))
  (block $done
    (loop $loop
      (br_if $done (i32.ge_s (local.get $i) (local.get $j)))
      (local.set $tmp (i32.load8_u (i32.add (local.get $offset) (local.get $i))))
      (i32.store8 (i32.add (local.get $offset) (local.get $i))
        (i32.load8_u (i32.add (local.get $offset) (local.get $j))))
      (i32.store8 (i32.add (local.get $offset) (local.get $j)) (local.get $tmp))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (local.set $j (i32.sub (local.get $j) (i32.const 1)))
      (br $loop)
    )
  )
)


;; bytes_to_int_big: Convert bytes to integer (big endian, unsigned)
;; Stack: $BYTES -> i31
(func $bytes_to_int_big (param $b (ref null eq)) (result (ref null eq))
  (local $offset i32)
  (local $length i32)
  (local $result i32)
  (local $i i32)
  ;; Get bytes offset and length
  (local.set $offset (struct.get $BYTES 0 (ref.cast (ref $BYTES) (local.get $b))))
  (local.set $length (struct.get $BYTES 1 (ref.cast (ref $BYTES) (local.get $b))))
  ;; Read bytes in big-endian order
  (local.set $result (i32.const 0))
  (local.set $i (i32.const 0))
  (block $done
    (loop $read
      (br_if $done (i32.ge_u (local.get $i) (local.get $length)))
      ;; result = (result << 8) | byte
      (local.set $result
        (i32.or
          (i32.shl (local.get $result) (i32.const 8))
          (i32.load8_u (i32.add (local.get $offset) (local.get $i)))))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $read)
    )
  )
  (ref.i31 (local.get $result))
)


;; bytes_to_int_little: Convert bytes to integer (little endian, unsigned)
(func $bytes_to_int_little (param $b (ref null eq)) (result (ref null eq))
  (local $offset i32)
  (local $length i32)
  (local $result i32)
  (local $i i32)
  (local $shift i32)
  ;; Get bytes offset and length
  (local.set $offset (struct.get $BYTES 0 (ref.cast (ref $BYTES) (local.get $b))))
  (local.set $length (struct.get $BYTES 1 (ref.cast (ref $BYTES) (local.get $b))))
  ;; Read bytes in little-endian order
  (local.set $result (i32.const 0))
  (local.set $i (i32.const 0))
  (block $done
    (loop $read
      (br_if $done (i32.ge_u (local.get $i) (local.get $length)))
      ;; result = result | (byte << (i * 8))
      (local.set $shift (i32.mul (local.get $i) (i32.const 8)))
      (local.set $result
        (i32.or
          (local.get $result)
          (i32.shl (i32.load8_u (i32.add (local.get $offset) (local.get $i))) (local.get $shift))))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $read)
    )
  )
  (ref.i31 (local.get $result))
)


;; bytes_to_int_big_signed: Convert bytes to signed integer (big endian)
;; Sign-extends based on the most significant bit
(func $bytes_to_int_big_signed (param $b (ref null eq)) (result (ref null eq))
  (local $offset i32)
  (local $length i32)
  (local $result i32)
  (local $i i32)
  (local $sign_bit i32)
  (local $max_unsigned i32)
  ;; Get bytes offset and length
  (local.set $offset (struct.get $BYTES 0 (ref.cast (ref $BYTES) (local.get $b))))
  (local.set $length (struct.get $BYTES 1 (ref.cast (ref $BYTES) (local.get $b))))
  ;; Read bytes in big-endian order (same as unsigned)
  (local.set $result (i32.const 0))
  (local.set $i (i32.const 0))
  (block $done
    (loop $read
      (br_if $done (i32.ge_u (local.get $i) (local.get $length)))
      (local.set $result
        (i32.or
          (i32.shl (local.get $result) (i32.const 8))
          (i32.load8_u (i32.add (local.get $offset) (local.get $i)))))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $read)
    )
  )
  ;; Sign extension: check if MSB is set
  ;; sign_bit = 1 << (length * 8 - 1)
  (local.set $sign_bit (i32.shl (i32.const 1) (i32.sub (i32.mul (local.get $length) (i32.const 8)) (i32.const 1))))
  ;; If result >= sign_bit, subtract 2^(length*8) to make it negative
  (if (i32.ge_u (local.get $result) (local.get $sign_bit))
    (then
      ;; max_unsigned = 1 << (length * 8)
      (local.set $max_unsigned (i32.shl (i32.const 1) (i32.mul (local.get $length) (i32.const 8))))
      (local.set $result (i32.sub (local.get $result) (local.get $max_unsigned)))
    )
  )
  (ref.i31 (local.get $result))
)


;; bytes_to_int_little_signed: Convert bytes to signed integer (little endian)
(func $bytes_to_int_little_signed (param $b (ref null eq)) (result (ref null eq))
  (local $offset i32)
  (local $length i32)
  (local $result i32)
  (local $i i32)
  (local $shift i32)
  (local $sign_bit i32)
  (local $max_unsigned i32)
  ;; Get bytes offset and length
  (local.set $offset (struct.get $BYTES 0 (ref.cast (ref $BYTES) (local.get $b))))
  (local.set $length (struct.get $BYTES 1 (ref.cast (ref $BYTES) (local.get $b))))
  ;; Read bytes in little-endian order (same as unsigned)
  (local.set $result (i32.const 0))
  (local.set $i (i32.const 0))
  (block $done
    (loop $read
      (br_if $done (i32.ge_u (local.get $i) (local.get $length)))
      (local.set $shift (i32.mul (local.get $i) (i32.const 8)))
      (local.set $result
        (i32.or
          (local.get $result)
          (i32.shl (i32.load8_u (i32.add (local.get $offset) (local.get $i))) (local.get $shift))))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $read)
    )
  )
  ;; Sign extension: check if MSB is set
  (local.set $sign_bit (i32.shl (i32.const 1) (i32.sub (i32.mul (local.get $length) (i32.const 8)) (i32.const 1))))
  (if (i32.ge_u (local.get $result) (local.get $sign_bit))
    (then
      (local.set $max_unsigned (i32.shl (i32.const 1) (i32.mul (local.get $length) (i32.const 8))))
      (local.set $result (i32.sub (local.get $result) (local.get $max_unsigned)))
    )
  )
  (ref.i31 (local.get $result))
)

"""
