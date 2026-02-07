"""WAT helper functions: Generator support."""

from __future__ import annotations

GENERATORS_CODE = """

;; =============================================================================
;; Generator Support Functions
;; =============================================================================

;; generator_iter: return self (generators are their own iterators)
(func $generator_iter (param $gen (ref null eq)) (result (ref null eq))
  (local.get $gen)
)


;; generator_next: advance generator to next yield point
;; Calls the generator body function which handles state machine internally
(func $generator_next (param $gen (ref null eq)) (result (ref null eq))
  (local $g (ref $GENERATOR))
  (local $state i32)
  (local $func_idx i32)
  (local $result (ref null eq))

  ;; Cast to GENERATOR
  (local.set $g (ref.cast (ref $GENERATOR) (local.get $gen)))

  ;; Check if already exhausted BEFORE calling body
  (local.set $state (struct.get $GENERATOR $state (local.get $g)))
  (if (i32.eq (local.get $state) (i32.const -1))
    (then
      ;; Already exhausted, throw StopIteration
      (throw $StopIteration)
    )
  )

  ;; Call the generator body function via indirect call
  ;; The function takes the generator as its argument and updates state internally
  (local.set $func_idx (struct.get $GENERATOR $func_idx (local.get $g)))
  (local.set $result
    (call_indirect (type $FUNC)
      (local.get $gen)
      (struct.get $GENERATOR $env (local.get $g))
      (local.get $func_idx)))

  ;; Return the yielded value
  ;; (The body returns null and sets state=-1 when exhausted, which will
  ;; cause StopIteration on the NEXT call to generator_next)
  (local.get $result)
)


;; generator_send: send a value into the generator
;; Sets the sent_value field and resumes the generator
(func $generator_send (param $gen (ref null eq)) (param $value (ref null eq)) (result (ref null eq))
  (local $g (ref $GENERATOR))

  ;; Cast to GENERATOR
  (local.set $g (ref.cast (ref $GENERATOR) (local.get $gen)))

  ;; Store the sent value
  (struct.set $GENERATOR $sent_value (local.get $g) (local.get $value))

  ;; Resume the generator (generator_next will clear sent_value after use)
  (call $generator_next (local.get $gen))
)


;; generator_throw: throw an exception into the generator
;; For now, this just marks the generator as exhausted and throws the exception
(func $generator_throw (param $gen (ref null eq)) (param $exc (ref null eq)) (result (ref null eq))
  (local $g (ref $GENERATOR))
  (local $exc_str (ref null $STRING))

  ;; Cast to GENERATOR
  (local.set $g (ref.cast (ref $GENERATOR) (local.get $gen)))

  ;; Mark generator as exhausted
  (struct.set $GENERATOR $state (local.get $g) (i32.const -1))

  ;; Create and throw the exception
  ;; If exc is a string, use it as the exception type
  ;; Otherwise, use "GeneratorExit" as default
  (if (ref.test (ref $STRING) (local.get $exc))
    (then
      (local.set $exc_str (ref.cast (ref $STRING) (local.get $exc)))
    )
    (else
      (local.set $exc_str (call $make_generator_exit_str))
    )
  )

  (throw $PyException (struct.new $EXCEPTION
    (ref.cast (ref $STRING) (local.get $exc_str))
    (ref.null eq)
    (ref.null eq)
    (ref.null eq)
  ))
)


;; generator_close: close the generator gracefully
;; Marks the generator as exhausted, returns None
(func $generator_close (param $gen (ref null eq)) (result (ref null eq))
  (local $g (ref $GENERATOR))

  ;; Cast to GENERATOR
  (local.set $g (ref.cast (ref $GENERATOR) (local.get $gen)))

  ;; Mark generator as exhausted
  (struct.set $GENERATOR $state (local.get $g) (i32.const -1))

  ;; Return None
  (ref.null eq)
)


;; Make GeneratorExit string for throw()
(func $make_generator_exit_str (result (ref $STRING))
  (local $offset i32)
  (local.set $offset (global.get $string_heap))
  ;; "GeneratorExit" = 13 chars
  (i32.store8 (local.get $offset) (i32.const 71))  ;; 'G'
  (i32.store8 (i32.add (local.get $offset) (i32.const 1)) (i32.const 101))  ;; 'e'
  (i32.store8 (i32.add (local.get $offset) (i32.const 2)) (i32.const 110))  ;; 'n'
  (i32.store8 (i32.add (local.get $offset) (i32.const 3)) (i32.const 101))  ;; 'e'
  (i32.store8 (i32.add (local.get $offset) (i32.const 4)) (i32.const 114))  ;; 'r'
  (i32.store8 (i32.add (local.get $offset) (i32.const 5)) (i32.const 97))   ;; 'a'
  (i32.store8 (i32.add (local.get $offset) (i32.const 6)) (i32.const 116))  ;; 't'
  (i32.store8 (i32.add (local.get $offset) (i32.const 7)) (i32.const 111))  ;; 'o'
  (i32.store8 (i32.add (local.get $offset) (i32.const 8)) (i32.const 114))  ;; 'r'
  (i32.store8 (i32.add (local.get $offset) (i32.const 9)) (i32.const 69))   ;; 'E'
  (i32.store8 (i32.add (local.get $offset) (i32.const 10)) (i32.const 120)) ;; 'x'
  (i32.store8 (i32.add (local.get $offset) (i32.const 11)) (i32.const 105)) ;; 'i'
  (i32.store8 (i32.add (local.get $offset) (i32.const 12)) (i32.const 116)) ;; 't'
  (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 13)))
  (struct.new $STRING (local.get $offset) (i32.const 13))
)


;; method_close: close method with runtime type checking
;; If obj is a generator, use generator_close
;; If obj is an OBJECT, call its close() method
;; Otherwise, return None
(func $method_close (param $obj (ref null eq)) (result (ref null eq))
  (local $g (ref $GENERATOR))
  (local $method_name (ref $STRING))
  (local $offset i32)

  ;; Check if it's a generator
  (if (ref.test (ref $GENERATOR) (local.get $obj))
    (then
      ;; Generator: use generator_close
      (local.set $g (ref.cast (ref $GENERATOR) (local.get $obj)))
      (struct.set $GENERATOR $state (local.get $g) (i32.const -1))
      (return (ref.null eq))
    )
  )

  ;; Check if it's an OBJECT with a close method
  (if (ref.test (ref $OBJECT) (local.get $obj))
    (then
      ;; Create string "close" (5 chars)
      (local.set $offset (global.get $string_heap))
      (i32.store8 (local.get $offset) (i32.const 99))  ;; 'c'
      (i32.store8 (i32.add (local.get $offset) (i32.const 1)) (i32.const 108))  ;; 'l'
      (i32.store8 (i32.add (local.get $offset) (i32.const 2)) (i32.const 111))  ;; 'o'
      (i32.store8 (i32.add (local.get $offset) (i32.const 3)) (i32.const 115))  ;; 's'
      (i32.store8 (i32.add (local.get $offset) (i32.const 4)) (i32.const 101))  ;; 'e'
      (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 5)))
      (local.set $method_name (struct.new $STRING (local.get $offset) (i32.const 5)))

      ;; Call close(self) - args = (PAIR self null)
      (return (call $object_call_method
        (local.get $obj)
        (local.get $method_name)
        (struct.new $PAIR (local.get $obj) (ref.null eq))
        (ref.null $ENV)
      ))
    )
  )

  ;; Unknown type - return None
  (ref.null eq)
)


;; is_generator: check if value is a generator
(func $is_generator (param $v (ref null eq)) (result i32)
  (ref.test (ref $GENERATOR) (local.get $v))
)


;; generator_to_list: eagerly consume a generator into a PAIR chain list
(func $generator_to_list (param $gen (ref null eq)) (result (ref null eq))
  (local $result (ref null eq))
  (local $tail (ref null eq))
  (local $new_pair (ref null $PAIR))
  (local $value (ref null eq))

  (local.set $result (ref.null eq))

  (block $done
    (loop $loop
      ;; Try to get next value using try_table
      (block $stop_iter
        (try_table (result (ref null eq)) (catch $StopIteration $stop_iter)
          (call $generator_next (local.get $gen))
        )
        (local.set $value)

        ;; Create new pair with the value
        (local.set $new_pair (struct.new $PAIR (local.get $value) (ref.null eq)))

        ;; Append to result
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
        (br $loop)
      )
      ;; StopIteration caught - exit loop
      (br $done)
    )
  )

  ;; Return result (or empty list if nothing was yielded)
  (if (ref.is_null (local.get $result))
    (then (return (struct.new $EMPTY_LIST)))
  )
  (local.get $result)
)


;; Make StopIteration string for error messages
(func $make_stop_iteration_str (result (ref $STRING))
  (local $offset i32)
  (local.set $offset (global.get $string_heap))
  ;; "StopIteration" = 13 chars
  (i32.store8 (local.get $offset) (i32.const 83))  ;; 'S'
  (i32.store8 (i32.add (local.get $offset) (i32.const 1)) (i32.const 116))  ;; 't'
  (i32.store8 (i32.add (local.get $offset) (i32.const 2)) (i32.const 111))  ;; 'o'
  (i32.store8 (i32.add (local.get $offset) (i32.const 3)) (i32.const 112))  ;; 'p'
  (i32.store8 (i32.add (local.get $offset) (i32.const 4)) (i32.const 73))   ;; 'I'
  (i32.store8 (i32.add (local.get $offset) (i32.const 5)) (i32.const 116))  ;; 't'
  (i32.store8 (i32.add (local.get $offset) (i32.const 6)) (i32.const 101))  ;; 'e'
  (i32.store8 (i32.add (local.get $offset) (i32.const 7)) (i32.const 114))  ;; 'r'
  (i32.store8 (i32.add (local.get $offset) (i32.const 8)) (i32.const 97))   ;; 'a'
  (i32.store8 (i32.add (local.get $offset) (i32.const 9)) (i32.const 116))  ;; 't'
  (i32.store8 (i32.add (local.get $offset) (i32.const 10)) (i32.const 105)) ;; 'i'
  (i32.store8 (i32.add (local.get $offset) (i32.const 11)) (i32.const 111)) ;; 'o'
  (i32.store8 (i32.add (local.get $offset) (i32.const 12)) (i32.const 110)) ;; 'n'
  (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 13)))
  (struct.new $STRING (local.get $offset) (i32.const 13))
)

"""
