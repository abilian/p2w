"""WAT helper functions: String operations and formatting."""

from __future__ import annotations

STRINGS_CODE = """

;; parse_int_base: parse string as integer with given base (2-36)
;; Handles optional 0x/0X (base 16), 0b/0B (base 2), 0o/0O (base 8) prefixes
(func $parse_int_base (param $str (ref $STRING)) (param $base i32) (result i32)
  (local $offset i32)
  (local $len i32)
  (local $i i32)
  (local $result i32)
  (local $char i32)
  (local $char2 i32)
  (local $digit i32)
  (local $neg i32)
  (local.set $offset (struct.get $STRING 0 (local.get $str)))
  (local.set $len (struct.get $STRING 1 (local.get $str)))
  (local.set $result (i32.const 0))
  (local.set $i (i32.const 0))
  (local.set $neg (i32.const 0))
  ;; Check for negative sign
  (if (i32.and (i32.gt_s (local.get $len) (i32.const 0))
               (i32.eq (i32.load8_u (local.get $offset)) (i32.const 45)))
    (then
      (local.set $neg (i32.const 1))
      (local.set $i (i32.const 1))
    )
  )
  ;; Check for prefix (0x, 0b, 0o) - need at least 2 more chars after current position
  (if (i32.ge_s (i32.sub (local.get $len) (local.get $i)) (i32.const 2))
    (then
      (local.set $char (i32.load8_u (i32.add (local.get $offset) (local.get $i))))
      (local.set $char2 (i32.load8_u (i32.add (local.get $offset) (i32.add (local.get $i) (i32.const 1)))))
      ;; Check for '0' prefix
      (if (i32.eq (local.get $char) (i32.const 48))  ;; '0'
        (then
          ;; Check for 0x or 0X (hex, base 16)
          (if (i32.and
                (i32.eq (local.get $base) (i32.const 16))
                (i32.or
                  (i32.eq (local.get $char2) (i32.const 120))  ;; 'x'
                  (i32.eq (local.get $char2) (i32.const 88)))) ;; 'X'
            (then (local.set $i (i32.add (local.get $i) (i32.const 2))))
          )
          ;; Check for 0b or 0B (binary, base 2)
          (if (i32.and
                (i32.eq (local.get $base) (i32.const 2))
                (i32.or
                  (i32.eq (local.get $char2) (i32.const 98))   ;; 'b'
                  (i32.eq (local.get $char2) (i32.const 66)))) ;; 'B'
            (then (local.set $i (i32.add (local.get $i) (i32.const 2))))
          )
          ;; Check for 0o or 0O (octal, base 8)
          (if (i32.and
                (i32.eq (local.get $base) (i32.const 8))
                (i32.or
                  (i32.eq (local.get $char2) (i32.const 111))  ;; 'o'
                  (i32.eq (local.get $char2) (i32.const 79)))) ;; 'O'
            (then (local.set $i (i32.add (local.get $i) (i32.const 2))))
          )
        )
      )
    )
  )
  ;; Parse digits
  (block $done
    (loop $loop
      (br_if $done (i32.ge_s (local.get $i) (local.get $len)))
      (local.set $char (i32.load8_u (i32.add (local.get $offset) (local.get $i))))
      ;; Convert char to digit value
      (if (i32.and (i32.ge_u (local.get $char) (i32.const 48))   ;; '0'
                   (i32.le_u (local.get $char) (i32.const 57)))  ;; '9'
        (then (local.set $digit (i32.sub (local.get $char) (i32.const 48))))
        (else
          (if (i32.and (i32.ge_u (local.get $char) (i32.const 97))   ;; 'a'
                       (i32.le_u (local.get $char) (i32.const 122))) ;; 'z'
            (then (local.set $digit (i32.add (i32.sub (local.get $char) (i32.const 97)) (i32.const 10))))
            (else
              (if (i32.and (i32.ge_u (local.get $char) (i32.const 65))   ;; 'A'
                           (i32.le_u (local.get $char) (i32.const 90))) ;; 'Z'
                (then (local.set $digit (i32.add (i32.sub (local.get $char) (i32.const 65)) (i32.const 10))))
                (else (br $done))  ;; Invalid char
              )
            )
          )
        )
      )
      ;; Check digit is valid for base
      (br_if $done (i32.ge_s (local.get $digit) (local.get $base)))
      ;; result = result * base + digit
      (local.set $result (i32.add
        (i32.mul (local.get $result) (local.get $base))
        (local.get $digit)))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $loop)
    )
  )
  ;; Apply negative sign
  (if (local.get $neg)
    (then (local.set $result (i32.sub (i32.const 0) (local.get $result))))
  )
  (local.get $result)
)


;; parse_float: parse string as float (e.g., "3.14", "-2.5")
(func $parse_float (param $str (ref $STRING)) (result f64)
  (local $offset i32)
  (local $len i32)
  (local $i i32)
  (local $char i32)
  (local $int_part f64)
  (local $frac_part f64)
  (local $frac_divisor f64)
  (local $neg i32)
  (local $in_frac i32)
  (local.set $offset (struct.get $STRING 0 (local.get $str)))
  (local.set $len (struct.get $STRING 1 (local.get $str)))
  (local.set $int_part (f64.const 0))
  (local.set $frac_part (f64.const 0))
  (local.set $frac_divisor (f64.const 1))
  (local.set $i (i32.const 0))
  (local.set $neg (i32.const 0))
  (local.set $in_frac (i32.const 0))
  ;; Check for negative sign
  (if (i32.and (i32.gt_s (local.get $len) (i32.const 0))
               (i32.eq (i32.load8_u (local.get $offset)) (i32.const 45)))
    (then
      (local.set $neg (i32.const 1))
      (local.set $i (i32.const 1))
    )
  )
  ;; Parse number
  (block $done
    (loop $loop
      (br_if $done (i32.ge_s (local.get $i) (local.get $len)))
      (local.set $char (i32.load8_u (i32.add (local.get $offset) (local.get $i))))
      ;; Check for decimal point
      (if (i32.eq (local.get $char) (i32.const 46))  ;; '.'
        (then
          (local.set $in_frac (i32.const 1))
          (local.set $i (i32.add (local.get $i) (i32.const 1)))
          (br $loop)
        )
      )
      ;; Check for digit
      (if (i32.and (i32.ge_u (local.get $char) (i32.const 48))
                   (i32.le_u (local.get $char) (i32.const 57)))
        (then
          (if (local.get $in_frac)
            (then
              ;; Fractional part
              (local.set $frac_divisor (f64.mul (local.get $frac_divisor) (f64.const 10)))
              (local.set $frac_part (f64.add (local.get $frac_part)
                (f64.div
                  (f64.convert_i32_u (i32.sub (local.get $char) (i32.const 48)))
                  (local.get $frac_divisor))))
            )
            (else
              ;; Integer part
              (local.set $int_part (f64.add
                (f64.mul (local.get $int_part) (f64.const 10))
                (f64.convert_i32_u (i32.sub (local.get $char) (i32.const 48)))))
            )
          )
        )
        (else (br $done))  ;; Non-digit
      )
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $loop)
    )
  )
  ;; Combine parts and apply sign
  (if (result f64) (local.get $neg)
    (then (f64.neg (f64.add (local.get $int_part) (local.get $frac_part))))
    (else (f64.add (local.get $int_part) (local.get $frac_part)))
  )
)


;; strings_equal: compare two STRING structs byte by byte
(func $strings_equal (param $a (ref $STRING)) (param $b (ref $STRING)) (result i32)
  (local $offset_a i32)
  (local $offset_b i32)
  (local $len_a i32)
  (local $len_b i32)
  (local $i i32)
  (local.set $offset_a (struct.get $STRING 0 (local.get $a)))
  (local.set $len_a (struct.get $STRING 1 (local.get $a)))
  (local.set $offset_b (struct.get $STRING 0 (local.get $b)))
  (local.set $len_b (struct.get $STRING 1 (local.get $b)))
  ;; Different lengths - not equal
  (if (i32.ne (local.get $len_a) (local.get $len_b))
    (then (return (i32.const 0)))
  )
  ;; Compare byte by byte
  (local.set $i (i32.const 0))
  (block $done
    (loop $loop
      (br_if $done (i32.ge_u (local.get $i) (local.get $len_a)))
      (if (i32.ne
            (i32.load8_u (i32.add (local.get $offset_a) (local.get $i)))
            (i32.load8_u (i32.add (local.get $offset_b) (local.get $i))))
        (then (return (i32.const 0)))
      )
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $loop)
    )
  )
  (i32.const 1)
)


;; strings_compare: compare two STRING structs lexicographically
;; Returns: -1 if a < b, 0 if a == b, 1 if a > b
(func $strings_compare (param $a (ref $STRING)) (param $b (ref $STRING)) (result i32)
  (local $offset_a i32)
  (local $offset_b i32)
  (local $len_a i32)
  (local $len_b i32)
  (local $min_len i32)
  (local $i i32)
  (local $char_a i32)
  (local $char_b i32)
  (local.set $offset_a (struct.get $STRING 0 (local.get $a)))
  (local.set $len_a (struct.get $STRING 1 (local.get $a)))
  (local.set $offset_b (struct.get $STRING 0 (local.get $b)))
  (local.set $len_b (struct.get $STRING 1 (local.get $b)))
  ;; Get minimum length
  (local.set $min_len (local.get $len_a))
  (if (i32.lt_u (local.get $len_b) (local.get $len_a))
    (then (local.set $min_len (local.get $len_b)))
  )
  ;; Compare byte by byte
  (local.set $i (i32.const 0))
  (block $done
    (loop $loop
      (br_if $done (i32.ge_u (local.get $i) (local.get $min_len)))
      (local.set $char_a (i32.load8_u (i32.add (local.get $offset_a) (local.get $i))))
      (local.set $char_b (i32.load8_u (i32.add (local.get $offset_b) (local.get $i))))
      (if (i32.lt_u (local.get $char_a) (local.get $char_b))
        (then (return (i32.const -1)))
      )
      (if (i32.gt_u (local.get $char_a) (local.get $char_b))
        (then (return (i32.const 1)))
      )
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $loop)
    )
  )
  ;; All compared bytes are equal - shorter string is less
  (if (i32.lt_u (local.get $len_a) (local.get $len_b))
    (then (return (i32.const -1)))
  )
  (if (i32.gt_u (local.get $len_a) (local.get $len_b))
    (then (return (i32.const 1)))
  )
  (i32.const 0)
)


;; string_get: get character at index from string
;; OPTIMIZATION: Returns a STRING pointing directly into the source string's memory
;; instead of copying the byte. This avoids heap allocation for every character access.
(func $string_get (param $s (ref $STRING)) (param $idx i32) (result (ref null eq))
  (local $offset i32)
  (local $len i32)
  (local.set $offset (struct.get $STRING 0 (local.get $s)))
  (local.set $len (struct.get $STRING 1 (local.get $s)))

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
  ;; Return STRING pointing directly into source string (no copy needed)
  (struct.new $STRING (i32.add (local.get $offset) (local.get $idx)) (i32.const 1))
)


;; string_repeat: repeat a string n times
(func $string_repeat (param $s (ref null eq)) (param $n (ref null eq)) (result (ref null eq))
  (local $str (ref null $STRING))
  (local $count i32)
  (local $i i32)
  (local $src_off i32)
  (local $src_len i32)
  (local $dst_off i32)
  (local $total_len i32)

  (if (ref.is_null (local.get $s))
    (then (return (ref.null eq)))
  )

  (local.set $str (ref.cast (ref $STRING) (local.get $s)))
  (local.set $count (i31.get_s (ref.cast (ref i31) (local.get $n))))

  (if (i32.le_s (local.get $count) (i32.const 0))
    (then (return (struct.new $STRING (global.get $string_heap) (i32.const 0))))
  )

  (local.set $src_off (struct.get $STRING 0 (local.get $str)))
  (local.set $src_len (struct.get $STRING 1 (local.get $str)))
  (local.set $total_len (i32.mul (local.get $src_len) (local.get $count)))

  ;; Allocate new string
  (local.set $dst_off (global.get $string_heap))
  (global.set $string_heap (i32.add (global.get $string_heap) (local.get $total_len)))

  ;; Copy n times
  (local.set $i (i32.const 0))
  (block $done
    (loop $loop
      (br_if $done (i32.ge_s (local.get $i) (local.get $count)))
      (memory.copy
        (i32.add (local.get $dst_off) (i32.mul (local.get $i) (local.get $src_len)))
        (local.get $src_off)
        (local.get $src_len))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $loop)
    )
  )
  (struct.new $STRING (local.get $dst_off) (local.get $total_len))
)


;; string_slice: slice a STRING from lower to upper (exclusive) with step
(func $string_slice (param $str (ref $STRING)) (param $lower i32) (param $upper i32) (param $step i32) (result (ref $STRING))
  (local $src_offset i32)
  (local $src_len i32)
  (local $dest_offset i32)
  (local $i i32)
  (local $dest_len i32)
  (local $step_count i32)
  ;; Get string info
  (local.set $src_offset (struct.get $STRING 0 (local.get $str)))
  (local.set $src_len (struct.get $STRING 1 (local.get $str)))
  ;; Handle negative step (reverse)
  (if (i32.lt_s (local.get $step) (i32.const 0))
    (then
      ;; Negative step: default lower is end-1, default upper is before start
      (if (i32.eq (local.get $lower) (i32.const -999999))
        (then (local.set $lower (i32.sub (local.get $src_len) (i32.const 1))))
        (else
          (if (i32.lt_s (local.get $lower) (i32.const 0))
            (then (local.set $lower (i32.add (local.get $src_len) (local.get $lower))))
          )
        )
      )
      (if (i32.eq (local.get $upper) (i32.const -999999))
        (then (local.set $upper (i32.const -1)))  ;; sentinel for before start
        (else
          (if (i32.lt_s (local.get $upper) (i32.const 0))
            (then (local.set $upper (i32.add (local.get $src_len) (local.get $upper))))
          )
        )
      )
      ;; Build reverse string
      (local.set $dest_offset (global.get $string_heap))
      (local.set $dest_len (i32.const 0))
      (local.set $i (local.get $lower))
      (block $done
        (loop $loop
          (br_if $done (i32.lt_s (local.get $i) (i32.const 0)))
          (if (i32.ne (local.get $upper) (i32.const -1))
            (then (br_if $done (i32.le_s (local.get $i) (local.get $upper))))
          )
          ;; Copy character
          (i32.store8
            (i32.add (local.get $dest_offset) (local.get $dest_len))
            (i32.load8_u (i32.add (local.get $src_offset) (local.get $i))))
          (local.set $dest_len (i32.add (local.get $dest_len) (i32.const 1)))
          ;; Step backwards
          (local.set $i (i32.add (local.get $i) (local.get $step)))
          (br $loop)
        )
      )
      (global.set $string_heap (i32.add (global.get $string_heap) (local.get $dest_len)))
      (return (struct.new $STRING (local.get $dest_offset) (local.get $dest_len)))
    )
  )
  ;; Positive step
  ;; Handle lower = -999999 sentinel (default to 0) or negative lower
  (if (i32.eq (local.get $lower) (i32.const -999999))
    (then (local.set $lower (i32.const 0)))
    (else
      (if (i32.lt_s (local.get $lower) (i32.const 0))
        (then (local.set $lower (i32.add (local.get $src_len) (local.get $lower))))
      )
    )
  )
  ;; Handle upper = -999999 sentinel (to end) or negative upper
  (if (i32.eq (local.get $upper) (i32.const -999999))
    (then (local.set $upper (local.get $src_len)))
    (else
      (if (i32.lt_s (local.get $upper) (i32.const 0))
        (then (local.set $upper (i32.add (local.get $src_len) (local.get $upper))))
      )
    )
  )
  ;; Clamp bounds to valid range
  (if (i32.lt_s (local.get $lower) (i32.const 0))
    (then (local.set $lower (i32.const 0)))
  )
  (if (i32.gt_s (local.get $upper) (local.get $src_len))
    (then (local.set $upper (local.get $src_len)))
  )
  ;; Calculate length
  (local.set $dest_len (i32.sub (local.get $upper) (local.get $lower)))
  (if (i32.le_s (local.get $dest_len) (i32.const 0))
    (then (return (struct.new $STRING (i32.const 0) (i32.const 0))))
  )
  ;; Fast path for step=1: use memory.copy instead of byte-by-byte loop
  (if (i32.eq (local.get $step) (i32.const 1))
    (then
      (local.set $dest_offset (global.get $string_heap))
      (global.set $string_heap (i32.add (global.get $string_heap) (local.get $dest_len)))
      (memory.copy (local.get $dest_offset) (i32.add (local.get $src_offset) (local.get $lower)) (local.get $dest_len))
      (return (struct.new $STRING (local.get $dest_offset) (local.get $dest_len)))
    )
  )
  ;; General case for step > 1: byte-by-byte with step
  (local.set $dest_offset (global.get $string_heap))
  (local.set $dest_len (i32.const 0))
  (local.set $i (local.get $lower))
  (local.set $step_count (i32.const 0))
  (block $done2
    (loop $loop2
      (br_if $done2 (i32.ge_s (local.get $i) (local.get $upper)))
      ;; Only include if step_count == 0
      (if (i32.eq (local.get $step_count) (i32.const 0))
        (then
          (i32.store8
            (i32.add (local.get $dest_offset) (local.get $dest_len))
            (i32.load8_u (i32.add (local.get $src_offset) (local.get $i))))
          (local.set $dest_len (i32.add (local.get $dest_len) (i32.const 1)))
        )
      )
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (local.set $step_count (i32.add (local.get $step_count) (i32.const 1)))
      (if (i32.ge_s (local.get $step_count) (local.get $step))
        (then (local.set $step_count (i32.const 0)))
      )
      (br $loop2)
    )
  )
  (global.set $string_heap (i32.add (global.get $string_heap) (local.get $dest_len)))
  (struct.new $STRING (local.get $dest_offset) (local.get $dest_len))
)


;; value_to_string: convert any value to a STRING for f-strings
(func $value_to_string (param $v (ref null eq)) (result (ref $STRING))
  (local $offset i32)
  (local $len i32)
  (local $num i32)
  (local $num64 i64)
  (local $neg i32)
  (local $start i32)
  (local $i i32)
  (local $digit i32)
  ;; null -> "None"
  (if (ref.is_null (local.get $v))
    (then
      ;; Write "None" to heap
      (local.set $offset (global.get $string_heap))
      (i32.store8 (local.get $offset) (i32.const 78))  ;; N
      (i32.store8 (i32.add (local.get $offset) (i32.const 1)) (i32.const 111))  ;; o
      (i32.store8 (i32.add (local.get $offset) (i32.const 2)) (i32.const 110))  ;; n
      (i32.store8 (i32.add (local.get $offset) (i32.const 3)) (i32.const 101))  ;; e
      (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 4)))
      (return (struct.new $STRING (local.get $offset) (i32.const 4)))
    )
  )
  ;; Already a string - return as-is
  (if (ref.test (ref $STRING) (local.get $v))
    (then (return (ref.cast (ref $STRING) (local.get $v))))
  )
  ;; Integer - convert to decimal string
  (if (ref.test (ref i31) (local.get $v))
    (then
      (local.set $num (i31.get_s (ref.cast (ref i31) (local.get $v))))
      (local.set $offset (global.get $string_heap))
      (local.set $start (local.get $offset))
      ;; Handle negative
      (if (i32.lt_s (local.get $num) (i32.const 0))
        (then
          (i32.store8 (local.get $offset) (i32.const 45))  ;; -
          (local.set $offset (i32.add (local.get $offset) (i32.const 1)))
          (local.set $num (i32.sub (i32.const 0) (local.get $num)))
          (local.set $neg (i32.const 1))
        )
      )
      ;; Handle zero
      (if (i32.eqz (local.get $num))
        (then
          (i32.store8 (local.get $offset) (i32.const 48))  ;; 0
          (global.set $string_heap (i32.add (local.get $offset) (i32.const 1)))
          (return (struct.new $STRING (local.get $start) (i32.const 1)))
        )
      )
      ;; Convert digits (reversed)
      (local.set $i (local.get $offset))
      (block $done
        (loop $loop
          (br_if $done (i32.eqz (local.get $num)))
          (local.set $digit (i32.rem_u (local.get $num) (i32.const 10)))
          (i32.store8 (local.get $i) (i32.add (i32.const 48) (local.get $digit)))
          (local.set $i (i32.add (local.get $i) (i32.const 1)))
          (local.set $num (i32.div_u (local.get $num) (i32.const 10)))
          (br $loop)
        )
      )
      ;; Reverse the digits
      (local.set $len (i32.sub (local.get $i) (local.get $offset)))
      (call $reverse_bytes (local.get $offset) (local.get $len))
      (global.set $string_heap (local.get $i))
      (return (struct.new $STRING (local.get $start) (i32.sub (local.get $i) (local.get $start))))
    )
  )
  ;; INT64 (large integer) - convert to decimal string
  (if (ref.test (ref $INT64) (local.get $v))
    (then
      (local.set $num64 (struct.get $INT64 0 (ref.cast (ref $INT64) (local.get $v))))
      (local.set $offset (global.get $string_heap))
      (local.set $start (local.get $offset))
      ;; Handle negative
      (if (i64.lt_s (local.get $num64) (i64.const 0))
        (then
          (i32.store8 (local.get $offset) (i32.const 45))  ;; -
          (local.set $offset (i32.add (local.get $offset) (i32.const 1)))
          (local.set $num64 (i64.sub (i64.const 0) (local.get $num64)))
          (local.set $neg (i32.const 1))
        )
      )
      ;; Handle zero
      (if (i64.eqz (local.get $num64))
        (then
          (i32.store8 (local.get $offset) (i32.const 48))  ;; 0
          (global.set $string_heap (i32.add (local.get $offset) (i32.const 1)))
          (return (struct.new $STRING (local.get $start) (i32.const 1)))
        )
      )
      ;; Convert digits (reversed)
      (local.set $i (local.get $offset))
      (block $done
        (loop $loop
          (br_if $done (i64.eqz (local.get $num64)))
          (local.set $digit (i32.wrap_i64 (i64.rem_u (local.get $num64) (i64.const 10))))
          (i32.store8 (local.get $i) (i32.add (i32.const 48) (local.get $digit)))
          (local.set $i (i32.add (local.get $i) (i32.const 1)))
          (local.set $num64 (i64.div_u (local.get $num64) (i64.const 10)))
          (br $loop)
        )
      )
      ;; Reverse the digits
      (local.set $len (i32.sub (local.get $i) (local.get $offset)))
      (call $reverse_bytes (local.get $offset) (local.get $len))
      (global.set $string_heap (local.get $i))
      (return (struct.new $STRING (local.get $start) (i32.sub (local.get $i) (local.get $start))))
    )
  )
  ;; Bool
  (if (ref.test (ref $BOOL) (local.get $v))
    (then
      (if (struct.get $BOOL 0 (ref.cast (ref $BOOL) (local.get $v)))
        (then
          ;; "True"
          (local.set $offset (global.get $string_heap))
          (i32.store8 (local.get $offset) (i32.const 84))
          (i32.store8 (i32.add (local.get $offset) (i32.const 1)) (i32.const 114))
          (i32.store8 (i32.add (local.get $offset) (i32.const 2)) (i32.const 117))
          (i32.store8 (i32.add (local.get $offset) (i32.const 3)) (i32.const 101))
          (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 4)))
          (return (struct.new $STRING (local.get $offset) (i32.const 4)))
        )
        (else
          ;; "False"
          (local.set $offset (global.get $string_heap))
          (i32.store8 (local.get $offset) (i32.const 70))
          (i32.store8 (i32.add (local.get $offset) (i32.const 1)) (i32.const 97))
          (i32.store8 (i32.add (local.get $offset) (i32.const 2)) (i32.const 108))
          (i32.store8 (i32.add (local.get $offset) (i32.const 3)) (i32.const 115))
          (i32.store8 (i32.add (local.get $offset) (i32.const 4)) (i32.const 101))
          (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 5)))
          (return (struct.new $STRING (local.get $offset) (i32.const 5)))
        )
      )
    )
  )
  ;; Float - use host function to convert
  (if (ref.test (ref $FLOAT) (local.get $v))
    (then
      (local.set $offset (global.get $string_heap))
      (local.set $len (call $f64_to_string
        (struct.get $FLOAT 0 (ref.cast (ref $FLOAT) (local.get $v)))
        (local.get $offset)))
      (global.set $string_heap (i32.add (local.get $offset) (local.get $len)))
      (return (struct.new $STRING (local.get $offset) (local.get $len)))
    )
  )
  ;; EMPTY_LIST - return "[]"
  (if (ref.test (ref $EMPTY_LIST) (local.get $v))
    (then
      (local.set $offset (global.get $string_heap))
      (i32.store8 (local.get $offset) (i32.const 91))  ;; [
      (i32.store8 (i32.add (local.get $offset) (i32.const 1)) (i32.const 93))  ;; ]
      (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 2)))
      (return (struct.new $STRING (local.get $offset) (i32.const 2)))
    )
  )
  ;; $LIST (array-backed list) - convert to "[elem, elem, ...]"
  (if (ref.test (ref $LIST) (local.get $v))
    (then
      (return (call $list_v2_to_string (ref.cast (ref $LIST) (local.get $v))))
    )
  )
  ;; TUPLE - convert to "(elem, elem, ...)"
  (if (ref.test (ref $TUPLE) (local.get $v))
    (then
      (return (call $tuple_to_string (local.get $v)))
    )
  )
  ;; PAIR (list) - convert to "[elem, elem, ...]"
  (if (ref.test (ref $PAIR) (local.get $v))
    (then
      (return (call $list_to_string (local.get $v)))
    )
  )
  ;; DICT - convert to "{key: val, ...}"
  (if (ref.test (ref $DICT) (local.get $v))
    (then
      (return (call $dict_to_string (local.get $v)))
    )
  )
  ;; SUPER - return "<super: <class 'X'"
  (if (ref.test (ref $SUPER) (local.get $v))
    (then
      (return (call $super_to_string (ref.cast (ref $SUPER) (local.get $v))))
    )
  )
  ;; CLASS - return "<class 'ClassName'>"
  (if (ref.test (ref $CLASS) (local.get $v))
    (then
      (return (call $class_to_string (ref.cast (ref $CLASS) (local.get $v))))
    )
  )
  ;; CLOSURE (builtin type) - return "<class 'typename'>"
  (if (ref.test (ref $CLOSURE) (local.get $v))
    (then
      (return (call $closure_type_to_string (struct.get $CLOSURE 1 (ref.cast (ref $CLOSURE) (local.get $v)))))
    )
  )
  ;; Default: empty string
  (struct.new $STRING (i32.const 0) (i32.const 0))
)


;; super_to_string: convert SUPER to string "<super: <class 'ClassName'"
(func $super_to_string (param $sup (ref $SUPER)) (result (ref $STRING))
  (local $offset i32)
  (local $class (ref $CLASS))
  (local $class_name (ref $STRING))
  (local $prefix (ref $STRING))
  (local $result (ref $STRING))

  (local.set $class (struct.get $SUPER 0 (local.get $sup)))
  (local.set $class_name (struct.get $CLASS 0 (local.get $class)))

  ;; Create "<super: <class '" prefix (16 chars)
  (local.set $offset (global.get $string_heap))
  (i32.store8 (local.get $offset) (i32.const 60))  ;; <
  (i32.store8 (i32.add (local.get $offset) (i32.const 1)) (i32.const 115))  ;; s
  (i32.store8 (i32.add (local.get $offset) (i32.const 2)) (i32.const 117))  ;; u
  (i32.store8 (i32.add (local.get $offset) (i32.const 3)) (i32.const 112))  ;; p
  (i32.store8 (i32.add (local.get $offset) (i32.const 4)) (i32.const 101))  ;; e
  (i32.store8 (i32.add (local.get $offset) (i32.const 5)) (i32.const 114))  ;; r
  (i32.store8 (i32.add (local.get $offset) (i32.const 6)) (i32.const 58))   ;; :
  (i32.store8 (i32.add (local.get $offset) (i32.const 7)) (i32.const 32))   ;; space
  (i32.store8 (i32.add (local.get $offset) (i32.const 8)) (i32.const 60))   ;; <
  (i32.store8 (i32.add (local.get $offset) (i32.const 9)) (i32.const 99))   ;; c
  (i32.store8 (i32.add (local.get $offset) (i32.const 10)) (i32.const 108)) ;; l
  (i32.store8 (i32.add (local.get $offset) (i32.const 11)) (i32.const 97))  ;; a
  (i32.store8 (i32.add (local.get $offset) (i32.const 12)) (i32.const 115)) ;; s
  (i32.store8 (i32.add (local.get $offset) (i32.const 13)) (i32.const 115)) ;; s
  (i32.store8 (i32.add (local.get $offset) (i32.const 14)) (i32.const 32))  ;; space
  (i32.store8 (i32.add (local.get $offset) (i32.const 15)) (i32.const 39))  ;; '
  (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 16)))
  (local.set $prefix (struct.new $STRING (local.get $offset) (i32.const 16)))

  ;; Concatenate prefix + class_name
  (call $string_concat (local.get $prefix) (local.get $class_name))
)


;; closure_type_to_string: convert CLOSURE func index to type string "<class 'typename'>"
(func $closure_type_to_string (param $idx i32) (result (ref $STRING))
  (local $offset i32)
  (local $prefix (ref $STRING))
  (local $typename (ref $STRING))
  (local $suffix (ref $STRING))
  (local $result (ref $STRING))

  ;; Initialize $typename with empty string as default
  (local.set $typename (struct.new $STRING (i32.const 0) (i32.const 0)))

  ;; Create "<class '" prefix (8 chars)
  (local.set $offset (global.get $string_heap))
  (i32.store8 (local.get $offset) (i32.const 60))   ;; <
  (i32.store8 (i32.add (local.get $offset) (i32.const 1)) (i32.const 99))   ;; c
  (i32.store8 (i32.add (local.get $offset) (i32.const 2)) (i32.const 108))  ;; l
  (i32.store8 (i32.add (local.get $offset) (i32.const 3)) (i32.const 97))   ;; a
  (i32.store8 (i32.add (local.get $offset) (i32.const 4)) (i32.const 115))  ;; s
  (i32.store8 (i32.add (local.get $offset) (i32.const 5)) (i32.const 115))  ;; s
  (i32.store8 (i32.add (local.get $offset) (i32.const 6)) (i32.const 32))   ;; space
  (i32.store8 (i32.add (local.get $offset) (i32.const 7)) (i32.const 39))   ;; '
  (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 8)))
  (local.set $prefix (struct.new $STRING (local.get $offset) (i32.const 8)))

  ;; Get type name based on index
  (local.set $offset (global.get $string_heap))
  (if (i32.eq (local.get $idx) (i32.const 6))  ;; int
    (then
      (i32.store8 (local.get $offset) (i32.const 105))  ;; i
      (i32.store8 (i32.add (local.get $offset) (i32.const 1)) (i32.const 110))  ;; n
      (i32.store8 (i32.add (local.get $offset) (i32.const 2)) (i32.const 116))  ;; t
      (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 3)))
      (local.set $typename (struct.new $STRING (local.get $offset) (i32.const 3)))
    )
  )
  (if (i32.eq (local.get $idx) (i32.const 7))  ;; bool
    (then
      (i32.store8 (local.get $offset) (i32.const 98))   ;; b
      (i32.store8 (i32.add (local.get $offset) (i32.const 1)) (i32.const 111))  ;; o
      (i32.store8 (i32.add (local.get $offset) (i32.const 2)) (i32.const 111))  ;; o
      (i32.store8 (i32.add (local.get $offset) (i32.const 3)) (i32.const 108))  ;; l
      (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 4)))
      (local.set $typename (struct.new $STRING (local.get $offset) (i32.const 4)))
    )
  )
  (if (i32.eq (local.get $idx) (i32.const 8))  ;; str
    (then
      (i32.store8 (local.get $offset) (i32.const 115))  ;; s
      (i32.store8 (i32.add (local.get $offset) (i32.const 1)) (i32.const 116))  ;; t
      (i32.store8 (i32.add (local.get $offset) (i32.const 2)) (i32.const 114))  ;; r
      (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 3)))
      (local.set $typename (struct.new $STRING (local.get $offset) (i32.const 3)))
    )
  )
  (if (i32.eq (local.get $idx) (i32.const 11))  ;; float
    (then
      (i32.store8 (local.get $offset) (i32.const 102))  ;; f
      (i32.store8 (i32.add (local.get $offset) (i32.const 1)) (i32.const 108))  ;; l
      (i32.store8 (i32.add (local.get $offset) (i32.const 2)) (i32.const 111))  ;; o
      (i32.store8 (i32.add (local.get $offset) (i32.const 3)) (i32.const 97))   ;; a
      (i32.store8 (i32.add (local.get $offset) (i32.const 4)) (i32.const 116))  ;; t
      (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 5)))
      (local.set $typename (struct.new $STRING (local.get $offset) (i32.const 5)))
    )
  )
  (if (i32.eq (local.get $idx) (i32.const 13))  ;; list
    (then
      (i32.store8 (local.get $offset) (i32.const 108))  ;; l
      (i32.store8 (i32.add (local.get $offset) (i32.const 1)) (i32.const 105))  ;; i
      (i32.store8 (i32.add (local.get $offset) (i32.const 2)) (i32.const 115))  ;; s
      (i32.store8 (i32.add (local.get $offset) (i32.const 3)) (i32.const 116))  ;; t
      (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 4)))
      (local.set $typename (struct.new $STRING (local.get $offset) (i32.const 4)))
    )
  )
  (if (i32.eq (local.get $idx) (i32.const 18))  ;; dict
    (then
      (i32.store8 (local.get $offset) (i32.const 100))  ;; d
      (i32.store8 (i32.add (local.get $offset) (i32.const 1)) (i32.const 105))  ;; i
      (i32.store8 (i32.add (local.get $offset) (i32.const 2)) (i32.const 99))   ;; c
      (i32.store8 (i32.add (local.get $offset) (i32.const 3)) (i32.const 116))  ;; t
      (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 4)))
      (local.set $typename (struct.new $STRING (local.get $offset) (i32.const 4)))
    )
  )
  (if (i32.eq (local.get $idx) (i32.const 19))  ;; tuple
    (then
      (i32.store8 (local.get $offset) (i32.const 116))  ;; t
      (i32.store8 (i32.add (local.get $offset) (i32.const 1)) (i32.const 117))  ;; u
      (i32.store8 (i32.add (local.get $offset) (i32.const 2)) (i32.const 112))  ;; p
      (i32.store8 (i32.add (local.get $offset) (i32.const 3)) (i32.const 108))  ;; l
      (i32.store8 (i32.add (local.get $offset) (i32.const 4)) (i32.const 101))  ;; e
      (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 5)))
      (local.set $typename (struct.new $STRING (local.get $offset) (i32.const 5)))
    )
  )
  (if (i32.eq (local.get $idx) (i32.const 30))  ;; bytes
    (then
      (i32.store8 (local.get $offset) (i32.const 98))   ;; b
      (i32.store8 (i32.add (local.get $offset) (i32.const 1)) (i32.const 121))  ;; y
      (i32.store8 (i32.add (local.get $offset) (i32.const 2)) (i32.const 116))  ;; t
      (i32.store8 (i32.add (local.get $offset) (i32.const 3)) (i32.const 101))  ;; e
      (i32.store8 (i32.add (local.get $offset) (i32.const 4)) (i32.const 115))  ;; s
      (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 5)))
      (local.set $typename (struct.new $STRING (local.get $offset) (i32.const 5)))
    )
  )

  ;; Create "'>" suffix (2 chars)
  (local.set $offset (global.get $string_heap))
  (i32.store8 (local.get $offset) (i32.const 39))   ;; '
  (i32.store8 (i32.add (local.get $offset) (i32.const 1)) (i32.const 62))   ;; >
  (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 2)))
  (local.set $suffix (struct.new $STRING (local.get $offset) (i32.const 2)))

  ;; Concatenate: "<class '" + typename + "'>"
  (local.set $result (call $string_concat (local.get $prefix) (local.get $typename)))
  (call $string_concat (local.get $result) (local.get $suffix))
)


;; value_to_string_repr: convert value to string with repr-style quoting for strings
(func $value_to_string_repr (param $v (ref null eq)) (result (ref $STRING))
  (local $offset i32)
  ;; For strings, add quotes
  (if (ref.test (ref $STRING) (local.get $v))
    (then
      (return (call $string_add_quotes (ref.cast (ref $STRING) (local.get $v))))
    )
  )
  ;; For everything else, use regular value_to_string
  (call $value_to_string (local.get $v))
)


;; float_to_string_precision: convert float to string with specified precision
(func $float_to_string_precision (param $v (ref null eq)) (param $precision i32) (result (ref $STRING))
  (local $offset i32)
  (local $len i32)
  (if (ref.is_null (local.get $v))
    (then (return (struct.new $STRING (i32.const 0) (i32.const 0))))
  )
  (if (ref.test (ref $FLOAT) (local.get $v))
    (then
      (local.set $offset (global.get $string_heap))
      (local.set $len (call $f64_format_precision
        (struct.get $FLOAT 0 (ref.cast (ref $FLOAT) (local.get $v)))
        (local.get $precision)
        (local.get $offset)))
      (global.set $string_heap (i32.add (local.get $offset) (local.get $len)))
      (return (struct.new $STRING (local.get $offset) (local.get $len)))
    )
  )
  ;; Not a float - use regular value_to_string
  (call $value_to_string (local.get $v))
)


;; format_precision: format value with specified decimal precision
;; Handles both floats (uses precision) and integers (ignores precision for now)
(func $format_precision (param $v (ref null eq)) (param $precision i32) (result (ref $STRING))
  (local $offset i32)
  (local $len i32)
  ;; For floats, use the precision
  (if (ref.test (ref $FLOAT) (local.get $v))
    (then
      (local.set $offset (global.get $string_heap))
      (local.set $len (call $f64_format_precision
        (struct.get $FLOAT 0 (ref.cast (ref $FLOAT) (local.get $v)))
        (local.get $precision)
        (local.get $offset)))
      (global.set $string_heap (i32.add (local.get $offset) (local.get $len)))
      (return (struct.new $STRING (local.get $offset) (local.get $len)))
    )
  )
  ;; For integers with precision, treat as float
  (if (ref.test (ref i31) (local.get $v))
    (then
      (local.set $offset (global.get $string_heap))
      (local.set $len (call $f64_format_precision
        (f64.convert_i32_s (i31.get_s (ref.cast (ref i31) (local.get $v))))
        (local.get $precision)
        (local.get $offset)))
      (global.set $string_heap (i32.add (local.get $offset) (local.get $len)))
      (return (struct.new $STRING (local.get $offset) (local.get $len)))
    )
  )
  ;; Default: use value_to_string
  (call $value_to_string (local.get $v))
)


;; format_with_commas: add thousands separators to a number string
(func $format_with_commas (param $s (ref $STRING)) (result (ref $STRING))
  (local $src_off i32)
  (local $src_len i32)
  (local $dst_off i32)
  (local $i i32)
  (local $j i32)
  (local $digit_count i32)
  (local $char i32)
  (local $neg i32)
  (local $decimal_pos i32)
  (local $integer_len i32)
  (local $result_len i32)
  (local $num_commas i32)

  (local.set $src_off (struct.get $STRING 0 (local.get $s)))
  (local.set $src_len (struct.get $STRING 1 (local.get $s)))

  ;; Empty string - return as is
  (if (i32.eqz (local.get $src_len))
    (then (return (local.get $s)))
  )

  ;; Check for negative sign
  (local.set $neg (i32.const 0))
  (local.set $i (i32.const 0))
  (if (i32.eq (i32.load8_u (local.get $src_off)) (i32.const 45))  ;; '-'
    (then
      (local.set $neg (i32.const 1))
      (local.set $i (i32.const 1))
    )
  )

  ;; Find decimal point (if any)
  (local.set $decimal_pos (local.get $src_len))  ;; default: no decimal
  (local.set $j (local.get $i))
  (block $found
    (loop $find_dec
      (br_if $found (i32.ge_u (local.get $j) (local.get $src_len)))
      (if (i32.eq (i32.load8_u (i32.add (local.get $src_off) (local.get $j))) (i32.const 46))  ;; '.'
        (then
          (local.set $decimal_pos (local.get $j))
          (br $found)
        )
      )
      (local.set $j (i32.add (local.get $j) (i32.const 1)))
      (br $find_dec)
    )
  )

  ;; Calculate integer part length (excluding sign)
  (local.set $integer_len (i32.sub (local.get $decimal_pos) (local.get $i)))

  ;; If integer part is 3 or less digits, no commas needed
  (if (i32.le_s (local.get $integer_len) (i32.const 3))
    (then (return (local.get $s)))
  )

  ;; Calculate number of commas needed
  (local.set $num_commas (i32.div_u (i32.sub (local.get $integer_len) (i32.const 1)) (i32.const 3)))

  ;; Allocate new string
  (local.set $result_len (i32.add (local.get $src_len) (local.get $num_commas)))
  (local.set $dst_off (global.get $string_heap))
  (global.set $string_heap (i32.add (global.get $string_heap) (local.get $result_len)))

  ;; Copy negative sign if present
  (local.set $j (i32.const 0))
  (if (local.get $neg)
    (then
      (i32.store8 (local.get $dst_off) (i32.const 45))
      (local.set $j (i32.const 1))
    )
  )

  ;; Copy integer part with commas
  ;; First group may be 1, 2, or 3 digits
  (local.set $digit_count (i32.rem_u (local.get $integer_len) (i32.const 3)))
  (if (i32.eqz (local.get $digit_count))
    (then (local.set $digit_count (i32.const 3)))
  )

  ;; Copy first group
  (block $int_done
    (loop $int_loop
      (br_if $int_done (i32.ge_u (local.get $i) (local.get $decimal_pos)))
      ;; Copy digit
      (local.set $char (i32.load8_u (i32.add (local.get $src_off) (local.get $i))))
      (i32.store8 (i32.add (local.get $dst_off) (local.get $j)) (local.get $char))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (local.set $j (i32.add (local.get $j) (i32.const 1)))
      (local.set $digit_count (i32.sub (local.get $digit_count) (i32.const 1)))

      ;; If digit_count is 0 and more digits remain, add comma
      (if (i32.and
            (i32.eqz (local.get $digit_count))
            (i32.lt_u (local.get $i) (local.get $decimal_pos)))
        (then
          (i32.store8 (i32.add (local.get $dst_off) (local.get $j)) (i32.const 44))  ;; ','
          (local.set $j (i32.add (local.get $j) (i32.const 1)))
          (local.set $digit_count (i32.const 3))
        )
      )
      (br $int_loop)
    )
  )

  ;; Copy decimal part if present
  (block $dec_done
    (loop $dec_loop
      (br_if $dec_done (i32.ge_u (local.get $i) (local.get $src_len)))
      (local.set $char (i32.load8_u (i32.add (local.get $src_off) (local.get $i))))
      (i32.store8 (i32.add (local.get $dst_off) (local.get $j)) (local.get $char))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (local.set $j (i32.add (local.get $j) (i32.const 1)))
      (br $dec_loop)
    )
  )

  (struct.new $STRING (local.get $dst_off) (local.get $result_len))
)


;; format_align: pad string to width with alignment
;; align: 0=right, 1=left, 2=center
(func $format_align (param $s (ref $STRING)) (param $width i32) (param $fill i32) (param $align i32) (result (ref $STRING))
  (local $src_off i32)
  (local $src_len i32)
  (local $dst_off i32)
  (local $pad_total i32)
  (local $pad_left i32)
  (local $pad_right i32)
  (local $i i32)

  (local.set $src_off (struct.get $STRING 0 (local.get $s)))
  (local.set $src_len (struct.get $STRING 1 (local.get $s)))

  ;; If string is already wide enough, return as is
  (if (i32.ge_s (local.get $src_len) (local.get $width))
    (then (return (local.get $s)))
  )

  ;; Calculate padding
  (local.set $pad_total (i32.sub (local.get $width) (local.get $src_len)))

  ;; Calculate left and right padding based on alignment
  (if (i32.eq (local.get $align) (i32.const 0))  ;; right align
    (then
      (local.set $pad_left (local.get $pad_total))
      (local.set $pad_right (i32.const 0))
    )
    (else
      (if (i32.eq (local.get $align) (i32.const 1))  ;; left align
        (then
          (local.set $pad_left (i32.const 0))
          (local.set $pad_right (local.get $pad_total))
        )
        (else  ;; center align
          (local.set $pad_left (i32.div_u (local.get $pad_total) (i32.const 2)))
          (local.set $pad_right (i32.sub (local.get $pad_total) (local.get $pad_left)))
        )
      )
    )
  )

  ;; Allocate new string
  (local.set $dst_off (global.get $string_heap))
  (global.set $string_heap (i32.add (global.get $string_heap) (local.get $width)))

  ;; Write left padding
  (local.set $i (i32.const 0))
  (block $left_done
    (loop $left_loop
      (br_if $left_done (i32.ge_u (local.get $i) (local.get $pad_left)))
      (i32.store8 (i32.add (local.get $dst_off) (local.get $i)) (local.get $fill))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $left_loop)
    )
  )

  ;; Copy source string
  (local.set $i (i32.const 0))
  (block $copy_done
    (loop $copy_loop
      (br_if $copy_done (i32.ge_u (local.get $i) (local.get $src_len)))
      (i32.store8
        (i32.add (local.get $dst_off) (i32.add (local.get $pad_left) (local.get $i)))
        (i32.load8_u (i32.add (local.get $src_off) (local.get $i))))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $copy_loop)
    )
  )

  ;; Write right padding
  (local.set $i (i32.const 0))
  (block $right_done
    (loop $right_loop
      (br_if $right_done (i32.ge_u (local.get $i) (local.get $pad_right)))
      (i32.store8
        (i32.add (local.get $dst_off) (i32.add (i32.add (local.get $pad_left) (local.get $src_len)) (local.get $i)))
        (local.get $fill))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $right_loop)
    )
  )

  (struct.new $STRING (local.get $dst_off) (local.get $width))
)


;; string_add_quotes: wrap string with single quotes for repr()
(func $string_add_quotes (param $s (ref $STRING)) (result (ref $STRING))
  (local $off i32)
  (local $len i32)
  (local $new_off i32)
  (local $new_len i32)
  (local $i i32)
  (local.set $off (struct.get $STRING 0 (local.get $s)))
  (local.set $len (struct.get $STRING 1 (local.get $s)))
  ;; New length = original + 2 (for quotes)
  (local.set $new_len (i32.add (local.get $len) (i32.const 2)))
  (local.set $new_off (global.get $string_heap))
  (global.set $string_heap (i32.add (global.get $string_heap) (local.get $new_len)))
  ;; Write opening quote
  (i32.store8 (local.get $new_off) (i32.const 39))  ;; '
  ;; Copy original string
  (local.set $i (i32.const 0))
  (block $done
    (loop $loop
      (br_if $done (i32.ge_u (local.get $i) (local.get $len)))
      (i32.store8
        (i32.add (i32.add (local.get $new_off) (i32.const 1)) (local.get $i))
        (i32.load8_u (i32.add (local.get $off) (local.get $i))))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $loop)
    )
  )
  ;; Write closing quote
  (i32.store8 (i32.add (local.get $new_off) (i32.add (local.get $len) (i32.const 1))) (i32.const 39))  ;; '
  (struct.new $STRING (local.get $new_off) (local.get $new_len))
)


;; string_concat: concatenate two strings
(func $string_concat (param $a (ref $STRING)) (param $b (ref $STRING)) (result (ref $STRING))
  (local $a_off i32)
  (local $a_len i32)
  (local $b_off i32)
  (local $b_len i32)
  (local $new_off i32)
  (local $new_len i32)
  (local.set $a_off (struct.get $STRING 0 (local.get $a)))
  (local.set $a_len (struct.get $STRING 1 (local.get $a)))
  (local.set $b_off (struct.get $STRING 0 (local.get $b)))
  (local.set $b_len (struct.get $STRING 1 (local.get $b)))
  ;; Calculate new length
  (local.set $new_len (i32.add (local.get $a_len) (local.get $b_len)))
  ;; Ensure we have enough memory before allocating
  (call $ensure_memory (local.get $new_len))
  ;; Allocate space on the string heap
  (local.set $new_off (global.get $string_heap))
  (global.set $string_heap (i32.add (global.get $string_heap) (local.get $new_len)))
  ;; Copy first string using memory.copy (much faster than byte-by-byte)
  (memory.copy (local.get $new_off) (local.get $a_off) (local.get $a_len))
  ;; Copy second string
  (memory.copy
    (i32.add (local.get $new_off) (local.get $a_len))
    (local.get $b_off)
    (local.get $b_len))
  ;; Return new STRING struct
  (struct.new $STRING (local.get $new_off) (local.get $new_len))
)


;; string_contains: check if needle is in haystack
(func $string_contains (param $haystack (ref $STRING)) (param $needle (ref $STRING)) (result i32)
  (local $h_off i32)
  (local $h_len i32)
  (local $n_off i32)
  (local $n_len i32)
  (local $i i32)
  (local $j i32)
  (local $match i32)
  (local.set $h_off (struct.get $STRING 0 (local.get $haystack)))
  (local.set $h_len (struct.get $STRING 1 (local.get $haystack)))
  (local.set $n_off (struct.get $STRING 0 (local.get $needle)))
  (local.set $n_len (struct.get $STRING 1 (local.get $needle)))
  ;; Empty needle is always found
  (if (i32.eqz (local.get $n_len))
    (then (return (i32.const 1)))
  )
  ;; If needle is longer than haystack, not found
  (if (i32.gt_u (local.get $n_len) (local.get $h_len))
    (then (return (i32.const 0)))
  )
  ;; Search for needle
  (local.set $i (i32.const 0))
  (block $not_found
    (loop $search
      (br_if $not_found (i32.gt_u (i32.add (local.get $i) (local.get $n_len)) (local.get $h_len)))
      ;; Check if needle matches at position i
      (local.set $match (i32.const 1))
      (local.set $j (i32.const 0))
      (block $no_match
        (loop $compare
          (br_if $no_match (i32.ge_u (local.get $j) (local.get $n_len)))
          (if (i32.ne
                (i32.load8_u (i32.add (local.get $h_off) (i32.add (local.get $i) (local.get $j))))
                (i32.load8_u (i32.add (local.get $n_off) (local.get $j))))
            (then
              (local.set $match (i32.const 0))
              (br $no_match)
            )
          )
          (local.set $j (i32.add (local.get $j) (i32.const 1)))
          (br $compare)
        )
      )
      (if (local.get $match)
        (then (return (i32.const 1)))
      )
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $search)
    )
  )
  (i32.const 0)
)


;; String method: upper() - convert to uppercase
(func $string_upper (param $s (ref null eq)) (result (ref null eq))
  (local $str (ref null $STRING))
  (local $src_off i32)
  (local $src_len i32)
  (local $dst_off i32)
  (local $i i32)
  (local $c i32)

  (if (ref.is_null (local.get $s))
    (then (return (ref.null eq)))
  )
  (local.set $str (ref.cast (ref $STRING) (local.get $s)))
  (local.set $src_off (struct.get $STRING 0 (local.get $str)))
  (local.set $src_len (struct.get $STRING 1 (local.get $str)))

  ;; Allocate new string in heap
  (local.set $dst_off (global.get $string_heap))
  (global.set $string_heap (i32.add (global.get $string_heap) (local.get $src_len)))

  ;; Copy and convert
  (local.set $i (i32.const 0))
  (block $done
    (loop $loop
      (br_if $done (i32.ge_u (local.get $i) (local.get $src_len)))
      (local.set $c (i32.load8_u (i32.add (local.get $src_off) (local.get $i))))
      ;; Convert lowercase a-z to uppercase A-Z
      (if (i32.and (i32.ge_u (local.get $c) (i32.const 97))
                   (i32.le_u (local.get $c) (i32.const 122)))
        (then (local.set $c (i32.sub (local.get $c) (i32.const 32))))
      )
      (i32.store8 (i32.add (local.get $dst_off) (local.get $i)) (local.get $c))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $loop)
    )
  )
  (struct.new $STRING (local.get $dst_off) (local.get $src_len))
)


;; String method: lower() - convert to lowercase
(func $string_lower (param $s (ref null eq)) (result (ref null eq))
  (local $str (ref null $STRING))
  (local $src_off i32)
  (local $src_len i32)
  (local $dst_off i32)
  (local $i i32)
  (local $c i32)

  (if (ref.is_null (local.get $s))
    (then (return (ref.null eq)))
  )
  (local.set $str (ref.cast (ref $STRING) (local.get $s)))
  (local.set $src_off (struct.get $STRING 0 (local.get $str)))
  (local.set $src_len (struct.get $STRING 1 (local.get $str)))

  ;; Allocate new string in heap
  (local.set $dst_off (global.get $string_heap))
  (global.set $string_heap (i32.add (global.get $string_heap) (local.get $src_len)))

  ;; Copy and convert
  (local.set $i (i32.const 0))
  (block $done
    (loop $loop
      (br_if $done (i32.ge_u (local.get $i) (local.get $src_len)))
      (local.set $c (i32.load8_u (i32.add (local.get $src_off) (local.get $i))))
      ;; Convert uppercase A-Z to lowercase a-z
      (if (i32.and (i32.ge_u (local.get $c) (i32.const 65))
                   (i32.le_u (local.get $c) (i32.const 90)))
        (then (local.set $c (i32.add (local.get $c) (i32.const 32))))
      )
      (i32.store8 (i32.add (local.get $dst_off) (local.get $i)) (local.get $c))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $loop)
    )
  )
  (struct.new $STRING (local.get $dst_off) (local.get $src_len))
)


;; String method: capitalize() - first char upper, rest lower
(func $string_capitalize (param $s (ref null eq)) (result (ref null eq))
  (local $str (ref null $STRING))
  (local $src_off i32)
  (local $src_len i32)
  (local $dst_off i32)
  (local $i i32)
  (local $c i32)

  (if (ref.is_null (local.get $s))
    (then (return (ref.null eq)))
  )
  (local.set $str (ref.cast (ref $STRING) (local.get $s)))
  (local.set $src_off (struct.get $STRING 0 (local.get $str)))
  (local.set $src_len (struct.get $STRING 1 (local.get $str)))

  (if (i32.eq (local.get $src_len) (i32.const 0))
    (then (return (local.get $s)))
  )

  ;; Allocate new string in heap
  (local.set $dst_off (global.get $string_heap))
  (global.set $string_heap (i32.add (global.get $string_heap) (local.get $src_len)))

  ;; First character: uppercase
  (local.set $c (i32.load8_u (local.get $src_off)))
  (if (i32.and (i32.ge_u (local.get $c) (i32.const 97))
               (i32.le_u (local.get $c) (i32.const 122)))
    (then (local.set $c (i32.sub (local.get $c) (i32.const 32))))
  )
  (i32.store8 (local.get $dst_off) (local.get $c))

  ;; Rest: lowercase
  (local.set $i (i32.const 1))
  (block $done
    (loop $loop
      (br_if $done (i32.ge_u (local.get $i) (local.get $src_len)))
      (local.set $c (i32.load8_u (i32.add (local.get $src_off) (local.get $i))))
      (if (i32.and (i32.ge_u (local.get $c) (i32.const 65))
                   (i32.le_u (local.get $c) (i32.const 90)))
        (then (local.set $c (i32.add (local.get $c) (i32.const 32))))
      )
      (i32.store8 (i32.add (local.get $dst_off) (local.get $i)) (local.get $c))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $loop)
    )
  )
  (struct.new $STRING (local.get $dst_off) (local.get $src_len))
)


;; String method: title() - capitalize first char of each word
(func $string_title (param $s (ref null eq)) (result (ref null eq))
  (local $str (ref null $STRING))
  (local $src_off i32)
  (local $src_len i32)
  (local $dst_off i32)
  (local $i i32)
  (local $c i32)
  (local $new_word i32)

  (if (ref.is_null (local.get $s))
    (then (return (ref.null eq)))
  )
  (local.set $str (ref.cast (ref $STRING) (local.get $s)))
  (local.set $src_off (struct.get $STRING 0 (local.get $str)))
  (local.set $src_len (struct.get $STRING 1 (local.get $str)))

  (if (i32.eq (local.get $src_len) (i32.const 0))
    (then (return (local.get $s)))
  )

  ;; Allocate new string in heap
  (local.set $dst_off (global.get $string_heap))
  (global.set $string_heap (i32.add (global.get $string_heap) (local.get $src_len)))

  (local.set $new_word (i32.const 1))  ;; Start of string = new word
  (local.set $i (i32.const 0))
  (block $done
    (loop $loop
      (br_if $done (i32.ge_u (local.get $i) (local.get $src_len)))
      (local.set $c (i32.load8_u (i32.add (local.get $src_off) (local.get $i))))

      ;; Check if whitespace (space, tab, newline)
      (if (i32.or (i32.eq (local.get $c) (i32.const 32))
            (i32.or (i32.eq (local.get $c) (i32.const 9))
                    (i32.eq (local.get $c) (i32.const 10))))
        (then
          (local.set $new_word (i32.const 1))
        )
        (else
          (if (local.get $new_word)
            (then
              ;; Uppercase
              (if (i32.and (i32.ge_u (local.get $c) (i32.const 97))
                           (i32.le_u (local.get $c) (i32.const 122)))
                (then (local.set $c (i32.sub (local.get $c) (i32.const 32))))
              )
              (local.set $new_word (i32.const 0))
            )
            (else
              ;; Lowercase
              (if (i32.and (i32.ge_u (local.get $c) (i32.const 65))
                           (i32.le_u (local.get $c) (i32.const 90)))
                (then (local.set $c (i32.add (local.get $c) (i32.const 32))))
              )
            )
          )
        )
      )
      (i32.store8 (i32.add (local.get $dst_off) (local.get $i)) (local.get $c))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $loop)
    )
  )
  (struct.new $STRING (local.get $dst_off) (local.get $src_len))
)


;; String method: swapcase() - swap upper/lower case
(func $string_swapcase (param $s (ref null eq)) (result (ref null eq))
  (local $str (ref null $STRING))
  (local $src_off i32)
  (local $src_len i32)
  (local $dst_off i32)
  (local $i i32)
  (local $c i32)

  (if (ref.is_null (local.get $s))
    (then (return (ref.null eq)))
  )
  (local.set $str (ref.cast (ref $STRING) (local.get $s)))
  (local.set $src_off (struct.get $STRING 0 (local.get $str)))
  (local.set $src_len (struct.get $STRING 1 (local.get $str)))

  (local.set $dst_off (global.get $string_heap))
  (global.set $string_heap (i32.add (global.get $string_heap) (local.get $src_len)))

  (local.set $i (i32.const 0))
  (block $done
    (loop $loop
      (br_if $done (i32.ge_u (local.get $i) (local.get $src_len)))
      (local.set $c (i32.load8_u (i32.add (local.get $src_off) (local.get $i))))
      ;; If uppercase, make lowercase
      (if (i32.and (i32.ge_u (local.get $c) (i32.const 65))
                   (i32.le_u (local.get $c) (i32.const 90)))
        (then (local.set $c (i32.add (local.get $c) (i32.const 32))))
        (else
          ;; If lowercase, make uppercase
          (if (i32.and (i32.ge_u (local.get $c) (i32.const 97))
                       (i32.le_u (local.get $c) (i32.const 122)))
            (then (local.set $c (i32.sub (local.get $c) (i32.const 32))))
          )
        )
      )
      (i32.store8 (i32.add (local.get $dst_off) (local.get $i)) (local.get $c))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $loop)
    )
  )
  (struct.new $STRING (local.get $dst_off) (local.get $src_len))
)


;; String method: strip() - remove leading and trailing whitespace
(func $string_strip (param $s (ref null eq)) (result (ref null eq))
  (local $str (ref null $STRING))
  (local $off i32)
  (local $len i32)
  (local $start i32)
  (local $end i32)
  (local $c i32)
  (local $dst_off i32)
  (local $new_len i32)

  (if (ref.is_null (local.get $s))
    (then (return (ref.null eq)))
  )
  (local.set $str (ref.cast (ref $STRING) (local.get $s)))
  (local.set $off (struct.get $STRING 0 (local.get $str)))
  (local.set $len (struct.get $STRING 1 (local.get $str)))

  ;; Find start (first non-whitespace)
  (local.set $start (i32.const 0))
  (block $found_start
    (loop $loop
      (br_if $found_start (i32.ge_u (local.get $start) (local.get $len)))
      (local.set $c (i32.load8_u (i32.add (local.get $off) (local.get $start))))
      ;; Check for space, tab, newline, carriage return
      (br_if $found_start (i32.and
        (i32.ne (local.get $c) (i32.const 32))
        (i32.and (i32.ne (local.get $c) (i32.const 9))
        (i32.and (i32.ne (local.get $c) (i32.const 10))
                 (i32.ne (local.get $c) (i32.const 13))))))
      (local.set $start (i32.add (local.get $start) (i32.const 1)))
      (br $loop)
    )
  )

  ;; Find end (last non-whitespace)
  (local.set $end (local.get $len))
  (block $found_end
    (loop $loop
      (br_if $found_end (i32.le_u (local.get $end) (local.get $start)))
      (local.set $c (i32.load8_u (i32.add (local.get $off) (i32.sub (local.get $end) (i32.const 1)))))
      (br_if $found_end (i32.and
        (i32.ne (local.get $c) (i32.const 32))
        (i32.and (i32.ne (local.get $c) (i32.const 9))
        (i32.and (i32.ne (local.get $c) (i32.const 10))
                 (i32.ne (local.get $c) (i32.const 13))))))
      (local.set $end (i32.sub (local.get $end) (i32.const 1)))
      (br $loop)
    )
  )

  (local.set $new_len (i32.sub (local.get $end) (local.get $start)))
  (if (i32.le_s (local.get $new_len) (i32.const 0))
    (then (return (struct.new $STRING (i32.const 0) (i32.const 0))))
  )

  ;; Allocate and copy
  (local.set $dst_off (global.get $string_heap))
  (global.set $string_heap (i32.add (global.get $string_heap) (local.get $new_len)))
  (memory.copy (local.get $dst_off) (i32.add (local.get $off) (local.get $start)) (local.get $new_len))
  (struct.new $STRING (local.get $dst_off) (local.get $new_len))
)


;; String method: startswith(prefix)
(func $string_startswith (param $s (ref null eq)) (param $prefix (ref null eq)) (result (ref null eq))
  (local $str (ref null $STRING))
  (local $pre (ref null $STRING))
  (local $s_off i32)
  (local $s_len i32)
  (local $p_off i32)
  (local $p_len i32)
  (local $i i32)

  (if (i32.or (ref.is_null (local.get $s)) (ref.is_null (local.get $prefix)))
    (then (return (struct.new $BOOL (i32.const 0))))
  )
  (local.set $str (ref.cast (ref $STRING) (local.get $s)))
  (local.set $pre (ref.cast (ref $STRING) (local.get $prefix)))
  (local.set $s_off (struct.get $STRING 0 (local.get $str)))
  (local.set $s_len (struct.get $STRING 1 (local.get $str)))
  (local.set $p_off (struct.get $STRING 0 (local.get $pre)))
  (local.set $p_len (struct.get $STRING 1 (local.get $pre)))

  ;; Prefix longer than string -> False
  (if (i32.gt_u (local.get $p_len) (local.get $s_len))
    (then (return (struct.new $BOOL (i32.const 0))))
  )

  ;; Compare prefix
  (local.set $i (i32.const 0))
  (block $mismatch
    (loop $loop
      (br_if $mismatch (i32.ge_u (local.get $i) (local.get $p_len)))
      (if (i32.ne
            (i32.load8_u (i32.add (local.get $s_off) (local.get $i)))
            (i32.load8_u (i32.add (local.get $p_off) (local.get $i))))
        (then (return (struct.new $BOOL (i32.const 0))))
      )
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $loop)
    )
  )
  (struct.new $BOOL (i32.const 1))
)


;; String method: endswith(suffix)
(func $string_endswith (param $s (ref null eq)) (param $suffix (ref null eq)) (result (ref null eq))
  (local $str (ref null $STRING))
  (local $suf (ref null $STRING))
  (local $s_off i32)
  (local $s_len i32)
  (local $x_off i32)
  (local $x_len i32)
  (local $i i32)
  (local $start i32)

  (if (i32.or (ref.is_null (local.get $s)) (ref.is_null (local.get $suffix)))
    (then (return (struct.new $BOOL (i32.const 0))))
  )
  (local.set $str (ref.cast (ref $STRING) (local.get $s)))
  (local.set $suf (ref.cast (ref $STRING) (local.get $suffix)))
  (local.set $s_off (struct.get $STRING 0 (local.get $str)))
  (local.set $s_len (struct.get $STRING 1 (local.get $str)))
  (local.set $x_off (struct.get $STRING 0 (local.get $suf)))
  (local.set $x_len (struct.get $STRING 1 (local.get $suf)))

  ;; Suffix longer than string -> False
  (if (i32.gt_u (local.get $x_len) (local.get $s_len))
    (then (return (struct.new $BOOL (i32.const 0))))
  )

  ;; Compare suffix
  (local.set $start (i32.sub (local.get $s_len) (local.get $x_len)))
  (local.set $i (i32.const 0))
  (block $mismatch
    (loop $loop
      (br_if $mismatch (i32.ge_u (local.get $i) (local.get $x_len)))
      (if (i32.ne
            (i32.load8_u (i32.add (local.get $s_off) (i32.add (local.get $start) (local.get $i))))
            (i32.load8_u (i32.add (local.get $x_off) (local.get $i))))
        (then (return (struct.new $BOOL (i32.const 0))))
      )
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $loop)
    )
  )
  (struct.new $BOOL (i32.const 1))
)


;; String method: find(substring) -> int index or -1
(func $string_find (param $s (ref null eq)) (param $sub (ref null eq)) (result (ref null eq))
  (local $str (ref null $STRING))
  (local $needle (ref null $STRING))
  (local $h_off i32)
  (local $h_len i32)
  (local $n_off i32)
  (local $n_len i32)
  (local $i i32)
  (local $j i32)
  (local $match i32)

  (if (i32.or (ref.is_null (local.get $s)) (ref.is_null (local.get $sub)))
    (then (return (ref.i31 (i32.const -1))))
  )
  (local.set $str (ref.cast (ref $STRING) (local.get $s)))
  (local.set $needle (ref.cast (ref $STRING) (local.get $sub)))
  (local.set $h_off (struct.get $STRING 0 (local.get $str)))
  (local.set $h_len (struct.get $STRING 1 (local.get $str)))
  (local.set $n_off (struct.get $STRING 0 (local.get $needle)))
  (local.set $n_len (struct.get $STRING 1 (local.get $needle)))

  ;; Empty needle always found at position 0
  (if (i32.eqz (local.get $n_len))
    (then (return (ref.i31 (i32.const 0))))
  )

  ;; Search
  (local.set $i (i32.const 0))
  (block $not_found
    (loop $search
      (br_if $not_found (i32.gt_u (i32.add (local.get $i) (local.get $n_len)) (local.get $h_len)))
      (local.set $match (i32.const 1))
      (local.set $j (i32.const 0))
      (block $no_match
        (loop $compare
          (br_if $no_match (i32.ge_u (local.get $j) (local.get $n_len)))
          (if (i32.ne
                (i32.load8_u (i32.add (local.get $h_off) (i32.add (local.get $i) (local.get $j))))
                (i32.load8_u (i32.add (local.get $n_off) (local.get $j))))
            (then
              (local.set $match (i32.const 0))
              (br $no_match)
            )
          )
          (local.set $j (i32.add (local.get $j) (i32.const 1)))
          (br $compare)
        )
      )
      (if (local.get $match)
        (then (return (ref.i31 (local.get $i))))
      )
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $search)
    )
  )
  (ref.i31 (i32.const -1))
)


;; String method: isdigit() -> bool
(func $string_isdigit (param $s (ref null eq)) (result (ref null eq))
  (local $str (ref null $STRING))
  (local $off i32)
  (local $len i32)
  (local $i i32)
  (local $c i32)

  (if (ref.is_null (local.get $s))
    (then (return (struct.new $BOOL (i32.const 0))))
  )
  (local.set $str (ref.cast (ref $STRING) (local.get $s)))
  (local.set $off (struct.get $STRING 0 (local.get $str)))
  (local.set $len (struct.get $STRING 1 (local.get $str)))

  ;; Empty string returns False
  (if (i32.eqz (local.get $len))
    (then (return (struct.new $BOOL (i32.const 0))))
  )

  (local.set $i (i32.const 0))
  (block $not_digit
    (loop $loop
      (br_if $not_digit (i32.ge_u (local.get $i) (local.get $len)))
      (local.set $c (i32.load8_u (i32.add (local.get $off) (local.get $i))))
      (if (i32.or (i32.lt_u (local.get $c) (i32.const 48))
                  (i32.gt_u (local.get $c) (i32.const 57)))
        (then (return (struct.new $BOOL (i32.const 0))))
      )
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $loop)
    )
  )
  (struct.new $BOOL (i32.const 1))
)


;; String method: isalpha() -> bool
(func $string_isalpha (param $s (ref null eq)) (result (ref null eq))
  (local $str (ref null $STRING))
  (local $off i32)
  (local $len i32)
  (local $i i32)
  (local $c i32)

  (if (ref.is_null (local.get $s))
    (then (return (struct.new $BOOL (i32.const 0))))
  )
  (local.set $str (ref.cast (ref $STRING) (local.get $s)))
  (local.set $off (struct.get $STRING 0 (local.get $str)))
  (local.set $len (struct.get $STRING 1 (local.get $str)))

  ;; Empty string returns False
  (if (i32.eqz (local.get $len))
    (then (return (struct.new $BOOL (i32.const 0))))
  )

  (local.set $i (i32.const 0))
  (block $not_alpha
    (loop $loop
      (br_if $not_alpha (i32.ge_u (local.get $i) (local.get $len)))
      (local.set $c (i32.load8_u (i32.add (local.get $off) (local.get $i))))
      ;; Check if a-z or A-Z
      (if (i32.and
            (i32.or (i32.lt_u (local.get $c) (i32.const 65))
                    (i32.gt_u (local.get $c) (i32.const 90)))
            (i32.or (i32.lt_u (local.get $c) (i32.const 97))
                    (i32.gt_u (local.get $c) (i32.const 122))))
        (then (return (struct.new $BOOL (i32.const 0))))
      )
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $loop)
    )
  )
  (struct.new $BOOL (i32.const 1))
)


;; String method: isalnum() -> bool
(func $string_isalnum (param $s (ref null eq)) (result (ref null eq))
  (local $str (ref null $STRING))
  (local $off i32)
  (local $len i32)
  (local $i i32)
  (local $c i32)
  (local $is_alnum i32)

  (if (ref.is_null (local.get $s))
    (then (return (struct.new $BOOL (i32.const 0))))
  )
  (local.set $str (ref.cast (ref $STRING) (local.get $s)))
  (local.set $off (struct.get $STRING 0 (local.get $str)))
  (local.set $len (struct.get $STRING 1 (local.get $str)))

  ;; Empty string returns False
  (if (i32.eqz (local.get $len))
    (then (return (struct.new $BOOL (i32.const 0))))
  )

  (local.set $i (i32.const 0))
  (block $not_alnum
    (loop $loop
      (br_if $not_alnum (i32.ge_u (local.get $i) (local.get $len)))
      (local.set $c (i32.load8_u (i32.add (local.get $off) (local.get $i))))
      ;; Check if digit (0-9), uppercase (A-Z), or lowercase (a-z)
      (local.set $is_alnum
        (i32.or
          (i32.and (i32.ge_u (local.get $c) (i32.const 48))
                   (i32.le_u (local.get $c) (i32.const 57)))
          (i32.or
            (i32.and (i32.ge_u (local.get $c) (i32.const 65))
                     (i32.le_u (local.get $c) (i32.const 90)))
            (i32.and (i32.ge_u (local.get $c) (i32.const 97))
                     (i32.le_u (local.get $c) (i32.const 122))))))
      (if (i32.eqz (local.get $is_alnum))
        (then (return (struct.new $BOOL (i32.const 0))))
      )
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $loop)
    )
  )
  (struct.new $BOOL (i32.const 1))
)


;; String method: isspace() -> bool (all whitespace chars)
(func $string_isspace (param $s (ref null eq)) (result (ref null eq))
  (local $str (ref null $STRING))
  (local $off i32)
  (local $len i32)
  (local $i i32)
  (local $c i32)

  (if (ref.is_null (local.get $s))
    (then (return (struct.new $BOOL (i32.const 0))))
  )
  (local.set $str (ref.cast (ref $STRING) (local.get $s)))
  (local.set $off (struct.get $STRING 0 (local.get $str)))
  (local.set $len (struct.get $STRING 1 (local.get $str)))

  ;; Empty string returns False
  (if (i32.eqz (local.get $len))
    (then (return (struct.new $BOOL (i32.const 0))))
  )

  (local.set $i (i32.const 0))
  (block $not_space
    (loop $loop
      (br_if $not_space (i32.ge_u (local.get $i) (local.get $len)))
      (local.set $c (i32.load8_u (i32.add (local.get $off) (local.get $i))))
      ;; Check for space (32), tab (9), newline (10), carriage return (13)
      (if (i32.and
            (i32.and (i32.ne (local.get $c) (i32.const 32))
                     (i32.ne (local.get $c) (i32.const 9)))
            (i32.and (i32.ne (local.get $c) (i32.const 10))
                     (i32.ne (local.get $c) (i32.const 13))))
        (then (return (struct.new $BOOL (i32.const 0))))
      )
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $loop)
    )
  )
  (struct.new $BOOL (i32.const 1))
)


;; String method: islower() -> bool (all cased chars are lowercase)
(func $string_islower (param $s (ref null eq)) (result (ref null eq))
  (local $str (ref null $STRING))
  (local $off i32)
  (local $len i32)
  (local $i i32)
  (local $c i32)
  (local $has_cased i32)

  (if (ref.is_null (local.get $s))
    (then (return (struct.new $BOOL (i32.const 0))))
  )
  (local.set $str (ref.cast (ref $STRING) (local.get $s)))
  (local.set $off (struct.get $STRING 0 (local.get $str)))
  (local.set $len (struct.get $STRING 1 (local.get $str)))
  (local.set $has_cased (i32.const 0))

  (local.set $i (i32.const 0))
  (block $done
    (loop $loop
      (br_if $done (i32.ge_u (local.get $i) (local.get $len)))
      (local.set $c (i32.load8_u (i32.add (local.get $off) (local.get $i))))
      ;; If uppercase (A-Z), return False
      (if (i32.and (i32.ge_u (local.get $c) (i32.const 65))
                   (i32.le_u (local.get $c) (i32.const 90)))
        (then (return (struct.new $BOOL (i32.const 0))))
      )
      ;; If lowercase (a-z), mark has_cased
      (if (i32.and (i32.ge_u (local.get $c) (i32.const 97))
                   (i32.le_u (local.get $c) (i32.const 122)))
        (then (local.set $has_cased (i32.const 1)))
      )
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $loop)
    )
  )
  (struct.new $BOOL (local.get $has_cased))
)


;; String method: isupper() -> bool (all cased chars are uppercase)
(func $string_isupper (param $s (ref null eq)) (result (ref null eq))
  (local $str (ref null $STRING))
  (local $off i32)
  (local $len i32)
  (local $i i32)
  (local $c i32)
  (local $has_cased i32)

  (if (ref.is_null (local.get $s))
    (then (return (struct.new $BOOL (i32.const 0))))
  )
  (local.set $str (ref.cast (ref $STRING) (local.get $s)))
  (local.set $off (struct.get $STRING 0 (local.get $str)))
  (local.set $len (struct.get $STRING 1 (local.get $str)))
  (local.set $has_cased (i32.const 0))

  (local.set $i (i32.const 0))
  (block $done
    (loop $loop
      (br_if $done (i32.ge_u (local.get $i) (local.get $len)))
      (local.set $c (i32.load8_u (i32.add (local.get $off) (local.get $i))))
      ;; If lowercase (a-z), return False
      (if (i32.and (i32.ge_u (local.get $c) (i32.const 97))
                   (i32.le_u (local.get $c) (i32.const 122)))
        (then (return (struct.new $BOOL (i32.const 0))))
      )
      ;; If uppercase (A-Z), mark has_cased
      (if (i32.and (i32.ge_u (local.get $c) (i32.const 65))
                   (i32.le_u (local.get $c) (i32.const 90)))
        (then (local.set $has_cased (i32.const 1)))
      )
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $loop)
    )
  )
  (struct.new $BOOL (local.get $has_cased))
)


;; String method: rfind(sub) -> int (find from end)
(func $string_rfind (param $s (ref null eq)) (param $sub (ref null eq)) (result (ref null eq))
  (local $str (ref null $STRING))
  (local $needle (ref null $STRING))
  (local $h_off i32)
  (local $h_len i32)
  (local $n_off i32)
  (local $n_len i32)
  (local $i i32)
  (local $j i32)
  (local $match i32)

  (if (i32.or (ref.is_null (local.get $s)) (ref.is_null (local.get $sub)))
    (then (return (ref.i31 (i32.const -1))))
  )
  (local.set $str (ref.cast (ref $STRING) (local.get $s)))
  (local.set $needle (ref.cast (ref $STRING) (local.get $sub)))
  (local.set $h_off (struct.get $STRING 0 (local.get $str)))
  (local.set $h_len (struct.get $STRING 1 (local.get $str)))
  (local.set $n_off (struct.get $STRING 0 (local.get $needle)))
  (local.set $n_len (struct.get $STRING 1 (local.get $needle)))

  ;; Empty needle always found at end
  (if (i32.eqz (local.get $n_len))
    (then (return (ref.i31 (local.get $h_len))))
  )

  ;; Start from last valid position
  (if (i32.lt_u (local.get $h_len) (local.get $n_len))
    (then (return (ref.i31 (i32.const -1))))
  )
  (local.set $i (i32.sub (local.get $h_len) (local.get $n_len)))

  (block $not_found
    (loop $search
      ;; Check if match at position i
      (local.set $match (i32.const 1))
      (local.set $j (i32.const 0))
      (block $no_match
        (loop $compare
          (br_if $no_match (i32.ge_u (local.get $j) (local.get $n_len)))
          (if (i32.ne
                (i32.load8_u (i32.add (local.get $h_off) (i32.add (local.get $i) (local.get $j))))
                (i32.load8_u (i32.add (local.get $n_off) (local.get $j))))
            (then
              (local.set $match (i32.const 0))
              (br $no_match)
            )
          )
          (local.set $j (i32.add (local.get $j) (i32.const 1)))
          (br $compare)
        )
      )
      (if (local.get $match)
        (then (return (ref.i31 (local.get $i))))
      )
      ;; Move backwards
      (br_if $not_found (i32.eqz (local.get $i)))
      (local.set $i (i32.sub (local.get $i) (i32.const 1)))
      (br $search)
    )
  )
  (ref.i31 (i32.const -1))
)


;; String method: ljust(width) -> str (left-justify, pad on right)
(func $string_ljust (param $s (ref null eq)) (param $width (ref null eq)) (result (ref null eq))
  (local $str (ref null $STRING))
  (local $off i32)
  (local $len i32)
  (local $w i32)
  (local $pad i32)
  (local $new_off i32)
  (local $i i32)

  (if (ref.is_null (local.get $s))
    (then (return (ref.null eq)))
  )
  (local.set $str (ref.cast (ref $STRING) (local.get $s)))
  (local.set $off (struct.get $STRING 0 (local.get $str)))
  (local.set $len (struct.get $STRING 1 (local.get $str)))
  (local.set $w (i31.get_s (ref.cast (ref i31) (local.get $width))))

  ;; If already wide enough, return original
  (if (i32.ge_s (local.get $len) (local.get $w))
    (then (return (local.get $s)))
  )

  (local.set $pad (i32.sub (local.get $w) (local.get $len)))
  (local.set $new_off (global.get $string_heap))

  ;; Copy original string
  (local.set $i (i32.const 0))
  (block $done_copy
    (loop $copy
      (br_if $done_copy (i32.ge_u (local.get $i) (local.get $len)))
      (i32.store8 (i32.add (local.get $new_off) (local.get $i))
                  (i32.load8_u (i32.add (local.get $off) (local.get $i))))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $copy)
    )
  )

  ;; Add padding spaces
  (local.set $i (i32.const 0))
  (block $done_pad
    (loop $pad_loop
      (br_if $done_pad (i32.ge_u (local.get $i) (local.get $pad)))
      (i32.store8 (i32.add (local.get $new_off) (i32.add (local.get $len) (local.get $i)))
                  (i32.const 32))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $pad_loop)
    )
  )

  (global.set $string_heap (i32.add (local.get $new_off) (local.get $w)))
  (struct.new $STRING (local.get $new_off) (local.get $w))
)


;; String method: rjust(width) -> str (right-justify, pad on left)
(func $string_rjust (param $s (ref null eq)) (param $width (ref null eq)) (result (ref null eq))
  (local $str (ref null $STRING))
  (local $off i32)
  (local $len i32)
  (local $w i32)
  (local $pad i32)
  (local $new_off i32)
  (local $i i32)

  (if (ref.is_null (local.get $s))
    (then (return (ref.null eq)))
  )
  (local.set $str (ref.cast (ref $STRING) (local.get $s)))
  (local.set $off (struct.get $STRING 0 (local.get $str)))
  (local.set $len (struct.get $STRING 1 (local.get $str)))
  (local.set $w (i31.get_s (ref.cast (ref i31) (local.get $width))))

  ;; If already wide enough, return original
  (if (i32.ge_s (local.get $len) (local.get $w))
    (then (return (local.get $s)))
  )

  (local.set $pad (i32.sub (local.get $w) (local.get $len)))
  (local.set $new_off (global.get $string_heap))

  ;; Add padding spaces first
  (local.set $i (i32.const 0))
  (block $done_pad
    (loop $pad_loop
      (br_if $done_pad (i32.ge_u (local.get $i) (local.get $pad)))
      (i32.store8 (i32.add (local.get $new_off) (local.get $i)) (i32.const 32))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $pad_loop)
    )
  )

  ;; Copy original string after padding
  (local.set $i (i32.const 0))
  (block $done_copy
    (loop $copy
      (br_if $done_copy (i32.ge_u (local.get $i) (local.get $len)))
      (i32.store8 (i32.add (local.get $new_off) (i32.add (local.get $pad) (local.get $i)))
                  (i32.load8_u (i32.add (local.get $off) (local.get $i))))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $copy)
    )
  )

  (global.set $string_heap (i32.add (local.get $new_off) (local.get $w)))
  (struct.new $STRING (local.get $new_off) (local.get $w))
)


;; String method: center(width) -> str (center, pad on both sides)
(func $string_center (param $s (ref null eq)) (param $width (ref null eq)) (result (ref null eq))
  (local $str (ref null $STRING))
  (local $off i32)
  (local $len i32)
  (local $w i32)
  (local $total_pad i32)
  (local $left_pad i32)
  (local $right_pad i32)
  (local $new_off i32)
  (local $i i32)

  (if (ref.is_null (local.get $s))
    (then (return (ref.null eq)))
  )
  (local.set $str (ref.cast (ref $STRING) (local.get $s)))
  (local.set $off (struct.get $STRING 0 (local.get $str)))
  (local.set $len (struct.get $STRING 1 (local.get $str)))
  (local.set $w (i31.get_s (ref.cast (ref i31) (local.get $width))))

  ;; If already wide enough, return original
  (if (i32.ge_s (local.get $len) (local.get $w))
    (then (return (local.get $s)))
  )

  (local.set $total_pad (i32.sub (local.get $w) (local.get $len)))
  (local.set $left_pad (i32.div_u (local.get $total_pad) (i32.const 2)))
  (local.set $right_pad (i32.sub (local.get $total_pad) (local.get $left_pad)))
  (local.set $new_off (global.get $string_heap))

  ;; Add left padding
  (local.set $i (i32.const 0))
  (block $done_left
    (loop $left_loop
      (br_if $done_left (i32.ge_u (local.get $i) (local.get $left_pad)))
      (i32.store8 (i32.add (local.get $new_off) (local.get $i)) (i32.const 32))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $left_loop)
    )
  )

  ;; Copy original string
  (local.set $i (i32.const 0))
  (block $done_copy
    (loop $copy
      (br_if $done_copy (i32.ge_u (local.get $i) (local.get $len)))
      (i32.store8 (i32.add (local.get $new_off) (i32.add (local.get $left_pad) (local.get $i)))
                  (i32.load8_u (i32.add (local.get $off) (local.get $i))))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $copy)
    )
  )

  ;; Add right padding
  (local.set $i (i32.const 0))
  (block $done_right
    (loop $right_loop
      (br_if $done_right (i32.ge_u (local.get $i) (local.get $right_pad)))
      (i32.store8 (i32.add (local.get $new_off) (i32.add (local.get $left_pad) (i32.add (local.get $len) (local.get $i))))
                  (i32.const 32))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $right_loop)
    )
  )

  (global.set $string_heap (i32.add (local.get $new_off) (local.get $w)))
  (struct.new $STRING (local.get $new_off) (local.get $w))
)


;; String method: zfill(width) -> str (pad with zeros on left)
(func $string_zfill (param $s (ref null eq)) (param $width (ref null eq)) (result (ref null eq))
  (local $str (ref null $STRING))
  (local $off i32)
  (local $len i32)
  (local $w i32)
  (local $pad i32)
  (local $new_off i32)
  (local $i i32)
  (local $sign_char i32)
  (local $has_sign i32)

  (if (ref.is_null (local.get $s))
    (then (return (ref.null eq)))
  )
  (local.set $str (ref.cast (ref $STRING) (local.get $s)))
  (local.set $off (struct.get $STRING 0 (local.get $str)))
  (local.set $len (struct.get $STRING 1 (local.get $str)))
  (local.set $w (i31.get_s (ref.cast (ref i31) (local.get $width))))

  ;; If already wide enough, return original
  (if (i32.ge_s (local.get $len) (local.get $w))
    (then (return (local.get $s)))
  )

  (local.set $pad (i32.sub (local.get $w) (local.get $len)))
  (local.set $new_off (global.get $string_heap))
  (local.set $has_sign (i32.const 0))

  ;; Check for sign character at start
  (if (i32.and (i32.gt_s (local.get $len) (i32.const 0))
               (i32.or (i32.eq (i32.load8_u (local.get $off)) (i32.const 43))
                       (i32.eq (i32.load8_u (local.get $off)) (i32.const 45))))
    (then
      (local.set $has_sign (i32.const 1))
      (local.set $sign_char (i32.load8_u (local.get $off)))
      ;; Write sign first
      (i32.store8 (local.get $new_off) (local.get $sign_char))
    )
  )

  ;; Add zeros after sign (or at start if no sign)
  (local.set $i (i32.const 0))
  (block $done_zeros
    (loop $zero_loop
      (br_if $done_zeros (i32.ge_u (local.get $i) (local.get $pad)))
      (i32.store8 (i32.add (local.get $new_off) (i32.add (local.get $has_sign) (local.get $i)))
                  (i32.const 48))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $zero_loop)
    )
  )

  ;; Copy original string (skip sign if present)
  (local.set $i (local.get $has_sign))
  (block $done_copy
    (loop $copy
      (br_if $done_copy (i32.ge_u (local.get $i) (local.get $len)))
      (i32.store8 (i32.add (local.get $new_off) (i32.add (local.get $pad) (local.get $i)))
                  (i32.load8_u (i32.add (local.get $off) (local.get $i))))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $copy)
    )
  )

  (global.set $string_heap (i32.add (local.get $new_off) (local.get $w)))
  (struct.new $STRING (local.get $new_off) (local.get $w))
)


;; String method: lstrip() - remove leading whitespace
(func $string_lstrip (param $s (ref null eq)) (result (ref null eq))
  (local $str (ref null $STRING))
  (local $off i32)
  (local $len i32)
  (local $start i32)
  (local $c i32)
  (local $dst_off i32)
  (local $new_len i32)

  (if (ref.is_null (local.get $s))
    (then (return (ref.null eq)))
  )
  (local.set $str (ref.cast (ref $STRING) (local.get $s)))
  (local.set $off (struct.get $STRING 0 (local.get $str)))
  (local.set $len (struct.get $STRING 1 (local.get $str)))

  ;; Find start (first non-whitespace)
  (local.set $start (i32.const 0))
  (block $found
    (loop $loop
      (br_if $found (i32.ge_u (local.get $start) (local.get $len)))
      (local.set $c (i32.load8_u (i32.add (local.get $off) (local.get $start))))
      (br_if $found (i32.and
        (i32.ne (local.get $c) (i32.const 32))
        (i32.and (i32.ne (local.get $c) (i32.const 9))
        (i32.and (i32.ne (local.get $c) (i32.const 10))
                 (i32.ne (local.get $c) (i32.const 13))))))
      (local.set $start (i32.add (local.get $start) (i32.const 1)))
      (br $loop)
    )
  )

  (local.set $new_len (i32.sub (local.get $len) (local.get $start)))
  (if (i32.le_s (local.get $new_len) (i32.const 0))
    (then (return (struct.new $STRING (i32.const 0) (i32.const 0))))
  )

  (local.set $dst_off (global.get $string_heap))
  (global.set $string_heap (i32.add (global.get $string_heap) (local.get $new_len)))
  (memory.copy (local.get $dst_off) (i32.add (local.get $off) (local.get $start)) (local.get $new_len))
  (struct.new $STRING (local.get $dst_off) (local.get $new_len))
)


;; String method: rstrip() - remove trailing whitespace
(func $string_rstrip (param $s (ref null eq)) (result (ref null eq))
  (local $str (ref null $STRING))
  (local $off i32)
  (local $len i32)
  (local $end i32)
  (local $c i32)
  (local $dst_off i32)

  (if (ref.is_null (local.get $s))
    (then (return (ref.null eq)))
  )
  (local.set $str (ref.cast (ref $STRING) (local.get $s)))
  (local.set $off (struct.get $STRING 0 (local.get $str)))
  (local.set $len (struct.get $STRING 1 (local.get $str)))

  ;; Find end (last non-whitespace)
  (local.set $end (local.get $len))
  (block $found
    (loop $loop
      (br_if $found (i32.le_u (local.get $end) (i32.const 0)))
      (local.set $c (i32.load8_u (i32.add (local.get $off) (i32.sub (local.get $end) (i32.const 1)))))
      (br_if $found (i32.and
        (i32.ne (local.get $c) (i32.const 32))
        (i32.and (i32.ne (local.get $c) (i32.const 9))
        (i32.and (i32.ne (local.get $c) (i32.const 10))
                 (i32.ne (local.get $c) (i32.const 13))))))
      (local.set $end (i32.sub (local.get $end) (i32.const 1)))
      (br $loop)
    )
  )

  (if (i32.le_s (local.get $end) (i32.const 0))
    (then (return (struct.new $STRING (i32.const 0) (i32.const 0))))
  )

  (local.set $dst_off (global.get $string_heap))
  (global.set $string_heap (i32.add (global.get $string_heap) (local.get $end)))
  (memory.copy (local.get $dst_off) (local.get $off) (local.get $end))
  (struct.new $STRING (local.get $dst_off) (local.get $end))
)


;; Helper: check if character is in a string
(func $char_in_string (param $c i32) (param $chars (ref null $STRING)) (result i32)
  (local $chars_off i32)
  (local $chars_len i32)
  (local $i i32)

  (local.set $chars_off (struct.get $STRING 0 (local.get $chars)))
  (local.set $chars_len (struct.get $STRING 1 (local.get $chars)))

  (local.set $i (i32.const 0))
  (block $not_found
    (loop $loop
      (br_if $not_found (i32.ge_u (local.get $i) (local.get $chars_len)))
      (if (i32.eq (local.get $c) (i32.load8_u (i32.add (local.get $chars_off) (local.get $i))))
        (then (return (i32.const 1)))
      )
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $loop)
    )
  )
  (i32.const 0)
)


;; String method: strip(chars) - remove leading/trailing chars
(func $string_strip_chars (param $s (ref null eq)) (param $chars (ref null eq)) (result (ref null eq))
  (local $str (ref null $STRING))
  (local $chars_str (ref null $STRING))
  (local $off i32)
  (local $len i32)
  (local $start i32)
  (local $end i32)
  (local $c i32)
  (local $dst_off i32)
  (local $new_len i32)

  (if (ref.is_null (local.get $s))
    (then (return (ref.null eq)))
  )
  (if (ref.is_null (local.get $chars))
    (then (return (call $string_strip (local.get $s))))
  )

  (local.set $str (ref.cast (ref $STRING) (local.get $s)))
  (local.set $chars_str (ref.cast (ref $STRING) (local.get $chars)))
  (local.set $off (struct.get $STRING 0 (local.get $str)))
  (local.set $len (struct.get $STRING 1 (local.get $str)))

  ;; Find start (first char not in chars)
  (local.set $start (i32.const 0))
  (block $found_start
    (loop $loop
      (br_if $found_start (i32.ge_u (local.get $start) (local.get $len)))
      (local.set $c (i32.load8_u (i32.add (local.get $off) (local.get $start))))
      (br_if $found_start (i32.eqz (call $char_in_string (local.get $c) (local.get $chars_str))))
      (local.set $start (i32.add (local.get $start) (i32.const 1)))
      (br $loop)
    )
  )

  ;; Find end (last char not in chars)
  (local.set $end (local.get $len))
  (block $found_end
    (loop $loop
      (br_if $found_end (i32.le_u (local.get $end) (local.get $start)))
      (local.set $c (i32.load8_u (i32.add (local.get $off) (i32.sub (local.get $end) (i32.const 1)))))
      (br_if $found_end (i32.eqz (call $char_in_string (local.get $c) (local.get $chars_str))))
      (local.set $end (i32.sub (local.get $end) (i32.const 1)))
      (br $loop)
    )
  )

  (local.set $new_len (i32.sub (local.get $end) (local.get $start)))
  (if (i32.le_s (local.get $new_len) (i32.const 0))
    (then (return (struct.new $STRING (i32.const 0) (i32.const 0))))
  )

  ;; Allocate and copy
  (local.set $dst_off (global.get $string_heap))
  (global.set $string_heap (i32.add (global.get $string_heap) (local.get $new_len)))
  (memory.copy (local.get $dst_off) (i32.add (local.get $off) (local.get $start)) (local.get $new_len))
  (struct.new $STRING (local.get $dst_off) (local.get $new_len))
)


;; String method: lstrip(chars) - remove leading chars
(func $string_lstrip_chars (param $s (ref null eq)) (param $chars (ref null eq)) (result (ref null eq))
  (local $str (ref null $STRING))
  (local $chars_str (ref null $STRING))
  (local $off i32)
  (local $len i32)
  (local $start i32)
  (local $c i32)
  (local $dst_off i32)
  (local $new_len i32)

  (if (ref.is_null (local.get $s))
    (then (return (ref.null eq)))
  )
  (if (ref.is_null (local.get $chars))
    (then (return (call $string_lstrip (local.get $s))))
  )

  (local.set $str (ref.cast (ref $STRING) (local.get $s)))
  (local.set $chars_str (ref.cast (ref $STRING) (local.get $chars)))
  (local.set $off (struct.get $STRING 0 (local.get $str)))
  (local.set $len (struct.get $STRING 1 (local.get $str)))

  ;; Find start (first char not in chars)
  (local.set $start (i32.const 0))
  (block $found
    (loop $loop
      (br_if $found (i32.ge_u (local.get $start) (local.get $len)))
      (local.set $c (i32.load8_u (i32.add (local.get $off) (local.get $start))))
      (br_if $found (i32.eqz (call $char_in_string (local.get $c) (local.get $chars_str))))
      (local.set $start (i32.add (local.get $start) (i32.const 1)))
      (br $loop)
    )
  )

  (local.set $new_len (i32.sub (local.get $len) (local.get $start)))
  (if (i32.le_s (local.get $new_len) (i32.const 0))
    (then (return (struct.new $STRING (i32.const 0) (i32.const 0))))
  )

  (local.set $dst_off (global.get $string_heap))
  (global.set $string_heap (i32.add (global.get $string_heap) (local.get $new_len)))
  (memory.copy (local.get $dst_off) (i32.add (local.get $off) (local.get $start)) (local.get $new_len))
  (struct.new $STRING (local.get $dst_off) (local.get $new_len))
)


;; String method: rstrip(chars) - remove trailing chars
(func $string_rstrip_chars (param $s (ref null eq)) (param $chars (ref null eq)) (result (ref null eq))
  (local $str (ref null $STRING))
  (local $chars_str (ref null $STRING))
  (local $off i32)
  (local $len i32)
  (local $end i32)
  (local $c i32)
  (local $dst_off i32)

  (if (ref.is_null (local.get $s))
    (then (return (ref.null eq)))
  )
  (if (ref.is_null (local.get $chars))
    (then (return (call $string_rstrip (local.get $s))))
  )

  (local.set $str (ref.cast (ref $STRING) (local.get $s)))
  (local.set $chars_str (ref.cast (ref $STRING) (local.get $chars)))
  (local.set $off (struct.get $STRING 0 (local.get $str)))
  (local.set $len (struct.get $STRING 1 (local.get $str)))

  ;; Find end (last char not in chars)
  (local.set $end (local.get $len))
  (block $found
    (loop $loop
      (br_if $found (i32.le_u (local.get $end) (i32.const 0)))
      (local.set $c (i32.load8_u (i32.add (local.get $off) (i32.sub (local.get $end) (i32.const 1)))))
      (br_if $found (i32.eqz (call $char_in_string (local.get $c) (local.get $chars_str))))
      (local.set $end (i32.sub (local.get $end) (i32.const 1)))
      (br $loop)
    )
  )

  (if (i32.le_s (local.get $end) (i32.const 0))
    (then (return (struct.new $STRING (i32.const 0) (i32.const 0))))
  )

  (local.set $dst_off (global.get $string_heap))
  (global.set $string_heap (i32.add (global.get $string_heap) (local.get $end)))
  (memory.copy (local.get $dst_off) (local.get $off) (local.get $end))
  (struct.new $STRING (local.get $dst_off) (local.get $end))
)


;; String method: replace(old, new) - replace all occurrences
(func $string_replace (param $s (ref null eq)) (param $old (ref null eq)) (param $new (ref null eq)) (result (ref null eq))
  (local $str (ref null $STRING))
  (local $old_str (ref null $STRING))
  (local $new_str (ref null $STRING))
  (local $s_off i32)
  (local $s_len i32)
  (local $o_off i32)
  (local $o_len i32)
  (local $n_off i32)
  (local $n_len i32)
  (local $dst_off i32)
  (local $i i32)
  (local $j i32)
  (local $k i32)
  (local $match i32)
  (local $dst_pos i32)

  (if (i32.or (ref.is_null (local.get $s))
              (i32.or (ref.is_null (local.get $old)) (ref.is_null (local.get $new))))
    (then (return (local.get $s)))
  )

  (local.set $str (ref.cast (ref $STRING) (local.get $s)))
  (local.set $old_str (ref.cast (ref $STRING) (local.get $old)))
  (local.set $new_str (ref.cast (ref $STRING) (local.get $new)))
  (local.set $s_off (struct.get $STRING 0 (local.get $str)))
  (local.set $s_len (struct.get $STRING 1 (local.get $str)))
  (local.set $o_off (struct.get $STRING 0 (local.get $old_str)))
  (local.set $o_len (struct.get $STRING 1 (local.get $old_str)))
  (local.set $n_off (struct.get $STRING 0 (local.get $new_str)))
  (local.set $n_len (struct.get $STRING 1 (local.get $new_str)))

  ;; Empty old string - return original
  (if (i32.eqz (local.get $o_len))
    (then (return (local.get $s)))
  )

  ;; Allocate generous space (assume worst case)
  (local.set $dst_off (global.get $string_heap))
  (local.set $dst_pos (i32.const 0))
  (local.set $i (i32.const 0))

  (block $done
    (loop $loop
      (br_if $done (i32.ge_u (local.get $i) (local.get $s_len)))

      ;; Check for match at position i
      (local.set $match (i32.const 1))
      (if (i32.le_u (i32.add (local.get $i) (local.get $o_len)) (local.get $s_len))
        (then
          (local.set $j (i32.const 0))
          (block $no_match
            (loop $cmp
              (br_if $no_match (i32.ge_u (local.get $j) (local.get $o_len)))
              (if (i32.ne
                    (i32.load8_u (i32.add (local.get $s_off) (i32.add (local.get $i) (local.get $j))))
                    (i32.load8_u (i32.add (local.get $o_off) (local.get $j))))
                (then
                  (local.set $match (i32.const 0))
                  (br $no_match)
                )
              )
              (local.set $j (i32.add (local.get $j) (i32.const 1)))
              (br $cmp)
            )
          )
        )
        (else (local.set $match (i32.const 0)))
      )

      (if (local.get $match)
        (then
          ;; Copy replacement
          (local.set $k (i32.const 0))
          (block $copy_new_done
            (loop $copy_new
              (br_if $copy_new_done (i32.ge_u (local.get $k) (local.get $n_len)))
              (i32.store8 (i32.add (local.get $dst_off) (local.get $dst_pos))
                          (i32.load8_u (i32.add (local.get $n_off) (local.get $k))))
              (local.set $dst_pos (i32.add (local.get $dst_pos) (i32.const 1)))
              (local.set $k (i32.add (local.get $k) (i32.const 1)))
              (br $copy_new)
            )
          )
          (local.set $i (i32.add (local.get $i) (local.get $o_len)))
        )
        (else
          ;; Copy original character
          (i32.store8 (i32.add (local.get $dst_off) (local.get $dst_pos))
                      (i32.load8_u (i32.add (local.get $s_off) (local.get $i))))
          (local.set $dst_pos (i32.add (local.get $dst_pos) (i32.const 1)))
          (local.set $i (i32.add (local.get $i) (i32.const 1)))
        )
      )
      (br $loop)
    )
  )

  (global.set $string_heap (i32.add (global.get $string_heap) (local.get $dst_pos)))
  (struct.new $STRING (local.get $dst_off) (local.get $dst_pos))
)


;; String method: replace(old, new, count) - replace with limit
(func $string_replace_count (param $s (ref null eq)) (param $old (ref null eq)) (param $new (ref null eq)) (param $count_arg (ref null eq)) (result (ref null eq))
  (local $str (ref null $STRING))
  (local $old_str (ref null $STRING))
  (local $new_str (ref null $STRING))
  (local $s_off i32)
  (local $s_len i32)
  (local $o_off i32)
  (local $o_len i32)
  (local $n_off i32)
  (local $n_len i32)
  (local $dst_off i32)
  (local $i i32)
  (local $j i32)
  (local $k i32)
  (local $match i32)
  (local $dst_pos i32)
  (local $max_count i32)
  (local $replace_count i32)

  (if (i32.or (ref.is_null (local.get $s))
              (i32.or (ref.is_null (local.get $old)) (ref.is_null (local.get $new))))
    (then (return (local.get $s)))
  )

  (local.set $str (ref.cast (ref $STRING) (local.get $s)))
  (local.set $old_str (ref.cast (ref $STRING) (local.get $old)))
  (local.set $new_str (ref.cast (ref $STRING) (local.get $new)))
  (local.set $s_off (struct.get $STRING 0 (local.get $str)))
  (local.set $s_len (struct.get $STRING 1 (local.get $str)))
  (local.set $o_off (struct.get $STRING 0 (local.get $old_str)))
  (local.set $o_len (struct.get $STRING 1 (local.get $old_str)))
  (local.set $n_off (struct.get $STRING 0 (local.get $new_str)))
  (local.set $n_len (struct.get $STRING 1 (local.get $new_str)))

  ;; Get max count (-1 for unlimited)
  (if (ref.is_null (local.get $count_arg))
    (then (local.set $max_count (i32.const -1)))
    (else (local.set $max_count (i31.get_s (ref.cast (ref i31) (local.get $count_arg)))))
  )

  ;; Empty old string - return original
  (if (i32.eqz (local.get $o_len))
    (then (return (local.get $s)))
  )

  ;; Allocate generous space (assume worst case)
  (local.set $dst_off (global.get $string_heap))
  (local.set $dst_pos (i32.const 0))
  (local.set $i (i32.const 0))
  (local.set $replace_count (i32.const 0))

  (block $done
    (loop $loop
      (br_if $done (i32.ge_u (local.get $i) (local.get $s_len)))

      ;; Check if we've reached max replacements
      (if (i32.and (i32.ge_s (local.get $max_count) (i32.const 0))
                   (i32.ge_s (local.get $replace_count) (local.get $max_count)))
        (then
          ;; Copy rest of string verbatim
          (block $copy_rest_done
            (loop $copy_rest
              (br_if $copy_rest_done (i32.ge_u (local.get $i) (local.get $s_len)))
              (i32.store8 (i32.add (local.get $dst_off) (local.get $dst_pos))
                          (i32.load8_u (i32.add (local.get $s_off) (local.get $i))))
              (local.set $dst_pos (i32.add (local.get $dst_pos) (i32.const 1)))
              (local.set $i (i32.add (local.get $i) (i32.const 1)))
              (br $copy_rest)
            )
          )
          (br $done)
        )
      )

      ;; Check for match at position i
      (local.set $match (i32.const 1))
      (if (i32.le_u (i32.add (local.get $i) (local.get $o_len)) (local.get $s_len))
        (then
          (local.set $j (i32.const 0))
          (block $no_match
            (loop $cmp
              (br_if $no_match (i32.ge_u (local.get $j) (local.get $o_len)))
              (if (i32.ne
                    (i32.load8_u (i32.add (local.get $s_off) (i32.add (local.get $i) (local.get $j))))
                    (i32.load8_u (i32.add (local.get $o_off) (local.get $j))))
                (then
                  (local.set $match (i32.const 0))
                  (br $no_match)
                )
              )
              (local.set $j (i32.add (local.get $j) (i32.const 1)))
              (br $cmp)
            )
          )
        )
        (else (local.set $match (i32.const 0)))
      )

      (if (local.get $match)
        (then
          ;; Copy replacement
          (local.set $k (i32.const 0))
          (block $copy_new_done
            (loop $copy_new
              (br_if $copy_new_done (i32.ge_u (local.get $k) (local.get $n_len)))
              (i32.store8 (i32.add (local.get $dst_off) (local.get $dst_pos))
                          (i32.load8_u (i32.add (local.get $n_off) (local.get $k))))
              (local.set $dst_pos (i32.add (local.get $dst_pos) (i32.const 1)))
              (local.set $k (i32.add (local.get $k) (i32.const 1)))
              (br $copy_new)
            )
          )
          (local.set $i (i32.add (local.get $i) (local.get $o_len)))
          (local.set $replace_count (i32.add (local.get $replace_count) (i32.const 1)))
        )
        (else
          ;; Copy original character
          (i32.store8 (i32.add (local.get $dst_off) (local.get $dst_pos))
                      (i32.load8_u (i32.add (local.get $s_off) (local.get $i))))
          (local.set $dst_pos (i32.add (local.get $dst_pos) (i32.const 1)))
          (local.set $i (i32.add (local.get $i) (i32.const 1)))
        )
      )
      (br $loop)
    )
  )

  (global.set $string_heap (i32.add (global.get $string_heap) (local.get $dst_pos)))
  (struct.new $STRING (local.get $dst_off) (local.get $dst_pos))
)


;; String method: count(sub) - count occurrences
(func $string_count (param $s (ref null eq)) (param $sub (ref null eq)) (result (ref null eq))
  (local $str (ref null $STRING))
  (local $needle (ref null $STRING))
  (local $h_off i32)
  (local $h_len i32)
  (local $n_off i32)
  (local $n_len i32)
  (local $i i32)
  (local $j i32)
  (local $match i32)
  (local $count i32)

  (if (i32.or (ref.is_null (local.get $s)) (ref.is_null (local.get $sub)))
    (then (return (ref.i31 (i32.const 0))))
  )
  (local.set $str (ref.cast (ref $STRING) (local.get $s)))
  (local.set $needle (ref.cast (ref $STRING) (local.get $sub)))
  (local.set $h_off (struct.get $STRING 0 (local.get $str)))
  (local.set $h_len (struct.get $STRING 1 (local.get $str)))
  (local.set $n_off (struct.get $STRING 0 (local.get $needle)))
  (local.set $n_len (struct.get $STRING 1 (local.get $needle)))

  ;; Empty needle -> 0
  (if (i32.eqz (local.get $n_len))
    (then (return (ref.i31 (i32.const 0))))
  )

  (local.set $count (i32.const 0))
  (local.set $i (i32.const 0))
  (block $done
    (loop $search
      (br_if $done (i32.gt_u (i32.add (local.get $i) (local.get $n_len)) (local.get $h_len)))
      (local.set $match (i32.const 1))
      (local.set $j (i32.const 0))
      (block $no_match
        (loop $compare
          (br_if $no_match (i32.ge_u (local.get $j) (local.get $n_len)))
          (if (i32.ne
                (i32.load8_u (i32.add (local.get $h_off) (i32.add (local.get $i) (local.get $j))))
                (i32.load8_u (i32.add (local.get $n_off) (local.get $j))))
            (then
              (local.set $match (i32.const 0))
              (br $no_match)
            )
          )
          (local.set $j (i32.add (local.get $j) (i32.const 1)))
          (br $compare)
        )
      )
      (if (local.get $match)
        (then
          (local.set $count (i32.add (local.get $count) (i32.const 1)))
          (local.set $i (i32.add (local.get $i) (local.get $n_len)))
        )
        (else
          (local.set $i (i32.add (local.get $i) (i32.const 1)))
        )
      )
      (br $search)
    )
  )
  (ref.i31 (local.get $count))
)


;; String method: split(sep) - split string by separator, return list
(func $string_split (param $s (ref null eq)) (param $sep (ref null eq)) (result (ref null eq))
  (local $str (ref null $STRING))
  (local $sep_str (ref null $STRING))
  (local $s_off i32)
  (local $s_len i32)
  (local $sep_off i32)
  (local $sep_len i32)
  (local $i i32)
  (local $j i32)
  (local $start i32)
  (local $match i32)
  (local $result (ref null eq))
  (local $part_off i32)
  (local $part_len i32)

  (if (i32.or (ref.is_null (local.get $s)) (ref.is_null (local.get $sep)))
    (then (return (ref.null eq)))
  )
  (local.set $str (ref.cast (ref $STRING) (local.get $s)))
  (local.set $sep_str (ref.cast (ref $STRING) (local.get $sep)))
  (local.set $s_off (struct.get $STRING 0 (local.get $str)))
  (local.set $s_len (struct.get $STRING 1 (local.get $str)))
  (local.set $sep_off (struct.get $STRING 0 (local.get $sep_str)))
  (local.set $sep_len (struct.get $STRING 1 (local.get $sep_str)))

  ;; Empty separator -> return list with original string
  (if (i32.eqz (local.get $sep_len))
    (then
      (return (struct.new $PAIR (local.get $s) (ref.null eq)))
    )
  )

  (local.set $result (ref.null eq))
  (local.set $start (i32.const 0))
  (local.set $i (i32.const 0))

  (block $done
    (loop $search
      ;; Check if we're past the end
      (if (i32.gt_u (i32.add (local.get $i) (local.get $sep_len)) (local.get $s_len))
        (then
          ;; Add final part
          (local.set $part_len (i32.sub (local.get $s_len) (local.get $start)))
          (local.set $part_off (global.get $string_heap))
          (global.set $string_heap (i32.add (global.get $string_heap) (local.get $part_len)))
          (if (i32.gt_s (local.get $part_len) (i32.const 0))
            (then
              (memory.copy (local.get $part_off) (i32.add (local.get $s_off) (local.get $start)) (local.get $part_len))
            )
          )
          (local.set $result
            (struct.new $PAIR
              (struct.new $STRING (local.get $part_off) (local.get $part_len))
              (local.get $result)))
          (br $done)
        )
      )

      ;; Check for separator match at i
      (local.set $match (i32.const 1))
      (local.set $j (i32.const 0))
      (block $no_match
        (loop $cmp
          (br_if $no_match (i32.ge_u (local.get $j) (local.get $sep_len)))
          (if (i32.ne
                (i32.load8_u (i32.add (local.get $s_off) (i32.add (local.get $i) (local.get $j))))
                (i32.load8_u (i32.add (local.get $sep_off) (local.get $j))))
            (then
              (local.set $match (i32.const 0))
              (br $no_match)
            )
          )
          (local.set $j (i32.add (local.get $j) (i32.const 1)))
          (br $cmp)
        )
      )

      (if (local.get $match)
        (then
          ;; Found separator - add part to result
          (local.set $part_len (i32.sub (local.get $i) (local.get $start)))
          (local.set $part_off (global.get $string_heap))
          (global.set $string_heap (i32.add (global.get $string_heap) (local.get $part_len)))
          (if (i32.gt_s (local.get $part_len) (i32.const 0))
            (then
              (memory.copy (local.get $part_off) (i32.add (local.get $s_off) (local.get $start)) (local.get $part_len))
            )
          )
          (local.set $result
            (struct.new $PAIR
              (struct.new $STRING (local.get $part_off) (local.get $part_len))
              (local.get $result)))
          (local.set $i (i32.add (local.get $i) (local.get $sep_len)))
          (local.set $start (local.get $i))
        )
        (else
          (local.set $i (i32.add (local.get $i) (i32.const 1)))
        )
      )
      (br $search)
    )
  )

  ;; Reverse the result list (we built it backwards)
  (call $list_reverse (local.get $result))
)


;; String method: split(sep, maxsplit) - split string by separator with limit
(func $string_split_max (param $s (ref null eq)) (param $sep (ref null eq)) (param $maxsplit (ref null eq)) (result (ref null eq))
  (local $str (ref null $STRING))
  (local $sep_str (ref null $STRING))
  (local $s_off i32)
  (local $s_len i32)
  (local $sep_off i32)
  (local $sep_len i32)
  (local $i i32)
  (local $j i32)
  (local $start i32)
  (local $match i32)
  (local $result (ref null eq))
  (local $part_off i32)
  (local $part_len i32)
  (local $max i32)
  (local $splits i32)

  (if (i32.or (ref.is_null (local.get $s)) (ref.is_null (local.get $sep)))
    (then (return (ref.null eq)))
  )
  (local.set $str (ref.cast (ref $STRING) (local.get $s)))
  (local.set $sep_str (ref.cast (ref $STRING) (local.get $sep)))
  (local.set $s_off (struct.get $STRING 0 (local.get $str)))
  (local.set $s_len (struct.get $STRING 1 (local.get $str)))
  (local.set $sep_off (struct.get $STRING 0 (local.get $sep_str)))
  (local.set $sep_len (struct.get $STRING 1 (local.get $sep_str)))

  ;; Get maxsplit value (default -1 for no limit)
  (if (ref.is_null (local.get $maxsplit))
    (then (local.set $max (i32.const -1)))
    (else (local.set $max (i31.get_s (ref.cast (ref i31) (local.get $maxsplit)))))
  )

  ;; Empty separator -> return list with original string
  (if (i32.eqz (local.get $sep_len))
    (then
      (return (struct.new $PAIR (local.get $s) (ref.null eq)))
    )
  )

  (local.set $result (ref.null eq))
  (local.set $start (i32.const 0))
  (local.set $i (i32.const 0))
  (local.set $splits (i32.const 0))

  (block $done
    (loop $search
      ;; Check if we've done enough splits (if max is set)
      (if (i32.and (i32.ge_s (local.get $max) (i32.const 0))
                   (i32.ge_s (local.get $splits) (local.get $max)))
        (then
          ;; Add rest of string as final part
          (local.set $part_len (i32.sub (local.get $s_len) (local.get $start)))
          (local.set $part_off (global.get $string_heap))
          (global.set $string_heap (i32.add (global.get $string_heap) (local.get $part_len)))
          (if (i32.gt_s (local.get $part_len) (i32.const 0))
            (then
              (memory.copy (local.get $part_off) (i32.add (local.get $s_off) (local.get $start)) (local.get $part_len))
            )
          )
          (local.set $result
            (struct.new $PAIR
              (struct.new $STRING (local.get $part_off) (local.get $part_len))
              (local.get $result)))
          (br $done)
        )
      )

      ;; Check if we're past the end
      (if (i32.gt_u (i32.add (local.get $i) (local.get $sep_len)) (local.get $s_len))
        (then
          ;; Add final part
          (local.set $part_len (i32.sub (local.get $s_len) (local.get $start)))
          (local.set $part_off (global.get $string_heap))
          (global.set $string_heap (i32.add (global.get $string_heap) (local.get $part_len)))
          (if (i32.gt_s (local.get $part_len) (i32.const 0))
            (then
              (memory.copy (local.get $part_off) (i32.add (local.get $s_off) (local.get $start)) (local.get $part_len))
            )
          )
          (local.set $result
            (struct.new $PAIR
              (struct.new $STRING (local.get $part_off) (local.get $part_len))
              (local.get $result)))
          (br $done)
        )
      )

      ;; Check for separator match at i
      (local.set $match (i32.const 1))
      (local.set $j (i32.const 0))
      (block $no_match
        (loop $cmp
          (br_if $no_match (i32.ge_u (local.get $j) (local.get $sep_len)))
          (if (i32.ne
                (i32.load8_u (i32.add (local.get $s_off) (i32.add (local.get $i) (local.get $j))))
                (i32.load8_u (i32.add (local.get $sep_off) (local.get $j))))
            (then
              (local.set $match (i32.const 0))
              (br $no_match)
            )
          )
          (local.set $j (i32.add (local.get $j) (i32.const 1)))
          (br $cmp)
        )
      )

      (if (local.get $match)
        (then
          ;; Found separator - add part to result
          (local.set $part_len (i32.sub (local.get $i) (local.get $start)))
          (local.set $part_off (global.get $string_heap))
          (global.set $string_heap (i32.add (global.get $string_heap) (local.get $part_len)))
          (if (i32.gt_s (local.get $part_len) (i32.const 0))
            (then
              (memory.copy (local.get $part_off) (i32.add (local.get $s_off) (local.get $start)) (local.get $part_len))
            )
          )
          (local.set $result
            (struct.new $PAIR
              (struct.new $STRING (local.get $part_off) (local.get $part_len))
              (local.get $result)))
          (local.set $i (i32.add (local.get $i) (local.get $sep_len)))
          (local.set $start (local.get $i))
          (local.set $splits (i32.add (local.get $splits) (i32.const 1)))
        )
        (else
          (local.set $i (i32.add (local.get $i) (i32.const 1)))
        )
      )
      (br $search)
    )
  )

  ;; Reverse the result list (we built it backwards)
  (call $list_reverse (local.get $result))
)


;; String method: join(iterable) - join strings with separator
(func $string_join (param $sep (ref null eq)) (param $lst (ref null eq)) (result (ref null eq))
  (local $sep_off i32)
  (local $sep_len i32)
  (local $current (ref null eq))
  (local $elem (ref null eq))
  (local $dst_off i32)
  (local $dst_len i32)
  (local $first i32)
  (local $i i32)
  (local $len i32)
  (local $data (ref null $ARRAY_ANY))

  (if (ref.is_null (local.get $sep))
    (then (return (struct.new $STRING (i32.const 0) (i32.const 0))))
  )
  (local.set $sep_off (struct.get $STRING 0 (ref.cast (ref $STRING) (local.get $sep))))
  (local.set $sep_len (struct.get $STRING 1 (ref.cast (ref $STRING) (local.get $sep))))

  ;; Empty list -> empty string
  (if (ref.is_null (local.get $lst))
    (then (return (struct.new $STRING (i32.const 0) (i32.const 0))))
  )

  (local.set $dst_off (global.get $string_heap))
  (local.set $dst_len (i32.const 0))
  (local.set $first (i32.const 1))

  ;; Handle $LIST (array-backed)
  (if (ref.test (ref $LIST) (local.get $lst))
    (then
      (local.set $data (struct.get $LIST 0 (ref.cast (ref $LIST) (local.get $lst))))
      (local.set $len (struct.get $LIST 1 (ref.cast (ref $LIST) (local.get $lst))))
      (local.set $i (i32.const 0))
      (block $done_arr
        (loop $loop_arr
          (br_if $done_arr (i32.ge_s (local.get $i) (local.get $len)))
          ;; Add separator (except before first element)
          (if (i32.eqz (local.get $first))
            (then
              (memory.copy (i32.add (local.get $dst_off) (local.get $dst_len))
                           (local.get $sep_off) (local.get $sep_len))
              (local.set $dst_len (i32.add (local.get $dst_len) (local.get $sep_len)))
            )
          )
          (local.set $first (i32.const 0))
          ;; Add element
          (local.set $elem (array.get $ARRAY_ANY (ref.cast (ref $ARRAY_ANY) (local.get $data)) (local.get $i)))
          (if (ref.test (ref $STRING) (local.get $elem))
            (then
              (memory.copy (i32.add (local.get $dst_off) (local.get $dst_len))
                           (struct.get $STRING 0 (ref.cast (ref $STRING) (local.get $elem)))
                           (struct.get $STRING 1 (ref.cast (ref $STRING) (local.get $elem))))
              (local.set $dst_len (i32.add (local.get $dst_len) (struct.get $STRING 1 (ref.cast (ref $STRING) (local.get $elem)))))
            )
          )
          (local.set $i (i32.add (local.get $i) (i32.const 1)))
          (br $loop_arr)
        )
      )
      (global.set $string_heap (i32.add (global.get $string_heap) (local.get $dst_len)))
      (return (struct.new $STRING (local.get $dst_off) (local.get $dst_len)))
    )
  )

  ;; PAIR chain path
  (local.set $current (local.get $lst))
  (block $done
    (loop $loop
      (br_if $done (ref.is_null (local.get $current)))
      (br_if $done (i32.eqz (ref.test (ref $PAIR) (local.get $current))))

      ;; Add separator (except before first element)
      (if (i32.eqz (local.get $first))
        (then
          (memory.copy (i32.add (local.get $dst_off) (local.get $dst_len))
                       (local.get $sep_off) (local.get $sep_len))
          (local.set $dst_len (i32.add (local.get $dst_len) (local.get $sep_len)))
        )
      )
      (local.set $first (i32.const 0))

      ;; Add element
      (local.set $elem (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $current))))
      (if (ref.test (ref $STRING) (local.get $elem))
        (then
          (memory.copy (i32.add (local.get $dst_off) (local.get $dst_len))
                       (struct.get $STRING 0 (ref.cast (ref $STRING) (local.get $elem)))
                       (struct.get $STRING 1 (ref.cast (ref $STRING) (local.get $elem))))
          (local.set $dst_len (i32.add (local.get $dst_len) (struct.get $STRING 1 (ref.cast (ref $STRING) (local.get $elem)))))
        )
      )

      (local.set $current (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current))))
      (br $loop)
    )
  )

  (global.set $string_heap (i32.add (global.get $string_heap) (local.get $dst_len)))
  (struct.new $STRING (local.get $dst_off) (local.get $dst_len))
)


;; String method: format() - basic positional formatting
;; Supports {} for sequential args and {N} for explicit positional args
;; Format string is on stack, followed by args list (PAIR chain)
;; Uses string concatenation to avoid heap conflicts with value_to_string
(func $string_format (param $fmt (ref null eq)) (param $args (ref null eq)) (result (ref null eq))
  (local $fmt_str (ref $STRING))
  (local $fmt_off i32)
  (local $fmt_len i32)
  (local $i i32)
  (local $c i32)
  (local $result (ref $STRING))
  (local $tmp_str (ref $STRING))
  (local $arg_idx i32)
  (local $placeholder_idx i32)
  (local $arg (ref null eq))
  (local $arg_str (ref $STRING))
  (local $segment_start i32)
  (local $segment_len i32)
  (local $segment_off i32)

  (if (ref.is_null (local.get $fmt))
    (then (return (struct.new $STRING (i32.const 0) (i32.const 0))))
  )
  (local.set $fmt_str (ref.cast (ref $STRING) (local.get $fmt)))
  (local.set $fmt_off (struct.get $STRING 0 (local.get $fmt_str)))
  (local.set $fmt_len (struct.get $STRING 1 (local.get $fmt_str)))

  ;; Start with empty result
  (local.set $result (struct.new $STRING (i32.const 0) (i32.const 0)))
  (local.set $arg_idx (i32.const 0))
  (local.set $i (i32.const 0))
  (local.set $segment_start (i32.const 0))

  (block $done
    (loop $loop
      (br_if $done (i32.ge_u (local.get $i) (local.get $fmt_len)))
      (local.set $c (i32.load8_u (i32.add (local.get $fmt_off) (local.get $i))))

      ;; Check for '{' placeholder
      (if (i32.eq (local.get $c) (i32.const 123))  ;; '{'
        (then
          ;; Append segment before placeholder
          (local.set $segment_len (i32.sub (local.get $i) (local.get $segment_start)))
          (if (i32.gt_s (local.get $segment_len) (i32.const 0))
            (then
              (local.set $segment_off (global.get $string_heap))
              (call $memcpy (local.get $segment_off)
                (i32.add (local.get $fmt_off) (local.get $segment_start))
                (local.get $segment_len))
              (global.set $string_heap (i32.add (global.get $string_heap) (local.get $segment_len)))
              (local.set $tmp_str (struct.new $STRING (local.get $segment_off) (local.get $segment_len)))
              (local.set $result (call $string_concat (local.get $result) (local.get $tmp_str)))
            )
          )

          ;; Look at next character
          (local.set $i (i32.add (local.get $i) (i32.const 1)))
          (if (i32.lt_u (local.get $i) (local.get $fmt_len))
            (then
              (local.set $c (i32.load8_u (i32.add (local.get $fmt_off) (local.get $i))))

              ;; Check for '}' - sequential placeholder
              (if (i32.eq (local.get $c) (i32.const 125))  ;; '}'
                (then
                  ;; Use next positional arg
                  (local.set $arg (call $list_get (local.get $args) (local.get $arg_idx)))
                  (local.set $arg_idx (i32.add (local.get $arg_idx) (i32.const 1)))
                  ;; Convert arg to string and append
                  (local.set $arg_str (call $value_to_string (local.get $arg)))
                  (local.set $result (call $string_concat (local.get $result) (local.get $arg_str)))
                  (local.set $i (i32.add (local.get $i) (i32.const 1)))
                  (local.set $segment_start (local.get $i))
                  (br $loop)
                )
              )

              ;; Check for digit - explicit positional placeholder like {0}
              (if (i32.and (i32.ge_u (local.get $c) (i32.const 48))
                           (i32.le_u (local.get $c) (i32.const 57)))  ;; '0'-'9'
                (then
                  (local.set $placeholder_idx (i32.sub (local.get $c) (i32.const 48)))
                  (local.set $i (i32.add (local.get $i) (i32.const 1)))
                  ;; Skip to closing '}'
                  (block $skip_done
                    (loop $skip_loop
                      (br_if $skip_done (i32.ge_u (local.get $i) (local.get $fmt_len)))
                      (local.set $c (i32.load8_u (i32.add (local.get $fmt_off) (local.get $i))))
                      (br_if $skip_done (i32.eq (local.get $c) (i32.const 125)))  ;; '}'
                      (local.set $i (i32.add (local.get $i) (i32.const 1)))
                      (br $skip_loop)
                    )
                  )
                  ;; Get arg at explicit index
                  (local.set $arg (call $list_get (local.get $args) (local.get $placeholder_idx)))
                  ;; Convert arg to string and append
                  (local.set $arg_str (call $value_to_string (local.get $arg)))
                  (local.set $result (call $string_concat (local.get $result) (local.get $arg_str)))
                  (local.set $i (i32.add (local.get $i) (i32.const 1)))
                  (local.set $segment_start (local.get $i))
                  (br $loop)
                )
              )

              ;; Check for ':' - format specifier like {:.2f}
              (if (i32.eq (local.get $c) (i32.const 58))  ;; ':'
                (then
                  (local.set $i (i32.add (local.get $i) (i32.const 1)))
                  ;; Check for '.' followed by digit and 'f'
                  (if (i32.and
                        (i32.lt_u (i32.add (local.get $i) (i32.const 2)) (local.get $fmt_len))
                        (i32.eq (i32.load8_u (i32.add (local.get $fmt_off) (local.get $i))) (i32.const 46)))  ;; '.'
                    (then
                      (local.set $i (i32.add (local.get $i) (i32.const 1)))
                      (local.set $c (i32.load8_u (i32.add (local.get $fmt_off) (local.get $i))))
                      ;; Check for digit
                      (if (i32.and (i32.ge_u (local.get $c) (i32.const 48))
                                   (i32.le_u (local.get $c) (i32.const 57)))  ;; '0'-'9'
                        (then
                          (local.set $placeholder_idx (i32.sub (local.get $c) (i32.const 48)))  ;; precision
                          (local.set $i (i32.add (local.get $i) (i32.const 1)))
                          ;; Check for 'f' format specifier
                          (if (i32.lt_u (local.get $i) (local.get $fmt_len))
                            (then
                              (local.set $c (i32.load8_u (i32.add (local.get $fmt_off) (local.get $i))))
                              (if (i32.eq (local.get $c) (i32.const 102))  ;; 'f'
                                (then
                                  (local.set $i (i32.add (local.get $i) (i32.const 1)))
                                  ;; Skip to closing '}'
                                  (block $skip_f_done
                                    (loop $skip_f
                                      (br_if $skip_f_done (i32.ge_u (local.get $i) (local.get $fmt_len)))
                                      (local.set $c (i32.load8_u (i32.add (local.get $fmt_off) (local.get $i))))
                                      (br_if $skip_f_done (i32.eq (local.get $c) (i32.const 125)))  ;; '}'
                                      (local.set $i (i32.add (local.get $i) (i32.const 1)))
                                      (br $skip_f)
                                    )
                                  )
                                  ;; Get next positional arg and format with precision
                                  (local.set $arg (call $list_get (local.get $args) (local.get $arg_idx)))
                                  (local.set $arg_idx (i32.add (local.get $arg_idx) (i32.const 1)))
                                  (local.set $arg_str (call $float_to_string_precision (local.get $arg) (local.get $placeholder_idx)))
                                  (local.set $result (call $string_concat (local.get $result) (local.get $arg_str)))
                                  (local.set $i (i32.add (local.get $i) (i32.const 1)))
                                  (local.set $segment_start (local.get $i))
                                  (br $loop)
                                )
                              )
                            )
                          )
                        )
                      )
                    )
                  )
                  ;; Unknown format spec - backtrack and include '{' in segment
                  (local.set $segment_start (i32.sub (local.get $i) (i32.const 2)))
                  (br $loop)
                )
              )

              ;; Unknown format - include the '{' in next segment
              (local.set $segment_start (i32.sub (local.get $i) (i32.const 1)))
              (br $loop)
            )
          )
          ;; Trailing '{' - include it in next segment
          (local.set $segment_start (i32.sub (local.get $i) (i32.const 1)))
          (br $loop)
        )
      )

      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $loop)
    )
  )

  ;; Append final segment
  (local.set $segment_len (i32.sub (local.get $fmt_len) (local.get $segment_start)))
  (if (i32.gt_s (local.get $segment_len) (i32.const 0))
    (then
      (local.set $segment_off (global.get $string_heap))
      (call $memcpy (local.get $segment_off)
        (i32.add (local.get $fmt_off) (local.get $segment_start))
        (local.get $segment_len))
      (global.set $string_heap (i32.add (global.get $string_heap) (local.get $segment_len)))
      (local.set $tmp_str (struct.new $STRING (local.get $segment_off) (local.get $segment_len)))
      (local.set $result (call $string_concat (local.get $result) (local.get $tmp_str)))
    )
  )

  (local.get $result)
)


;; Helper: string_equals - compare two strings
(func $string_equals (param $a (ref $STRING)) (param $b (ref $STRING)) (result i32)
  (local $a_off i32)
  (local $a_len i32)
  (local $b_off i32)
  (local $b_len i32)
  (local $i i32)

  (local.set $a_off (struct.get $STRING 0 (local.get $a)))
  (local.set $a_len (struct.get $STRING 1 (local.get $a)))
  (local.set $b_off (struct.get $STRING 0 (local.get $b)))
  (local.set $b_len (struct.get $STRING 1 (local.get $b)))

  ;; Different lengths -> not equal
  (if (i32.ne (local.get $a_len) (local.get $b_len))
    (then (return (i32.const 0)))
  )

  ;; Compare bytes
  (local.set $i (i32.const 0))
  (block $not_equal
    (loop $loop
      (br_if $not_equal (i32.ge_u (local.get $i) (local.get $a_len)))
      (if (i32.ne
            (i32.load8_u (i32.add (local.get $a_off) (local.get $i)))
            (i32.load8_u (i32.add (local.get $b_off) (local.get $i))))
        (then (return (i32.const 0)))
      )
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $loop)
    )
  )
  (i32.const 1)
)


;; string_to_chars: convert a STRING to a PAIR chain of single-character strings
;; Used for iteration: for c in "abc" -> iterates over ["a", "b", "c"]
(func $string_to_chars (param $str (ref $STRING)) (result (ref null eq))
  (local $offset i32)
  (local $len i32)
  (local $i i32)
  (local $result (ref null eq))
  (local $char_off i32)
  (local $char_str (ref $STRING))

  (local.set $offset (struct.get $STRING 0 (local.get $str)))
  (local.set $len (struct.get $STRING 1 (local.get $str)))

  ;; Empty string -> return null (empty list)
  (if (i32.eqz (local.get $len))
    (then (return (ref.null eq)))
  )

  ;; Build PAIR chain in reverse (start from end of string)
  (local.set $result (ref.null eq))
  (local.set $i (i32.sub (local.get $len) (i32.const 1)))

  (block $done
    (loop $loop
      (br_if $done (i32.lt_s (local.get $i) (i32.const 0)))

      ;; Allocate space for single character in string heap
      (local.set $char_off (global.get $string_heap))
      (i32.store8 (local.get $char_off)
        (i32.load8_u (i32.add (local.get $offset) (local.get $i))))
      (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 1)))

      ;; Create single-char STRING
      (local.set $char_str (struct.new $STRING (local.get $char_off) (i32.const 1)))

      ;; Prepend to result list
      (local.set $result (struct.new $PAIR (local.get $char_str) (local.get $result)))

      (local.set $i (i32.sub (local.get $i) (i32.const 1)))
      (br $loop)
    )
  )

  (local.get $result)
)


;; string_to_chars_reversed: convert STRING to PAIR chain of chars in reverse order
;; Used for reversed("hello") -> ['o', 'l', 'l', 'e', 'h']
(func $string_to_chars_reversed (param $str (ref $STRING)) (result (ref null eq))
  (local $offset i32)
  (local $len i32)
  (local $i i32)
  (local $result (ref null eq))
  (local $char_off i32)
  (local $char_str (ref $STRING))

  (local.set $offset (struct.get $STRING 0 (local.get $str)))
  (local.set $len (struct.get $STRING 1 (local.get $str)))

  ;; Empty string -> return null (empty list)
  (if (i32.eqz (local.get $len))
    (then (return (ref.null eq)))
  )

  ;; Build PAIR chain in forward order (start from beginning, prepend)
  ;; This gives us reversed result
  (local.set $result (ref.null eq))
  (local.set $i (i32.const 0))

  (block $done
    (loop $loop
      (br_if $done (i32.ge_s (local.get $i) (local.get $len)))

      ;; Allocate space for single character in string heap
      (local.set $char_off (global.get $string_heap))
      (i32.store8 (local.get $char_off)
        (i32.load8_u (i32.add (local.get $offset) (local.get $i))))
      (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 1)))

      ;; Create single-char STRING
      (local.set $char_str (struct.new $STRING (local.get $char_off) (i32.const 1)))

      ;; Prepend to result list (gives reversed order)
      (local.set $result (struct.new $PAIR (local.get $char_str) (local.get $result)))

      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $loop)
    )
  )

  (local.get $result)
)

"""
