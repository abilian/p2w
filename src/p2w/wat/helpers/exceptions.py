"""WAT helper functions: Exception handling."""

from __future__ import annotations

EXCEPTIONS_CODE = """

;; =============================================================================
;; Exception Handling Helpers
;; =============================================================================

;; make_exception: create a new exception object
;; type_name should be the exception class name as a STRING
(func $make_exception (param $type_name (ref $STRING)) (param $message (ref null eq)) (result (ref $EXCEPTION))
  (struct.new $EXCEPTION
    (local.get $type_name)
    (local.get $message)
    (ref.null eq)   ;; cause
    (ref.null eq))  ;; context
)


;; make_exception_with_cause: create exception with chaining
(func $make_exception_with_cause
  (param $type_name (ref $STRING))
  (param $message (ref null eq))
  (param $cause (ref null eq))
  (result (ref $EXCEPTION))
  (struct.new $EXCEPTION
    (local.get $type_name)
    (local.get $message)
    (local.get $cause)
    (ref.null eq))
)


;; exception_get_type: get exception type name
(func $exception_get_type (param $exc (ref $EXCEPTION)) (result (ref $STRING))
  (struct.get $EXCEPTION $type (local.get $exc))
)


;; exception_get_message: get exception message
(func $exception_get_message (param $exc (ref $EXCEPTION)) (result (ref null eq))
  (struct.get $EXCEPTION $message (local.get $exc))
)


;; exception_matches: check if exception matches a type name
;; Returns 1 if the exception type equals the given type name
(func $exception_matches (param $exc (ref $EXCEPTION)) (param $type_name (ref $STRING)) (result i32)
  (call $strings_equal
    (struct.get $EXCEPTION $type (local.get $exc))
    (local.get $type_name))
)


;; exception_matches_any: check if exception matches any type in a list
;; type_list is a PAIR chain of STRING type names, returns 1 if any match
(func $exception_matches_any (param $exc (ref $EXCEPTION)) (param $type_list (ref null eq)) (result i32)
  (local $current (ref null eq))
  (local $type_name (ref $STRING))
  (local.set $current (local.get $type_list))
  (block $done
    (loop $check
      (br_if $done (ref.is_null (local.get $current)))
      ;; Get current type name
      (local.set $type_name
        (ref.cast (ref $STRING)
          (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $current)))))
      ;; Check if it matches
      (if (call $exception_matches (local.get $exc) (local.get $type_name))
        (then (return (i32.const 1)))
      )
      ;; Move to next
      (local.set $current
        (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $current))))
      (br $check)
    )
  )
  (i32.const 0)
)


;; is_base_exception: check if type is a subtype of BaseException
;; For now, all exception types are considered subtypes
;; In a full implementation, this would check the exception hierarchy
(func $is_base_exception (param $type_name (ref $STRING)) (result i32)
  ;; For now, always return true - all exceptions are BaseException subtypes
  (i32.const 1)
)


;; exception_to_string: convert exception to string for printing
(func $exception_to_string (param $exc (ref $EXCEPTION)) (result (ref $STRING))
  (local $type_str (ref null eq))
  (local $msg (ref null eq))
  (local $msg_str (ref null eq))
  (local $result (ref null eq))

  (local.set $type_str (struct.get $EXCEPTION $type (local.get $exc)))
  (local.set $msg (struct.get $EXCEPTION $message (local.get $exc)))

  ;; If message is null, just return type name
  (if (ref.is_null (local.get $msg))
    (then (return (ref.cast (ref $STRING) (local.get $type_str))))
  )

  ;; Otherwise, format as "TypeName: message"
  (if (ref.test (ref $STRING) (local.get $msg))
    (then
      (local.set $msg_str (ref.cast (ref $STRING) (local.get $msg)))
    )
    (else
      (local.set $msg_str (call $value_to_string (local.get $msg)))
    )
  )

  ;; Concatenate: type + ": " + message
  (local.set $result (call $string_concat (ref.cast (ref $STRING) (local.get $type_str)) (call $make_string_colon_space)))
  (local.set $result (call $string_concat (ref.cast (ref $STRING) (local.get $result)) (ref.cast (ref $STRING) (local.get $msg_str))))
  (ref.cast (ref $STRING) (local.get $result))
)


;; make_string_colon_space: helper to create ": " string
(func $make_string_colon_space (result (ref $STRING))
  (local $offset i32)
  (local.set $offset (global.get $string_heap))
  (i32.store8 (local.get $offset) (i32.const 58))  ;; ':'
  (i32.store8 (i32.add (local.get $offset) (i32.const 1)) (i32.const 32))  ;; ' '
  (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 2)))
  (struct.new $STRING (local.get $offset) (i32.const 2))
)


;; raise_exception: throw an exception (convenience wrapper)
(func $raise_exception (param $exc (ref $EXCEPTION))
  (throw $PyException (local.get $exc))
)


;; make_assertion_error: create AssertionError exception
(func $make_assertion_error (param $message (ref null eq)) (result (ref $EXCEPTION))
  (call $make_exception (call $make_string_assertion_error) (local.get $message))
)


;; make_string_assertion_error: create "AssertionError" string
(func $make_string_assertion_error (result (ref $STRING))
  (local $offset i32)
  (local.set $offset (global.get $string_heap))
  ;; "AssertionError" = 14 chars
  (i32.store8 (local.get $offset) (i32.const 65))  ;; 'A'
  (i32.store8 (i32.add (local.get $offset) (i32.const 1)) (i32.const 115))  ;; 's'
  (i32.store8 (i32.add (local.get $offset) (i32.const 2)) (i32.const 115))  ;; 's'
  (i32.store8 (i32.add (local.get $offset) (i32.const 3)) (i32.const 101))  ;; 'e'
  (i32.store8 (i32.add (local.get $offset) (i32.const 4)) (i32.const 114))  ;; 'r'
  (i32.store8 (i32.add (local.get $offset) (i32.const 5)) (i32.const 116))  ;; 't'
  (i32.store8 (i32.add (local.get $offset) (i32.const 6)) (i32.const 105))  ;; 'i'
  (i32.store8 (i32.add (local.get $offset) (i32.const 7)) (i32.const 111))  ;; 'o'
  (i32.store8 (i32.add (local.get $offset) (i32.const 8)) (i32.const 110))  ;; 'n'
  (i32.store8 (i32.add (local.get $offset) (i32.const 9)) (i32.const 69))   ;; 'E'
  (i32.store8 (i32.add (local.get $offset) (i32.const 10)) (i32.const 114)) ;; 'r'
  (i32.store8 (i32.add (local.get $offset) (i32.const 11)) (i32.const 114)) ;; 'r'
  (i32.store8 (i32.add (local.get $offset) (i32.const 12)) (i32.const 111)) ;; 'o'
  (i32.store8 (i32.add (local.get $offset) (i32.const 13)) (i32.const 114)) ;; 'r'
  (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 14)))
  (struct.new $STRING (local.get $offset) (i32.const 14))
)


;; make_string_attribute_error: create "AttributeError" string
(func $make_string_attribute_error (result (ref $STRING))
  (local $offset i32)
  (local.set $offset (global.get $string_heap))
  ;; "AttributeError" = 14 chars
  (i32.store8 (local.get $offset) (i32.const 65))  ;; 'A'
  (i32.store8 (i32.add (local.get $offset) (i32.const 1)) (i32.const 116))  ;; 't'
  (i32.store8 (i32.add (local.get $offset) (i32.const 2)) (i32.const 116))  ;; 't'
  (i32.store8 (i32.add (local.get $offset) (i32.const 3)) (i32.const 114))  ;; 'r'
  (i32.store8 (i32.add (local.get $offset) (i32.const 4)) (i32.const 105))  ;; 'i'
  (i32.store8 (i32.add (local.get $offset) (i32.const 5)) (i32.const 98))   ;; 'b'
  (i32.store8 (i32.add (local.get $offset) (i32.const 6)) (i32.const 117))  ;; 'u'
  (i32.store8 (i32.add (local.get $offset) (i32.const 7)) (i32.const 116))  ;; 't'
  (i32.store8 (i32.add (local.get $offset) (i32.const 8)) (i32.const 101))  ;; 'e'
  (i32.store8 (i32.add (local.get $offset) (i32.const 9)) (i32.const 69))   ;; 'E'
  (i32.store8 (i32.add (local.get $offset) (i32.const 10)) (i32.const 114)) ;; 'r'
  (i32.store8 (i32.add (local.get $offset) (i32.const 11)) (i32.const 114)) ;; 'r'
  (i32.store8 (i32.add (local.get $offset) (i32.const 12)) (i32.const 111)) ;; 'o'
  (i32.store8 (i32.add (local.get $offset) (i32.const 13)) (i32.const 114)) ;; 'r'
  (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 14)))
  (struct.new $STRING (local.get $offset) (i32.const 14))
)


;; throw_attribute_error: throw an AttributeError exception
(func $throw_attribute_error (param $message (ref null eq))
  (local $exc (ref $EXCEPTION))
  (local.set $exc (call $make_exception (call $make_string_attribute_error) (local.get $message)))
  (throw $PyException (local.get $exc))
)


;; make_string_cause: create "__cause__" string for exception chaining
(func $make_string_cause (result (ref $STRING))
  (local $offset i32)
  (local.set $offset (global.get $string_heap))
  ;; "__cause__" = 9 chars
  (i32.store8 (local.get $offset) (i32.const 95))  ;; '_'
  (i32.store8 (i32.add (local.get $offset) (i32.const 1)) (i32.const 95))   ;; '_'
  (i32.store8 (i32.add (local.get $offset) (i32.const 2)) (i32.const 99))   ;; 'c'
  (i32.store8 (i32.add (local.get $offset) (i32.const 3)) (i32.const 97))   ;; 'a'
  (i32.store8 (i32.add (local.get $offset) (i32.const 4)) (i32.const 117))  ;; 'u'
  (i32.store8 (i32.add (local.get $offset) (i32.const 5)) (i32.const 115))  ;; 's'
  (i32.store8 (i32.add (local.get $offset) (i32.const 6)) (i32.const 101))  ;; 'e'
  (i32.store8 (i32.add (local.get $offset) (i32.const 7)) (i32.const 95))   ;; '_'
  (i32.store8 (i32.add (local.get $offset) (i32.const 8)) (i32.const 95))   ;; '_'
  (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 9)))
  (struct.new $STRING (local.get $offset) (i32.const 9))
)


;; make_string_args: create "args" string for exception args attribute
(func $make_string_args (result (ref $STRING))
  (local $offset i32)
  (local.set $offset (global.get $string_heap))
  ;; "args" = 4 chars
  (i32.store8 (local.get $offset) (i32.const 97))   ;; 'a'
  (i32.store8 (i32.add (local.get $offset) (i32.const 1)) (i32.const 114))  ;; 'r'
  (i32.store8 (i32.add (local.get $offset) (i32.const 2)) (i32.const 103))  ;; 'g'
  (i32.store8 (i32.add (local.get $offset) (i32.const 3)) (i32.const 115))  ;; 's'
  (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 4)))
  (struct.new $STRING (local.get $offset) (i32.const 4))
)


;; make_string_matmul: create "__matmul__" string for matrix multiplication
(func $make_string_matmul (result (ref $STRING))
  (local $offset i32)
  (local.set $offset (global.get $string_heap))
  ;; "__matmul__" = 10 chars
  (i32.store8 (local.get $offset) (i32.const 95))   ;; '_'
  (i32.store8 (i32.add (local.get $offset) (i32.const 1)) (i32.const 95))   ;; '_'
  (i32.store8 (i32.add (local.get $offset) (i32.const 2)) (i32.const 109))  ;; 'm'
  (i32.store8 (i32.add (local.get $offset) (i32.const 3)) (i32.const 97))   ;; 'a'
  (i32.store8 (i32.add (local.get $offset) (i32.const 4)) (i32.const 116))  ;; 't'
  (i32.store8 (i32.add (local.get $offset) (i32.const 5)) (i32.const 109))  ;; 'm'
  (i32.store8 (i32.add (local.get $offset) (i32.const 6)) (i32.const 117))  ;; 'u'
  (i32.store8 (i32.add (local.get $offset) (i32.const 7)) (i32.const 108))  ;; 'l'
  (i32.store8 (i32.add (local.get $offset) (i32.const 8)) (i32.const 95))   ;; '_'
  (i32.store8 (i32.add (local.get $offset) (i32.const 9)) (i32.const 95))   ;; '_'
  (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 10)))
  (struct.new $STRING (local.get $offset) (i32.const 10))
)


;; make_string_rmatmul: create "__rmatmul__" string for reverse matrix multiplication
(func $make_string_rmatmul (result (ref $STRING))
  (local $offset i32)
  (local.set $offset (global.get $string_heap))
  ;; "__rmatmul__" = 11 chars
  (i32.store8 (local.get $offset) (i32.const 95))   ;; '_'
  (i32.store8 (i32.add (local.get $offset) (i32.const 1)) (i32.const 95))   ;; '_'
  (i32.store8 (i32.add (local.get $offset) (i32.const 2)) (i32.const 114))  ;; 'r'
  (i32.store8 (i32.add (local.get $offset) (i32.const 3)) (i32.const 109))  ;; 'm'
  (i32.store8 (i32.add (local.get $offset) (i32.const 4)) (i32.const 97))   ;; 'a'
  (i32.store8 (i32.add (local.get $offset) (i32.const 5)) (i32.const 116))  ;; 't'
  (i32.store8 (i32.add (local.get $offset) (i32.const 6)) (i32.const 109))  ;; 'm'
  (i32.store8 (i32.add (local.get $offset) (i32.const 7)) (i32.const 117))  ;; 'u'
  (i32.store8 (i32.add (local.get $offset) (i32.const 8)) (i32.const 108))  ;; 'l'
  (i32.store8 (i32.add (local.get $offset) (i32.const 9)) (i32.const 95))   ;; '_'
  (i32.store8 (i32.add (local.get $offset) (i32.const 10)) (i32.const 95))  ;; '_'
  (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 11)))
  (struct.new $STRING (local.get $offset) (i32.const 11))
)


;; Standard exception type name helpers
(func $make_value_error_str (result (ref $STRING))
  (local $offset i32)
  (local.set $offset (global.get $string_heap))
  ;; "ValueError" = 10 chars
  (i32.store8 (local.get $offset) (i32.const 86))  ;; 'V'
  (i32.store8 (i32.add (local.get $offset) (i32.const 1)) (i32.const 97))   ;; 'a'
  (i32.store8 (i32.add (local.get $offset) (i32.const 2)) (i32.const 108))  ;; 'l'
  (i32.store8 (i32.add (local.get $offset) (i32.const 3)) (i32.const 117))  ;; 'u'
  (i32.store8 (i32.add (local.get $offset) (i32.const 4)) (i32.const 101))  ;; 'e'
  (i32.store8 (i32.add (local.get $offset) (i32.const 5)) (i32.const 69))   ;; 'E'
  (i32.store8 (i32.add (local.get $offset) (i32.const 6)) (i32.const 114))  ;; 'r'
  (i32.store8 (i32.add (local.get $offset) (i32.const 7)) (i32.const 114))  ;; 'r'
  (i32.store8 (i32.add (local.get $offset) (i32.const 8)) (i32.const 111))  ;; 'o'
  (i32.store8 (i32.add (local.get $offset) (i32.const 9)) (i32.const 114))  ;; 'r'
  (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 10)))
  (struct.new $STRING (local.get $offset) (i32.const 10))
)


(func $make_type_error_str (result (ref $STRING))
  (local $offset i32)
  (local.set $offset (global.get $string_heap))
  ;; "TypeError" = 9 chars
  (i32.store8 (local.get $offset) (i32.const 84))  ;; 'T'
  (i32.store8 (i32.add (local.get $offset) (i32.const 1)) (i32.const 121))  ;; 'y'
  (i32.store8 (i32.add (local.get $offset) (i32.const 2)) (i32.const 112))  ;; 'p'
  (i32.store8 (i32.add (local.get $offset) (i32.const 3)) (i32.const 101))  ;; 'e'
  (i32.store8 (i32.add (local.get $offset) (i32.const 4)) (i32.const 69))   ;; 'E'
  (i32.store8 (i32.add (local.get $offset) (i32.const 5)) (i32.const 114))  ;; 'r'
  (i32.store8 (i32.add (local.get $offset) (i32.const 6)) (i32.const 114))  ;; 'r'
  (i32.store8 (i32.add (local.get $offset) (i32.const 7)) (i32.const 111))  ;; 'o'
  (i32.store8 (i32.add (local.get $offset) (i32.const 8)) (i32.const 114))  ;; 'r'
  (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 9)))
  (struct.new $STRING (local.get $offset) (i32.const 9))
)

"""
