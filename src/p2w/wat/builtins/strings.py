"""WAT builtin functions: String/character functions (chr, ord, hex, etc.)."""

from __future__ import annotations

CHR_CODE = """
(func $chr (param $args (ref null eq)) (param $env (ref null $ENV)) (result (ref null eq))
  (local $code i32)
  (local $offset i32)
  (local $len i32)
  (if (ref.is_null (local.get $args))
    (then (return (struct.new $STRING (i32.const 0) (i32.const 0))))
  )
  (local.set $code (i31.get_s (ref.cast (ref i31)
    (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))))
  (local.set $offset (global.get $string_heap))

  ;; UTF-8 encoding
  (if (i32.lt_u (local.get $code) (i32.const 0x80))
    (then
      ;; 1-byte: 0xxxxxxx (ASCII)
      (i32.store8 (local.get $offset) (local.get $code))
      (local.set $len (i32.const 1))
    )
    (else
      (if (i32.lt_u (local.get $code) (i32.const 0x800))
        (then
          ;; 2-byte: 110xxxxx 10xxxxxx
          (i32.store8 (local.get $offset)
            (i32.or (i32.const 0xC0) (i32.shr_u (local.get $code) (i32.const 6))))
          (i32.store8 (i32.add (local.get $offset) (i32.const 1))
            (i32.or (i32.const 0x80) (i32.and (local.get $code) (i32.const 0x3F))))
          (local.set $len (i32.const 2))
        )
        (else
          (if (i32.lt_u (local.get $code) (i32.const 0x10000))
            (then
              ;; 3-byte: 1110xxxx 10xxxxxx 10xxxxxx
              (i32.store8 (local.get $offset)
                (i32.or (i32.const 0xE0) (i32.shr_u (local.get $code) (i32.const 12))))
              (i32.store8 (i32.add (local.get $offset) (i32.const 1))
                (i32.or (i32.const 0x80) (i32.and (i32.shr_u (local.get $code) (i32.const 6)) (i32.const 0x3F))))
              (i32.store8 (i32.add (local.get $offset) (i32.const 2))
                (i32.or (i32.const 0x80) (i32.and (local.get $code) (i32.const 0x3F))))
              (local.set $len (i32.const 3))
            )
            (else
              ;; 4-byte: 11110xxx 10xxxxxx 10xxxxxx 10xxxxxx
              (i32.store8 (local.get $offset)
                (i32.or (i32.const 0xF0) (i32.shr_u (local.get $code) (i32.const 18))))
              (i32.store8 (i32.add (local.get $offset) (i32.const 1))
                (i32.or (i32.const 0x80) (i32.and (i32.shr_u (local.get $code) (i32.const 12)) (i32.const 0x3F))))
              (i32.store8 (i32.add (local.get $offset) (i32.const 2))
                (i32.or (i32.const 0x80) (i32.and (i32.shr_u (local.get $code) (i32.const 6)) (i32.const 0x3F))))
              (i32.store8 (i32.add (local.get $offset) (i32.const 3))
                (i32.or (i32.const 0x80) (i32.and (local.get $code) (i32.const 0x3F))))
              (local.set $len (i32.const 4))
            )
          )
        )
      )
    )
  )
  (global.set $string_heap (i32.add (global.get $string_heap) (local.get $len)))
  (struct.new $STRING (local.get $offset) (local.get $len))
)
"""

ORD_CODE = """
(func $ord (param $args (ref null eq)) (param $env (ref null $ENV)) (result (ref null eq))
  (local $s (ref null $STRING))
  (if (ref.is_null (local.get $args))
    (then (return (ref.i31 (i32.const 0))))
  )
  (local.set $s (ref.cast (ref $STRING)
    (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args)))))
  ;; Return first character code
  (ref.i31 (i32.load8_u (struct.get $STRING 0 (local.get $s))))
)
"""

REPR_CODE = """
(func $repr (param $args (ref null eq)) (param $env (ref null $ENV)) (result (ref null eq))
  (local $val (ref null eq))
  (local $method_result (ref null eq))
  (local $method_name (ref $STRING))
  (local $offset i32)
  (if (ref.is_null (local.get $args))
    (then (return (struct.new $STRING (i32.const 0) (i32.const 0))))
  )
  (local.set $val (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))

  ;; Check for OBJECT with __repr__ special method
  (if (ref.test (ref $OBJECT) (local.get $val))
    (then
      ;; Create string "__repr__" (8 chars: 95,95,114,101,112,114,95,95)
      (local.set $offset (global.get $string_heap))
      (i32.store8 (local.get $offset) (i32.const 95))  ;; _
      (i32.store8 (i32.add (local.get $offset) (i32.const 1)) (i32.const 95))  ;; _
      (i32.store8 (i32.add (local.get $offset) (i32.const 2)) (i32.const 114))  ;; r
      (i32.store8 (i32.add (local.get $offset) (i32.const 3)) (i32.const 101))  ;; e
      (i32.store8 (i32.add (local.get $offset) (i32.const 4)) (i32.const 112))  ;; p
      (i32.store8 (i32.add (local.get $offset) (i32.const 5)) (i32.const 114))  ;; r
      (i32.store8 (i32.add (local.get $offset) (i32.const 6)) (i32.const 95))  ;; _
      (i32.store8 (i32.add (local.get $offset) (i32.const 7)) (i32.const 95))  ;; _
      (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 8)))
      (local.set $method_name (struct.new $STRING (local.get $offset) (i32.const 8)))

      ;; Call __repr__(self) - args = (PAIR self null)
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

  ;; For strings, add quotes
  (if (ref.test (ref $STRING) (local.get $val))
    (then
      (return (call $string_add_quotes (ref.cast (ref $STRING) (local.get $val))))
    )
  )
  ;; For other types, return str representation
  (call $str (local.get $args) (local.get $env))
)
"""

HEX_CODE = """
;; hex(x) - convert integer to hex string
(func $hex (param $args (ref null eq)) (param $env (ref null $ENV)) (result (ref null eq))
  (local $val (ref null eq))
  (local $n i32)
  (local $neg i32)
  (local $digit i32)
  (local $dst i32)
  (local $start i32)
  (local $len i32)
  (local $temp i32)
  ;; Get argument
  (if (ref.is_null (local.get $args))
    (then (return (struct.new $STRING (global.get $string_heap) (i32.const 0))))
  )
  (local.set $val (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))
  (local.set $n (i31.get_s (ref.cast (ref i31) (local.get $val))))
  ;; Handle zero
  (if (i32.eqz (local.get $n))
    (then
      (local.set $dst (global.get $string_heap))
      (i32.store8 (local.get $dst) (i32.const 48))  ;; '0'
      (i32.store8 (i32.add (local.get $dst) (i32.const 1)) (i32.const 120))  ;; 'x'
      (i32.store8 (i32.add (local.get $dst) (i32.const 2)) (i32.const 48))  ;; '0'
      (global.set $string_heap (i32.add (local.get $dst) (i32.const 3)))
      (return (struct.new $STRING (local.get $dst) (i32.const 3)))
    )
  )
  ;; Handle negative
  (local.set $neg (i32.lt_s (local.get $n) (i32.const 0)))
  (if (local.get $neg)
    (then (local.set $n (i32.sub (i32.const 0) (local.get $n))))
  )
  ;; Write hex digits in reverse, starting from a temp position
  (local.set $dst (i32.add (global.get $string_heap) (i32.const 20)))
  (local.set $len (i32.const 0))
  (block $done
    (loop $loop
      (br_if $done (i32.eqz (local.get $n)))
      (local.set $digit (i32.and (local.get $n) (i32.const 15)))
      (local.set $dst (i32.sub (local.get $dst) (i32.const 1)))
      (if (i32.lt_u (local.get $digit) (i32.const 10))
        (then (i32.store8 (local.get $dst) (i32.add (local.get $digit) (i32.const 48))))
        (else (i32.store8 (local.get $dst) (i32.add (i32.sub (local.get $digit) (i32.const 10)) (i32.const 97))))
      )
      (local.set $n (i32.shr_u (local.get $n) (i32.const 4)))
      (local.set $len (i32.add (local.get $len) (i32.const 1)))
      (br $loop)
    )
  )
  ;; Add 0x prefix
  (local.set $dst (i32.sub (local.get $dst) (i32.const 1)))
  (i32.store8 (local.get $dst) (i32.const 120))  ;; 'x'
  (local.set $dst (i32.sub (local.get $dst) (i32.const 1)))
  (i32.store8 (local.get $dst) (i32.const 48))  ;; '0'
  (local.set $len (i32.add (local.get $len) (i32.const 2)))
  ;; Add minus sign if negative
  (if (local.get $neg)
    (then
      (local.set $dst (i32.sub (local.get $dst) (i32.const 1)))
      (i32.store8 (local.get $dst) (i32.const 45))  ;; '-'
      (local.set $len (i32.add (local.get $len) (i32.const 1)))
    )
  )
  ;; Copy to final position
  (local.set $start (global.get $string_heap))
  (memory.copy (local.get $start) (local.get $dst) (local.get $len))
  (global.set $string_heap (i32.add (local.get $start) (local.get $len)))
  (struct.new $STRING (local.get $start) (local.get $len))
)
"""

BIN_CODE = """
;; bin(x) - convert integer to binary string
(func $bin (param $args (ref null eq)) (param $env (ref null $ENV)) (result (ref null eq))
  (local $val (ref null eq))
  (local $n i32)
  (local $neg i32)
  (local $digit i32)
  (local $dst i32)
  (local $start i32)
  (local $len i32)
  ;; Get argument
  (if (ref.is_null (local.get $args))
    (then (return (struct.new $STRING (global.get $string_heap) (i32.const 0))))
  )
  (local.set $val (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))
  (local.set $n (i31.get_s (ref.cast (ref i31) (local.get $val))))
  ;; Handle zero
  (if (i32.eqz (local.get $n))
    (then
      (local.set $dst (global.get $string_heap))
      (i32.store8 (local.get $dst) (i32.const 48))  ;; '0'
      (i32.store8 (i32.add (local.get $dst) (i32.const 1)) (i32.const 98))  ;; 'b'
      (i32.store8 (i32.add (local.get $dst) (i32.const 2)) (i32.const 48))  ;; '0'
      (global.set $string_heap (i32.add (local.get $dst) (i32.const 3)))
      (return (struct.new $STRING (local.get $dst) (i32.const 3)))
    )
  )
  ;; Handle negative
  (local.set $neg (i32.lt_s (local.get $n) (i32.const 0)))
  (if (local.get $neg)
    (then (local.set $n (i32.sub (i32.const 0) (local.get $n))))
  )
  ;; Write binary digits in reverse
  (local.set $dst (i32.add (global.get $string_heap) (i32.const 40)))
  (local.set $len (i32.const 0))
  (block $done
    (loop $loop
      (br_if $done (i32.eqz (local.get $n)))
      (local.set $digit (i32.and (local.get $n) (i32.const 1)))
      (local.set $dst (i32.sub (local.get $dst) (i32.const 1)))
      (i32.store8 (local.get $dst) (i32.add (local.get $digit) (i32.const 48)))
      (local.set $n (i32.shr_u (local.get $n) (i32.const 1)))
      (local.set $len (i32.add (local.get $len) (i32.const 1)))
      (br $loop)
    )
  )
  ;; Add 0b prefix
  (local.set $dst (i32.sub (local.get $dst) (i32.const 1)))
  (i32.store8 (local.get $dst) (i32.const 98))  ;; 'b'
  (local.set $dst (i32.sub (local.get $dst) (i32.const 1)))
  (i32.store8 (local.get $dst) (i32.const 48))  ;; '0'
  (local.set $len (i32.add (local.get $len) (i32.const 2)))
  ;; Add minus sign if negative
  (if (local.get $neg)
    (then
      (local.set $dst (i32.sub (local.get $dst) (i32.const 1)))
      (i32.store8 (local.get $dst) (i32.const 45))  ;; '-'
      (local.set $len (i32.add (local.get $len) (i32.const 1)))
    )
  )
  ;; Copy to final position
  (local.set $start (global.get $string_heap))
  (memory.copy (local.get $start) (local.get $dst) (local.get $len))
  (global.set $string_heap (i32.add (local.get $start) (local.get $len)))
  (struct.new $STRING (local.get $start) (local.get $len))
)
"""

OCT_CODE = """
;; oct(x) - convert integer to octal string
(func $oct (param $args (ref null eq)) (param $env (ref null $ENV)) (result (ref null eq))
  (local $val (ref null eq))
  (local $n i32)
  (local $neg i32)
  (local $digit i32)
  (local $dst i32)
  (local $start i32)
  (local $len i32)
  ;; Get argument
  (if (ref.is_null (local.get $args))
    (then (return (struct.new $STRING (global.get $string_heap) (i32.const 0))))
  )
  (local.set $val (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))
  (local.set $n (i31.get_s (ref.cast (ref i31) (local.get $val))))
  ;; Handle zero
  (if (i32.eqz (local.get $n))
    (then
      (local.set $dst (global.get $string_heap))
      (i32.store8 (local.get $dst) (i32.const 48))  ;; '0'
      (i32.store8 (i32.add (local.get $dst) (i32.const 1)) (i32.const 111))  ;; 'o'
      (i32.store8 (i32.add (local.get $dst) (i32.const 2)) (i32.const 48))  ;; '0'
      (global.set $string_heap (i32.add (local.get $dst) (i32.const 3)))
      (return (struct.new $STRING (local.get $dst) (i32.const 3)))
    )
  )
  ;; Handle negative
  (local.set $neg (i32.lt_s (local.get $n) (i32.const 0)))
  (if (local.get $neg)
    (then (local.set $n (i32.sub (i32.const 0) (local.get $n))))
  )
  ;; Write octal digits in reverse
  (local.set $dst (i32.add (global.get $string_heap) (i32.const 20)))
  (local.set $len (i32.const 0))
  (block $done
    (loop $loop
      (br_if $done (i32.eqz (local.get $n)))
      (local.set $digit (i32.and (local.get $n) (i32.const 7)))
      (local.set $dst (i32.sub (local.get $dst) (i32.const 1)))
      (i32.store8 (local.get $dst) (i32.add (local.get $digit) (i32.const 48)))
      (local.set $n (i32.shr_u (local.get $n) (i32.const 3)))
      (local.set $len (i32.add (local.get $len) (i32.const 1)))
      (br $loop)
    )
  )
  ;; Add 0o prefix
  (local.set $dst (i32.sub (local.get $dst) (i32.const 1)))
  (i32.store8 (local.get $dst) (i32.const 111))  ;; 'o'
  (local.set $dst (i32.sub (local.get $dst) (i32.const 1)))
  (i32.store8 (local.get $dst) (i32.const 48))  ;; '0'
  (local.set $len (i32.add (local.get $len) (i32.const 2)))
  ;; Add minus sign if negative
  (if (local.get $neg)
    (then
      (local.set $dst (i32.sub (local.get $dst) (i32.const 1)))
      (i32.store8 (local.get $dst) (i32.const 45))  ;; '-'
      (local.set $len (i32.add (local.get $len) (i32.const 1)))
    )
  )
  ;; Copy to final position
  (local.set $start (global.get $string_heap))
  (memory.copy (local.get $start) (local.get $dst) (local.get $len))
  (global.set $string_heap (i32.add (local.get $start) (local.get $len)))
  (struct.new $STRING (local.get $start) (local.get $len))
)
"""

ASCII_CODE = """
;; ascii(obj) - like repr but escapes non-ASCII (for now, same as repr)
(func $ascii (param $args (ref null eq)) (param $env (ref null $ENV)) (result (ref null eq))
  ;; Delegate to repr for now
  (call $repr (local.get $args) (local.get $env))
)
"""

# Combined code for this module
STRINGS_CODE = (
    CHR_CODE + ORD_CODE + REPR_CODE + HEX_CODE + BIN_CODE + OCT_CODE + ASCII_CODE
)
