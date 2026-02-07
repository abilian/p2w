"""WAT helper functions: Core utilities (truthiness, type checks, memory)."""

from __future__ import annotations

CORE_CODE = """

;; is_false: returns 1 if value is falsy (False, None, 0)
(func $is_false (param $v (ref null eq)) (result i32)
  ;; null is falsy
  (if (ref.is_null (local.get $v))
    (then (return (i32.const 1)))
  )
  ;; BOOL with value 0 is falsy
  (if (ref.test (ref $BOOL) (local.get $v))
    (then
      (return (i32.eqz (struct.get $BOOL 0 (ref.cast (ref $BOOL) (local.get $v)))))
    )
  )
  ;; i31 with value 0 is falsy
  (if (ref.test (ref i31) (local.get $v))
    (then
      (return (i32.eqz (i31.get_s (ref.cast (ref i31) (local.get $v)))))
    )
  )
  ;; INT64 with value 0 is falsy
  (if (ref.test (ref $INT64) (local.get $v))
    (then
      (return (i64.eqz (struct.get $INT64 0 (ref.cast (ref $INT64) (local.get $v)))))
    )
  )
  ;; Empty string is falsy
  (if (ref.test (ref $STRING) (local.get $v))
    (then
      (return (i32.eqz (struct.get $STRING 1 (ref.cast (ref $STRING) (local.get $v)))))
    )
  )
  ;; $DICT (hash table based): empty dict is falsy, non-empty is truthy
  (if (ref.test (ref $DICT) (local.get $v))
    (then
      ;; Check if hash table count is 0
      (return (i32.eqz (struct.get $HASHTABLE $count
        (struct.get $DICT $table (ref.cast (ref $DICT) (local.get $v))))))
    )
  )
  ;; $LIST (array-backed): empty list is falsy
  (if (ref.test (ref $LIST) (local.get $v))
    (then
      (return (i32.eqz (struct.get $LIST $len (ref.cast (ref $LIST) (local.get $v)))))
    )
  )
  ;; PAIR chain: non-empty PAIR is truthy
  (if (ref.test (ref $PAIR) (local.get $v))
    (then (return (i32.const 0)))  ;; Non-empty PAIR is truthy
  )
  ;; $ELLIPSIS is truthy (check before EMPTY_LIST as they were both empty structs)
  (if (ref.test (ref $ELLIPSIS) (local.get $v))
    (then (return (i32.const 0)))
  )
  ;; $EMPTY_LIST is falsy
  (if (ref.test (ref $EMPTY_LIST) (local.get $v))
    (then (return (i32.const 1)))
  )
  ;; everything else is truthy
  (i32.const 0)
)


;; ============================================================================
;; INT64 Helper Functions (for integers exceeding i31 range)
;; i31 range: -1073741824 to 1073741823 (approximately ±1 billion)
;; ============================================================================

;; to_i64: convert any integer (i31, INT64, or BOOL) to i64
(func $to_i64 (param $v (ref null eq)) (result i64)
  (if (result i64) (ref.test (ref i31) (local.get $v))
    (then (i64.extend_i32_s (i31.get_s (ref.cast (ref i31) (local.get $v)))))
    (else
      (if (result i64) (ref.test (ref $INT64) (local.get $v))
        (then (struct.get $INT64 0 (ref.cast (ref $INT64) (local.get $v))))
        (else
          (if (result i64) (ref.test (ref $BOOL) (local.get $v))
            (then (i64.extend_i32_u (struct.get $BOOL 0 (ref.cast (ref $BOOL) (local.get $v)))))
            (else (i64.const 0))  ;; fallback for non-integer
          )
        )
      )
    )
  )
)


;; fits_i31: check if i64 value fits in i31 range (-2^30 to 2^30-1)
(func $fits_i31 (param $val i64) (result i32)
  (i32.and
    (i64.ge_s (local.get $val) (i64.const -1073741824))
    (i64.le_s (local.get $val) (i64.const 1073741823))
  )
)


;; pack_int: return i31 if value fits, otherwise INT64
(func $pack_int (param $val i64) (result (ref null eq))
  (if (result (ref null eq)) (call $fits_i31 (local.get $val))
    (then (ref.i31 (i32.wrap_i64 (local.get $val))))
    (else (struct.new $INT64 (local.get $val)))
  )
)


;; is_integer: check if value is an integer (i31, INT64, or BOOL)
(func $is_integer (param $v (ref null eq)) (result i32)
  (i32.or
    (i32.or
      (ref.test (ref i31) (local.get $v))
      (ref.test (ref $INT64) (local.get $v))
    )
    (ref.test (ref $BOOL) (local.get $v))
  )
)


;; is_dict: check if value is a dict ($DICT wrapper or legacy PAIR chain of PAIRs)
(func $is_dict (param $container (ref null eq)) (result i32)
  (local $first (ref null eq))
  (if (ref.is_null (local.get $container))
    (then (return (i32.const 0)))
  )
  ;; Check for $DICT wrapper (new format)
  (if (ref.test (ref $DICT) (local.get $container))
    (then (return (i32.const 1)))
  )
  ;; Legacy check: PAIR chain where first element is also a PAIR (key-value)
  (if (ref.test (ref $PAIR) (local.get $container))
    (then
      (local.set $first (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $container))))
      (return (ref.test (ref $PAIR) (local.get $first)))
    )
  )
  (i32.const 0)
)


;; to_f64: convert any numeric value to f64
(func $to_f64 (param $v (ref null eq)) (result f64)
  (if (result f64) (ref.test (ref i31) (local.get $v))
    (then (f64.convert_i32_s (i31.get_s (ref.cast (ref i31) (local.get $v)))))
    (else
      (if (result f64) (ref.test (ref $INT64) (local.get $v))
        (then (f64.convert_i64_s (struct.get $INT64 0 (ref.cast (ref $INT64) (local.get $v)))))
        (else
          (if (result f64) (ref.test (ref $FLOAT) (local.get $v))
            (then (struct.get $FLOAT 0 (ref.cast (ref $FLOAT) (local.get $v))))
            (else (f64.const 0))
          )
        )
      )
    )
  )
)


;; memcpy: copy bytes from src to dst
(func $memcpy (param $dst i32) (param $src i32) (param $len i32)
  (local $i i32)
  (local.set $i (i32.const 0))
  (block $done
    (loop $loop
      (br_if $done (i32.ge_u (local.get $i) (local.get $len)))
      (i32.store8 (i32.add (local.get $dst) (local.get $i))
        (i32.load8_u (i32.add (local.get $src) (local.get $i))))
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $loop)
    )
  )
)


;; ensure_memory: ensure there is at least $needed bytes available from $string_heap
;; Grows memory if necessary. Each WASM page is 65536 bytes.
(func $ensure_memory (param $needed i32)
  (local $current_end i32)
  (local $mem_size i32)
  (local $pages_needed i32)
  (local $grow_result i32)
  ;; Calculate where the allocation would end
  (local.set $current_end (i32.add (global.get $string_heap) (local.get $needed)))
  ;; Get current memory size in bytes (memory.size returns pages)
  (local.set $mem_size (i32.mul (memory.size) (i32.const 65536)))
  ;; If we have enough space, return
  (if (i32.le_u (local.get $current_end) (local.get $mem_size))
    (then (return))
  )
  ;; Calculate pages needed: ceil((current_end - mem_size) / 65536) + 1 for safety
  (local.set $pages_needed
    (i32.add
      (i32.div_u
        (i32.add
          (i32.sub (local.get $current_end) (local.get $mem_size))
          (i32.const 65535))  ;; round up
        (i32.const 65536))
      (i32.const 1)))  ;; add 1 page buffer
  ;; Grow memory
  (local.set $grow_result (memory.grow (local.get $pages_needed)))
  ;; Note: grow_result is -1 on failure, but we don't handle that for now
)

"""
