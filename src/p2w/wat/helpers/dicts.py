"""WAT helper functions: Dictionary and hash table operations."""

from __future__ import annotations

DICTS_CODE = """

;; =============================================================================
;; Hash Functions for Dict/Set O(1) Operations
;; =============================================================================

;; FNV-1a hash for strings
;; Uses FNV-1a algorithm with 32-bit parameters
;; FNV offset basis: 2166136261
;; FNV prime: 16777619
(func $hash_string (param $s (ref $STRING)) (result i32)
  (local $offset i32)
  (local $len i32)
  (local $hash i32)
  (local $i i32)

  (local.set $offset (struct.get $STRING 0 (local.get $s)))
  (local.set $len (struct.get $STRING 1 (local.get $s)))
  (local.set $hash (i32.const 2166136261))  ;; FNV offset basis

  (block $done
    (loop $loop
      (br_if $done (i32.ge_u (local.get $i) (local.get $len)))

      ;; hash ^= byte
      (local.set $hash (i32.xor (local.get $hash)
        (i32.load8_u (i32.add (local.get $offset) (local.get $i)))))

      ;; hash *= FNV prime
      (local.set $hash (i32.mul (local.get $hash) (i32.const 16777619)))

      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $loop)
    )
  )
  (local.get $hash)
)


;; Hash any value
;; Returns an i32 hash code for use in hash tables
(func $hash_value (param $v (ref null eq)) (result i32)
  (local $i64_val i64)

  ;; null -> 0
  (if (ref.is_null (local.get $v))
    (then (return (i32.const 0)))
  )

  ;; i31 -> use the value directly (good distribution for small ints)
  (if (ref.test (ref i31) (local.get $v))
    (then (return (i31.get_s (ref.cast (ref i31) (local.get $v)))))
  )

  ;; STRING -> FNV-1a hash
  (if (ref.test (ref $STRING) (local.get $v))
    (then (return (call $hash_string (ref.cast (ref $STRING) (local.get $v)))))
  )

  ;; BOOL -> 0 or 1
  (if (ref.test (ref $BOOL) (local.get $v))
    (then (return (struct.get $BOOL 0 (ref.cast (ref $BOOL) (local.get $v)))))
  )

  ;; INT64 -> XOR lower and upper 32 bits
  (if (ref.test (ref $INT64) (local.get $v))
    (then
      (local.set $i64_val (struct.get $INT64 0 (ref.cast (ref $INT64) (local.get $v))))
      (return (i32.xor
        (i32.wrap_i64 (local.get $i64_val))
        (i32.wrap_i64 (i64.shr_u (local.get $i64_val) (i64.const 32)))
      ))
    )
  )

  ;; FLOAT -> XOR lower and upper 32 bits of bit representation
  (if (ref.test (ref $FLOAT) (local.get $v))
    (then
      (local.set $i64_val (i64.reinterpret_f64
        (struct.get $FLOAT 0 (ref.cast (ref $FLOAT) (local.get $v)))))
      (return (i32.xor
        (i32.wrap_i64 (local.get $i64_val))
        (i32.wrap_i64 (i64.shr_u (local.get $i64_val) (i64.const 32)))
      ))
    )
  )

  ;; Default: identity hash (not ideal, but safe)
  (i32.const 0)
)


;; =============================================================================
;; Hash Table Operations
;; =============================================================================

;; Create hash table with given number of buckets
(func $hashtable_new (param $size i32) (result (ref $HASHTABLE))
  (struct.new $HASHTABLE
    (array.new $BUCKET_ARRAY (ref.null $ENTRY) (local.get $size))
    (local.get $size)
    (i32.const 0)  ;; count = 0
  )
)


;; Get value by key (returns null if not found)
(func $hashtable_get (param $table (ref $HASHTABLE)) (param $key (ref null eq)) (result (ref null eq))
  (local $hash i32)
  (local $bucket_idx i32)
  (local $entry (ref null $ENTRY))

  (local.set $hash (call $hash_value (local.get $key)))
  (local.set $bucket_idx (i32.rem_u
    (i32.and (local.get $hash) (i32.const 0x7FFFFFFF))  ;; ensure positive
    (struct.get $HASHTABLE $size (local.get $table))
  ))

  (local.set $entry (array.get $BUCKET_ARRAY
    (struct.get $HASHTABLE $buckets (local.get $table))
    (local.get $bucket_idx)
  ))

  ;; Search chain
  (block $done
    (loop $loop
      (br_if $done (ref.is_null (local.get $entry)))

      ;; Check hash first (fast rejection)
      (if (i32.eq (struct.get $ENTRY $hash (ref.cast (ref $ENTRY) (local.get $entry)))
                  (local.get $hash))
        (then
          ;; Check key equality
          (if (call $values_equal
                (struct.get $ENTRY $key (ref.cast (ref $ENTRY) (local.get $entry)))
                (local.get $key))
            (then
              (return (struct.get $ENTRY $value (ref.cast (ref $ENTRY) (local.get $entry))))
            )
          )
        )
      )

      (local.set $entry (struct.get $ENTRY $next (ref.cast (ref $ENTRY) (local.get $entry))))
      (br $loop)
    )
  )

  (ref.null eq)
)


;; Check if key exists in hash table
(func $hashtable_contains (param $table (ref $HASHTABLE)) (param $key (ref null eq)) (result i32)
  (local $hash i32)
  (local $bucket_idx i32)
  (local $entry (ref null $ENTRY))

  (local.set $hash (call $hash_value (local.get $key)))
  (local.set $bucket_idx (i32.rem_u
    (i32.and (local.get $hash) (i32.const 0x7FFFFFFF))
    (struct.get $HASHTABLE $size (local.get $table))
  ))

  (local.set $entry (array.get $BUCKET_ARRAY
    (struct.get $HASHTABLE $buckets (local.get $table))
    (local.get $bucket_idx)
  ))

  ;; Search chain
  (block $done
    (loop $loop
      (br_if $done (ref.is_null (local.get $entry)))

      (if (i32.eq (struct.get $ENTRY $hash (ref.cast (ref $ENTRY) (local.get $entry)))
                  (local.get $hash))
        (then
          (if (call $values_equal
                (struct.get $ENTRY $key (ref.cast (ref $ENTRY) (local.get $entry)))
                (local.get $key))
            (then (return (i32.const 1)))
          )
        )
      )

      (local.set $entry (struct.get $ENTRY $next (ref.cast (ref $ENTRY) (local.get $entry))))
      (br $loop)
    )
  )

  (i32.const 0)
)


;; Set key-value pair in hash table
;; Updates existing entry if key exists, otherwise adds new entry
(func $hashtable_set (param $table (ref $HASHTABLE)) (param $key (ref null eq)) (param $value (ref null eq))
  (local $hash i32)
  (local $bucket_idx i32)
  (local $entry (ref null $ENTRY))
  (local $new_entry (ref $ENTRY))
  (local $buckets (ref $BUCKET_ARRAY))

  (local.set $hash (call $hash_value (local.get $key)))
  (local.set $bucket_idx (i32.rem_u
    (i32.and (local.get $hash) (i32.const 0x7FFFFFFF))
    (struct.get $HASHTABLE $size (local.get $table))
  ))

  (local.set $buckets (struct.get $HASHTABLE $buckets (local.get $table)))
  (local.set $entry (array.get $BUCKET_ARRAY (local.get $buckets) (local.get $bucket_idx)))

  ;; Search for existing entry
  (block $not_found
    (block $found
      (loop $loop
        (br_if $not_found (ref.is_null (local.get $entry)))

        (if (i32.eq (struct.get $ENTRY $hash (ref.cast (ref $ENTRY) (local.get $entry)))
                    (local.get $hash))
          (then
            (if (call $values_equal
                  (struct.get $ENTRY $key (ref.cast (ref $ENTRY) (local.get $entry)))
                  (local.get $key))
              (then
                ;; Update existing entry
                (struct.set $ENTRY $value
                  (ref.cast (ref $ENTRY) (local.get $entry))
                  (local.get $value))
                (br $found)
              )
            )
          )
        )

        (local.set $entry (struct.get $ENTRY $next (ref.cast (ref $ENTRY) (local.get $entry))))
        (br $loop)
      )
    )
    (return)
  )

  ;; Create new entry and prepend to bucket
  (local.set $new_entry (struct.new $ENTRY
    (local.get $hash)
    (local.get $key)
    (local.get $value)
    (array.get $BUCKET_ARRAY (local.get $buckets) (local.get $bucket_idx))
  ))
  (array.set $BUCKET_ARRAY (local.get $buckets) (local.get $bucket_idx) (local.get $new_entry))

  ;; Increment count
  (struct.set $HASHTABLE $count (local.get $table)
    (i32.add (struct.get $HASHTABLE $count (local.get $table)) (i32.const 1)))
)


;; Delete key from hash table
;; Returns 1 if key was found and deleted, 0 otherwise
(func $hashtable_delete (param $table (ref $HASHTABLE)) (param $key (ref null eq)) (result i32)
  (local $hash i32)
  (local $bucket_idx i32)
  (local $entry (ref null $ENTRY))
  (local $prev (ref null $ENTRY))
  (local $buckets (ref $BUCKET_ARRAY))

  (local.set $hash (call $hash_value (local.get $key)))
  (local.set $bucket_idx (i32.rem_u
    (i32.and (local.get $hash) (i32.const 0x7FFFFFFF))
    (struct.get $HASHTABLE $size (local.get $table))
  ))

  (local.set $buckets (struct.get $HASHTABLE $buckets (local.get $table)))
  (local.set $entry (array.get $BUCKET_ARRAY (local.get $buckets) (local.get $bucket_idx)))

  ;; Search for entry
  (block $done
    (loop $loop
      (br_if $done (ref.is_null (local.get $entry)))

      (if (i32.eq (struct.get $ENTRY $hash (ref.cast (ref $ENTRY) (local.get $entry)))
                  (local.get $hash))
        (then
          (if (call $values_equal
                (struct.get $ENTRY $key (ref.cast (ref $ENTRY) (local.get $entry)))
                (local.get $key))
            (then
              ;; Found - remove from chain
              (if (ref.is_null (local.get $prev))
                (then
                  ;; First in bucket - update bucket head
                  (array.set $BUCKET_ARRAY (local.get $buckets) (local.get $bucket_idx)
                    (struct.get $ENTRY $next (ref.cast (ref $ENTRY) (local.get $entry))))
                )
                (else
                  ;; Not first - update prev's next
                  (struct.set $ENTRY $next (ref.cast (ref $ENTRY) (local.get $prev))
                    (struct.get $ENTRY $next (ref.cast (ref $ENTRY) (local.get $entry))))
                )
              )

              ;; Decrement count
              (struct.set $HASHTABLE $count (local.get $table)
                (i32.sub (struct.get $HASHTABLE $count (local.get $table)) (i32.const 1)))
              (return (i32.const 1))
            )
          )
        )
      )

      (local.set $prev (local.get $entry))
      (local.set $entry (struct.get $ENTRY $next (ref.cast (ref $ENTRY) (local.get $entry))))
      (br $loop)
    )
  )

  (i32.const 0)
)


;; Get hash table size (number of entries)
(func $hashtable_len (param $table (ref $HASHTABLE)) (result i32)
  (struct.get $HASHTABLE $count (local.get $table))
)


;; Iterate over hash table entries, calling a function for each
;; Returns a PAIR chain of all entries (for keys/values/items)
(func $hashtable_entries (param $table (ref $HASHTABLE)) (result (ref null eq))
  (local $result (ref null eq))
  (local $buckets (ref $BUCKET_ARRAY))
  (local $size i32)
  (local $i i32)
  (local $entry (ref null $ENTRY))

  (local.set $buckets (struct.get $HASHTABLE $buckets (local.get $table)))
  (local.set $size (struct.get $HASHTABLE $size (local.get $table)))
  (local.set $result (ref.null eq))

  (block $done
    (loop $bucket_loop
      (br_if $done (i32.ge_u (local.get $i) (local.get $size)))

      (local.set $entry (array.get $BUCKET_ARRAY (local.get $buckets) (local.get $i)))

      ;; Iterate through chain in this bucket
      (block $chain_done
        (loop $chain_loop
          (br_if $chain_done (ref.is_null (local.get $entry)))

          ;; Add (key, value) pair to result
          (local.set $result
            (struct.new $PAIR
              (struct.new $PAIR
                (struct.get $ENTRY $key (ref.cast (ref $ENTRY) (local.get $entry)))
                (struct.get $ENTRY $value (ref.cast (ref $ENTRY) (local.get $entry))))
              (local.get $result)))

          (local.set $entry (struct.get $ENTRY $next (ref.cast (ref $ENTRY) (local.get $entry))))
          (br $chain_loop)
        )
      )

      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      (br $bucket_loop)
    )
  )

  (local.get $result)
)


;; =============================================================================
;; Dict Operations (using hash table internally)
;; =============================================================================

;; Create empty dict with default capacity
(func $dict_new (result (ref $DICT))
  (struct.new $DICT (call $hashtable_new (i32.const 16)))
)


;; dict_get: get value by key from dict
;; Handles both $DICT (hash table) and legacy PAIR chains for compatibility
(func $dict_get (param $dict (ref null eq)) (param $key (ref null eq)) (result (ref null eq))
  (local $current (ref null eq))
  (local $entry (ref null eq))
  (local $entry_arr (ref $ARRAY_ANY))

  ;; Handle null
  (if (ref.is_null (local.get $dict))
    (then (return (ref.null eq)))
  )

  ;; If $DICT (hash table based), use hashtable_get
  (if (ref.test (ref $DICT) (local.get $dict))
    (then
      (return (call $hashtable_get
        (struct.get $DICT $table (ref.cast (ref $DICT) (local.get $dict)))
        (local.get $key)))
    )
  )

  ;; Legacy: handle PAIR chains for backwards compatibility
  (if (ref.test (ref $EMPTY_LIST) (local.get $dict))
    (then (return (ref.null eq)))
  )

  (local.set $current (local.get $dict))
  (block $done
    (loop $loop
      (br_if $done (ref.is_null (local.get $current)))
      (if (i32.eqz (ref.test (ref $PAIR) (local.get $current)))
        (then (br $done))
      )
      (local.set $entry (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $current))))
      ;; Handle $TUPLE entries
      (if (ref.test (ref $TUPLE) (local.get $entry))
        (then
          (local.set $entry_arr (struct.get $TUPLE 0 (ref.cast (ref $TUPLE) (local.get $entry))))
          (if (call $values_equal (local.get $key) (array.get $ARRAY_ANY (local.get $entry_arr) (i32.const 0)))
            (then (return (array.get $ARRAY_ANY (local.get $entry_arr) (i32.const 1))))
          )
        )
        (else
          (if (call $values_equal (local.get $key) (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $entry))))
            (then (return (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $entry)))))
          )
        )
      )
      (local.set $current (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current))))
      (br $loop)
    )
  )
  (ref.null eq)
)


;; dict_get_default: get value by key with default if not found
(func $dict_get_default (param $dict (ref null eq)) (param $key (ref null eq)) (param $default (ref null eq)) (result (ref null eq))
  (local $result (ref null eq))

  ;; Handle null
  (if (ref.is_null (local.get $dict))
    (then (return (local.get $default)))
  )

  ;; If $DICT (hash table based), use hashtable_get
  (if (ref.test (ref $DICT) (local.get $dict))
    (then
      (local.set $result (call $hashtable_get
        (struct.get $DICT $table (ref.cast (ref $DICT) (local.get $dict)))
        (local.get $key)))
      (if (ref.is_null (local.get $result))
        (then (return (local.get $default)))
        (else (return (local.get $result)))
      )
    )
  )

  ;; Legacy: use dict_get and check for null
  (local.set $result (call $dict_get (local.get $dict) (local.get $key)))
  (if (ref.is_null (local.get $result))
    (then (return (local.get $default)))
  )
  (local.get $result)
)


;; dict_contains: check if key is in dict
(func $dict_contains (param $dict (ref null eq)) (param $key (ref null eq)) (result i32)
  (local $current (ref null eq))
  (local $entry (ref null eq))
  (local $entry_arr (ref $ARRAY_ANY))

  ;; Handle null
  (if (ref.is_null (local.get $dict))
    (then (return (i32.const 0)))
  )

  ;; If $DICT (hash table based), use hashtable_contains
  (if (ref.test (ref $DICT) (local.get $dict))
    (then
      (return (call $hashtable_contains
        (struct.get $DICT $table (ref.cast (ref $DICT) (local.get $dict)))
        (local.get $key)))
    )
  )

  ;; Legacy: handle PAIR chains
  (if (ref.test (ref $EMPTY_LIST) (local.get $dict))
    (then (return (i32.const 0)))
  )

  (local.set $current (local.get $dict))
  (block $done
    (loop $loop
      (br_if $done (ref.is_null (local.get $current)))
      (if (i32.eqz (ref.test (ref $PAIR) (local.get $current)))
        (then (br $done))
      )
      (local.set $entry (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $current))))
      (if (ref.test (ref $TUPLE) (local.get $entry))
        (then
          (local.set $entry_arr (struct.get $TUPLE 0 (ref.cast (ref $TUPLE) (local.get $entry))))
          (if (call $values_equal (local.get $key) (array.get $ARRAY_ANY (local.get $entry_arr) (i32.const 0)))
            (then (return (i32.const 1)))
          )
        )
        (else
          (if (call $values_equal (local.get $key) (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $entry))))
            (then (return (i32.const 1)))
          )
        )
      )
      (local.set $current (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current))))
      (br $loop)
    )
  )
  (i32.const 0)
)


;; dict_set: set key-value pair in dict
;; For $DICT, modifies in place and returns the same dict
(func $dict_set (param $dict (ref null eq)) (param $key (ref null eq)) (param $value (ref null eq)) (result (ref null eq))
  (local $new_dict (ref $DICT))
  (local $new_entry (ref null $PAIR))

  ;; If $DICT (hash table based), set in place
  (if (ref.test (ref $DICT) (local.get $dict))
    (then
      (call $hashtable_set
        (struct.get $DICT $table (ref.cast (ref $DICT) (local.get $dict)))
        (local.get $key)
        (local.get $value))
      (return (local.get $dict))
    )
  )

  ;; Handle null or EMPTY_LIST - create new hash-table dict
  (if (i32.or (ref.is_null (local.get $dict)) (ref.test (ref $EMPTY_LIST) (local.get $dict)))
    (then
      (local.set $new_dict (call $dict_new))
      (call $hashtable_set
        (struct.get $DICT $table (local.get $new_dict))
        (local.get $key)
        (local.get $value))
      (return (local.get $new_dict))
    )
  )

  ;; Legacy PAIR chain - convert to hash table dict
  ;; For now, just prepend (old behavior for backwards compat)
  (local.set $new_entry (struct.new $PAIR (local.get $key) (local.get $value)))
  (struct.new $PAIR (local.get $new_entry) (local.get $dict))
)


;; dict_set_wrapped: Same as dict_set (both handle $DICT now)
(func $dict_set_wrapped (param $dict (ref null eq)) (param $key (ref null eq)) (param $value (ref null eq)) (result (ref null eq))
  (call $dict_set (local.get $dict) (local.get $key) (local.get $value))
)


;; dict_delete: delete key from dict
(func $dict_delete (param $dict (ref null eq)) (param $key (ref null eq)) (result (ref null eq))
  (local $current (ref null eq))
  (local $prev (ref null $PAIR))
  (local $entry (ref null eq))
  (local $first (ref null eq))

  ;; Handle null
  (if (ref.is_null (local.get $dict))
    (then (return (local.get $dict)))
  )

  ;; If $DICT (hash table based), use hashtable_delete
  (if (ref.test (ref $DICT) (local.get $dict))
    (then
      (drop (call $hashtable_delete
        (struct.get $DICT $table (ref.cast (ref $DICT) (local.get $dict)))
        (local.get $key)))
      (return (local.get $dict))
    )
  )

  ;; Legacy PAIR chain handling
  (if (ref.test (ref $EMPTY_LIST) (local.get $dict))
    (then (return (local.get $dict)))
  )

  (local.set $entry (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $dict))))
  (if (call $values_equal (local.get $key) (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $entry))))
    (then (return (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $dict)))))
  )

  (local.set $first (local.get $dict))
  (local.set $prev (ref.cast (ref $PAIR) (local.get $dict)))
  (local.set $current (struct.get $PAIR 1 (local.get $prev)))

  (block $done
    (loop $loop
      (br_if $done (ref.is_null (local.get $current)))
      (if (i32.eqz (ref.test (ref $PAIR) (local.get $current)))
        (then (br $done))
      )
      (local.set $entry (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $current))))
      (if (call $values_equal (local.get $key) (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $entry))))
        (then
          (struct.set $PAIR 1 (local.get $prev)
            (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current))))
          (return (local.get $first))
        )
      )
      (local.set $prev (ref.cast (ref $PAIR) (local.get $current)))
      (local.set $current (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current))))
      (br $loop)
    )
  )
  (local.get $first)
)


;; dict_keys: return list of keys from dict
(func $dict_keys (param $dict (ref null eq)) (result (ref null eq))
  (local $entries (ref null eq))
  (local $result (ref null eq))
  (local $current (ref null eq))
  (local $entry (ref null eq))
  (local $new_pair (ref null $PAIR))
  (local $tail (ref null eq))

  (if (ref.is_null (local.get $dict))
    (then (return (struct.new $EMPTY_LIST)))
  )

  ;; If $DICT (hash table based), get entries and extract keys
  (if (ref.test (ref $DICT) (local.get $dict))
    (then
      (local.set $entries (call $hashtable_entries
        (struct.get $DICT $table (ref.cast (ref $DICT) (local.get $dict)))))

      ;; Extract keys from entries
      (local.set $current (local.get $entries))
      (block $done
        (loop $loop
          (br_if $done (ref.is_null (local.get $current)))
          (local.set $entry (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $current))))
          (local.set $new_pair (struct.new $PAIR
            (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $entry)))
            (ref.null eq)))
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
      (if (ref.is_null (local.get $result))
        (then (return (struct.new $EMPTY_LIST)))
      )
      (return (local.get $result))
    )
  )

  ;; Legacy PAIR chain
  (local.set $current (local.get $dict))
  (block $done
    (loop $loop
      (br_if $done (ref.is_null (local.get $current)))
      (if (i32.eqz (ref.test (ref $PAIR) (local.get $current)))
        (then (br $done))
      )
      (local.set $entry (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $current))))
      (local.set $new_pair (struct.new $PAIR
        (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $entry)))
        (ref.null eq)))
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
  (if (ref.is_null (local.get $result))
    (then (return (struct.new $EMPTY_LIST)))
  )
  (local.get $result)
)


;; dict_values: return list of values from dict
(func $dict_values (param $dict (ref null eq)) (result (ref null eq))
  (local $entries (ref null eq))
  (local $result (ref null eq))
  (local $current (ref null eq))
  (local $entry (ref null eq))
  (local $new_pair (ref null $PAIR))
  (local $tail (ref null eq))

  (if (ref.is_null (local.get $dict))
    (then (return (struct.new $EMPTY_LIST)))
  )

  ;; If $DICT (hash table based)
  (if (ref.test (ref $DICT) (local.get $dict))
    (then
      (local.set $entries (call $hashtable_entries
        (struct.get $DICT $table (ref.cast (ref $DICT) (local.get $dict)))))

      (local.set $current (local.get $entries))
      (block $done
        (loop $loop
          (br_if $done (ref.is_null (local.get $current)))
          (local.set $entry (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $current))))
          (local.set $new_pair (struct.new $PAIR
            (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $entry)))
            (ref.null eq)))
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
      (if (ref.is_null (local.get $result))
        (then (return (struct.new $EMPTY_LIST)))
      )
      (return (local.get $result))
    )
  )

  ;; Legacy
  (local.set $current (local.get $dict))
  (block $done
    (loop $loop
      (br_if $done (ref.is_null (local.get $current)))
      (if (i32.eqz (ref.test (ref $PAIR) (local.get $current)))
        (then (br $done))
      )
      (local.set $entry (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $current))))
      (local.set $new_pair (struct.new $PAIR
        (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $entry)))
        (ref.null eq)))
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
  (if (ref.is_null (local.get $result))
    (then (return (struct.new $EMPTY_LIST)))
  )
  (local.get $result)
)


;; dict_items: return list of (key, value) pairs from dict
(func $dict_items (param $dict (ref null eq)) (result (ref null eq))
  (local $entries (ref null eq))
  (local $result (ref null eq))
  (local $current (ref null eq))
  (local $entry (ref null eq))
  (local $new_pair (ref null $PAIR))
  (local $tail (ref null eq))

  (if (ref.is_null (local.get $dict))
    (then (return (struct.new $EMPTY_LIST)))
  )

  ;; If $DICT (hash table based), entries are already (key, value) pairs
  (if (ref.test (ref $DICT) (local.get $dict))
    (then
      (local.set $entries (call $hashtable_entries
        (struct.get $DICT $table (ref.cast (ref $DICT) (local.get $dict)))))

      (local.set $current (local.get $entries))
      (block $done
        (loop $loop
          (br_if $done (ref.is_null (local.get $current)))
          (local.set $entry (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $current))))
          (local.set $new_pair (struct.new $PAIR (local.get $entry) (ref.null eq)))
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
      (if (ref.is_null (local.get $result))
        (then (return (struct.new $EMPTY_LIST)))
      )
      (return (local.get $result))
    )
  )

  ;; Legacy
  (local.set $current (local.get $dict))
  (block $done
    (loop $loop
      (br_if $done (ref.is_null (local.get $current)))
      (if (i32.eqz (ref.test (ref $PAIR) (local.get $current)))
        (then (br $done))
      )
      (local.set $entry (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $current))))
      (local.set $new_pair (struct.new $PAIR (local.get $entry) (ref.null eq)))
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
  (if (ref.is_null (local.get $result))
    (then (return (struct.new $EMPTY_LIST)))
  )
  (local.get $result)
)


;; dict_pop: remove and return value for key
(func $dict_pop (param $dict (ref null eq)) (param $key (ref null eq)) (param $default (ref null eq)) (result (ref null eq) (ref null eq))
  (local $result (ref null eq))

  (if (ref.is_null (local.get $dict))
    (then (return (local.get $default) (local.get $dict)))
  )

  ;; If $DICT (hash table based)
  (if (ref.test (ref $DICT) (local.get $dict))
    (then
      ;; Get value first
      (local.set $result (call $hashtable_get
        (struct.get $DICT $table (ref.cast (ref $DICT) (local.get $dict)))
        (local.get $key)))

      (if (ref.is_null (local.get $result))
        (then (return (local.get $default) (local.get $dict)))
      )

      ;; Delete the key
      (drop (call $hashtable_delete
        (struct.get $DICT $table (ref.cast (ref $DICT) (local.get $dict)))
        (local.get $key)))

      (return (local.get $result) (local.get $dict))
    )
  )

  ;; Legacy - just return default
  (local.get $default) (local.get $dict)
)


;; dict_setdefault: if key exists return value, else set key to default and return default
(func $dict_setdefault (param $dict (ref null eq)) (param $key (ref null eq)) (param $default (ref null eq)) (result (ref null eq) (ref null eq))
  (local $value (ref null eq))

  (if (ref.is_null (local.get $dict))
    (then
      ;; Create new dict with key=default
      (return (local.get $default) (call $dict_set (local.get $dict) (local.get $key) (local.get $default)))
    )
  )

  ;; If $DICT (hash table based)
  (if (ref.test (ref $DICT) (local.get $dict))
    (then
      (local.set $value (call $hashtable_get
        (struct.get $DICT $table (ref.cast (ref $DICT) (local.get $dict)))
        (local.get $key)))

      (if (i32.eqz (ref.is_null (local.get $value)))
        (then (return (local.get $value) (local.get $dict)))
      )

      ;; Key doesn't exist - set it
      (call $hashtable_set
        (struct.get $DICT $table (ref.cast (ref $DICT) (local.get $dict)))
        (local.get $key)
        (local.get $default))
      (return (local.get $default) (local.get $dict))
    )
  )

  ;; Legacy
  (local.set $value (call $dict_get (local.get $dict) (local.get $key)))
  (if (i32.eqz (ref.is_null (local.get $value)))
    (then (return (local.get $value) (local.get $dict)))
  )
  (return (local.get $default) (call $dict_set_wrapped (local.get $dict) (local.get $key) (local.get $default)))
)


;; dict_update: merge another dict into this one
(func $dict_update (param $dict (ref null eq)) (param $other (ref null eq)) (result (ref null eq))
  (local $entries (ref null eq))
  (local $current (ref null eq))
  (local $entry (ref null eq))
  (local $result (ref null eq))

  (if (ref.is_null (local.get $other))
    (then (return (local.get $dict)))
  )

  ;; Ensure we have a $DICT
  (if (ref.is_null (local.get $dict))
    (then (local.set $result (call $dict_new)))
    (else
      (if (ref.test (ref $DICT) (local.get $dict))
        (then (local.set $result (local.get $dict)))
        (else (local.set $result (call $dict_new)))
      )
    )
  )

  ;; Get entries from other dict
  (if (ref.test (ref $DICT) (local.get $other))
    (then
      (local.set $entries (call $hashtable_entries
        (struct.get $DICT $table (ref.cast (ref $DICT) (local.get $other)))))
    )
    (else
      ;; Legacy PAIR chain
      (local.set $entries (local.get $other))
    )
  )

  ;; Add all entries to result
  (local.set $current (local.get $entries))
  (block $done
    (loop $loop
      (br_if $done (ref.is_null (local.get $current)))
      (if (i32.eqz (ref.test (ref $PAIR) (local.get $current)))
        (then (br $done))
      )
      (local.set $entry (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $current))))
      (call $hashtable_set
        (struct.get $DICT $table (ref.cast (ref $DICT) (local.get $result)))
        (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $entry)))
        (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $entry))))
      (local.set $current (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current))))
      (br $loop)
    )
  )

  (local.get $result)
)


;; dict_clear: return empty dict
(func $dict_clear (param $dict (ref null eq)) (result (ref null eq))
  (call $dict_new)
)


;; dict_copy: shallow copy of dict, or create dict from iterable of (key, value) pairs
(func $dict_copy (param $dict (ref null eq)) (result (ref null eq))
  (local $new_dict (ref $DICT))
  (local $entries (ref null eq))
  (local $current (ref null eq))
  (local $entry (ref null eq))
  (local $i i32)

  (if (ref.is_null (local.get $dict))
    (then (return (call $dict_new)))
  )

  (local.set $new_dict (call $dict_new))

  ;; If $DICT (hash table based)
  (if (ref.test (ref $DICT) (local.get $dict))
    (then
      (local.set $entries (call $hashtable_entries
        (struct.get $DICT $table (ref.cast (ref $DICT) (local.get $dict)))))

      (local.set $current (local.get $entries))
      (block $done
        (loop $loop
          (br_if $done (ref.is_null (local.get $current)))
          (local.set $entry (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $current))))
          (call $hashtable_set
            (struct.get $DICT $table (local.get $new_dict))
            (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $entry)))
            (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $entry))))
          (local.set $current (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current))))
          (br $loop)
        )
      )
      (return (local.get $new_dict))
    )
  )

  ;; Handle $LIST input (e.g., from zip() returning list of tuples)
  (if (ref.test (ref $LIST) (local.get $dict))
    (then
      (local.set $current (local.get $dict))
      (block $list_done
        (loop $list_loop
          ;; Get list data and length
          (if (i32.ge_s (local.get $i)
                (struct.get $LIST $len (ref.cast (ref $LIST) (local.get $current))))
            (then (br $list_done))
          )
          ;; Get element at index i
          (local.set $entry
            (array.get $ARRAY_ANY
              (struct.get $LIST $data (ref.cast (ref $LIST) (local.get $current)))
              (local.get $i)))
          ;; Entry should be a $TUPLE with 2 elements (key, value)
          (if (ref.test (ref $TUPLE) (local.get $entry))
            (then
              (call $hashtable_set
                (struct.get $DICT $table (local.get $new_dict))
                (array.get $ARRAY_ANY
                  (struct.get $TUPLE $data (ref.cast (ref $TUPLE) (local.get $entry)))
                  (i32.const 0))
                (array.get $ARRAY_ANY
                  (struct.get $TUPLE $data (ref.cast (ref $TUPLE) (local.get $entry)))
                  (i32.const 1)))
            )
            ;; Also handle PAIR entries (legacy)
            (else
              (if (ref.test (ref $PAIR) (local.get $entry))
                (then
                  (call $hashtable_set
                    (struct.get $DICT $table (local.get $new_dict))
                    (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $entry)))
                    (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $entry))))
                )
              )
            )
          )
          (local.set $i (i32.add (local.get $i) (i32.const 1)))
          (br $list_loop)
        )
      )
      (return (local.get $new_dict))
    )
  )

  ;; Legacy - copy from PAIR chain (e.g., from zip() which returns PAIR chain of tuples)
  (local.set $current (local.get $dict))
  (block $done
    (loop $loop
      (br_if $done (ref.is_null (local.get $current)))
      (if (i32.eqz (ref.test (ref $PAIR) (local.get $current)))
        (then (br $done))
      )
      (local.set $entry (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $current))))
      ;; Entry could be a $TUPLE (from zip) or a $PAIR (legacy)
      (if (ref.test (ref $TUPLE) (local.get $entry))
        (then
          (call $hashtable_set
            (struct.get $DICT $table (local.get $new_dict))
            (array.get $ARRAY_ANY
              (struct.get $TUPLE $data (ref.cast (ref $TUPLE) (local.get $entry)))
              (i32.const 0))
            (array.get $ARRAY_ANY
              (struct.get $TUPLE $data (ref.cast (ref $TUPLE) (local.get $entry)))
              (i32.const 1)))
        )
        (else
          (if (ref.test (ref $PAIR) (local.get $entry))
            (then
              (call $hashtable_set
                (struct.get $DICT $table (local.get $new_dict))
                (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $entry)))
                (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $entry))))
            )
          )
        )
      )
      (local.set $current (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current))))
      (br $loop)
    )
  )
  (local.get $new_dict)
)


;; dict_to_string: convert dict to string "{key: val, ...}"
(func $dict_to_string (param $dict (ref null eq)) (result (ref $STRING))
  (local $result (ref $STRING))
  (local $entries (ref null eq))
  (local $current (ref null eq))
  (local $kv (ref null $PAIR))
  (local $key_str (ref $STRING))
  (local $val_str (ref $STRING))
  (local $first i32)
  (local $offset i32)
  (local $comma_space (ref $STRING))
  (local $brace_open (ref $STRING))
  (local $brace_close (ref $STRING))
  (local $colon_space (ref $STRING))

  ;; Create "{" string
  (local.set $offset (global.get $string_heap))
  (i32.store8 (local.get $offset) (i32.const 123))  ;; {
  (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 1)))
  (local.set $brace_open (struct.new $STRING (local.get $offset) (i32.const 1)))

  ;; Create "}" string
  (local.set $offset (global.get $string_heap))
  (i32.store8 (local.get $offset) (i32.const 125))  ;; }
  (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 1)))
  (local.set $brace_close (struct.new $STRING (local.get $offset) (i32.const 1)))

  ;; Create ", " string
  (local.set $offset (global.get $string_heap))
  (i32.store8 (local.get $offset) (i32.const 44))  ;; ,
  (i32.store8 (i32.add (local.get $offset) (i32.const 1)) (i32.const 32))  ;; space
  (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 2)))
  (local.set $comma_space (struct.new $STRING (local.get $offset) (i32.const 2)))

  ;; Create ": " string
  (local.set $offset (global.get $string_heap))
  (i32.store8 (local.get $offset) (i32.const 58))  ;; :
  (i32.store8 (i32.add (local.get $offset) (i32.const 1)) (i32.const 32))  ;; space
  (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 2)))
  (local.set $colon_space (struct.new $STRING (local.get $offset) (i32.const 2)))

  (local.set $result (local.get $brace_open))
  (local.set $first (i32.const 1))

  ;; Get entries
  (if (ref.test (ref $DICT) (local.get $dict))
    (then
      (local.set $entries (call $hashtable_entries
        (struct.get $DICT $table (ref.cast (ref $DICT) (local.get $dict)))))
    )
    (else
      (local.set $entries (local.get $dict))
    )
  )

  (local.set $current (local.get $entries))

  (block $done
    (loop $loop
      (br_if $done (ref.is_null (local.get $current)))

      (if (i32.eqz (local.get $first))
        (then
          (local.set $result (call $string_concat (local.get $result) (local.get $comma_space)))
        )
      )
      (local.set $first (i32.const 0))

      (local.set $kv (ref.cast (ref $PAIR) (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $current)))))
      (local.set $key_str (call $value_to_string_repr (struct.get $PAIR 0 (local.get $kv))))
      (local.set $result (call $string_concat (local.get $result) (local.get $key_str)))
      (local.set $result (call $string_concat (local.get $result) (local.get $colon_space)))
      (local.set $val_str (call $value_to_string_repr (struct.get $PAIR 1 (local.get $kv))))
      (local.set $result (call $string_concat (local.get $result) (local.get $val_str)))

      (local.set $current (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current))))
      (br $loop)
    )
  )

  (call $string_concat (local.get $result) (local.get $brace_close))
)


;; =============================================================================
;; Legacy Dict V2 Operations (for backwards compatibility)
;; =============================================================================

;; Create empty dict with default capacity
(func $dict_v2_new (result (ref $DICT_V2))
  (struct.new $DICT_V2 (call $hashtable_new (i32.const 16)))
)


;; Get value by key from dict
(func $dict_v2_get (param $dict (ref $DICT_V2)) (param $key (ref null eq)) (result (ref null eq))
  (call $hashtable_get (struct.get $DICT_V2 $table (local.get $dict)) (local.get $key))
)


;; Set key-value pair in dict
(func $dict_v2_set (param $dict (ref $DICT_V2)) (param $key (ref null eq)) (param $value (ref null eq))
  (call $hashtable_set (struct.get $DICT_V2 $table (local.get $dict)) (local.get $key) (local.get $value))
)


;; Check if key exists in dict
(func $dict_v2_contains (param $dict (ref $DICT_V2)) (param $key (ref null eq)) (result i32)
  (call $hashtable_contains (struct.get $DICT_V2 $table (local.get $dict)) (local.get $key))
)


;; Delete key from dict
(func $dict_v2_delete (param $dict (ref $DICT_V2)) (param $key (ref null eq)) (result i32)
  (call $hashtable_delete (struct.get $DICT_V2 $table (local.get $dict)) (local.get $key))
)


;; Get dict length
(func $dict_v2_len (param $dict (ref $DICT_V2)) (result i32)
  (call $hashtable_len (struct.get $DICT_V2 $table (local.get $dict)))
)

"""
