"""WAT builtin functions: Type introspection (isinstance, type, getattr, etc.)."""

from __future__ import annotations

ISINSTANCE_CODE = """
;; isinstance_single: check if obj is an instance of a single type (cls)
;; Returns i32 (1 for true, 0 for false)
(func $isinstance_single (param $obj (ref null eq)) (param $cls (ref null eq)) (result i32)
  (local $obj_class (ref null $CLASS))
  (local $current (ref null $CLASS))
  (local $target (ref null $CLASS))
  (local $target_name (ref null $STRING))
  (local $func_idx i32)
  ;; Check if cls is a CLOSURE (builtin type like int, str, list)
  (if (ref.test (ref $CLOSURE) (local.get $cls))
    (then
      (local.set $func_idx (struct.get $CLOSURE 1 (ref.cast (ref $CLOSURE) (local.get $cls))))
      ;; int = 6: check if obj is i31 or INT64
      (if (i32.eq (local.get $func_idx) (i32.const 6))
        (then
          (if (ref.test (ref i31) (local.get $obj))
            (then (return (i32.const 1)))
          )
          (if (ref.test (ref $INT64) (local.get $obj))
            (then (return (i32.const 1)))
          )
          (return (i32.const 0))
        )
      )
      ;; bool = 7: check if obj is $BOOL
      (if (i32.eq (local.get $func_idx) (i32.const 7))
        (then
          (if (ref.test (ref $BOOL) (local.get $obj))
            (then (return (i32.const 1)))
          )
          (return (i32.const 0))
        )
      )
      ;; str = 8: check if obj is $STRING
      (if (i32.eq (local.get $func_idx) (i32.const 8))
        (then
          (if (ref.test (ref $STRING) (local.get $obj))
            (then (return (i32.const 1)))
          )
          (return (i32.const 0))
        )
      )
      ;; float = 11: check if obj is $FLOAT
      (if (i32.eq (local.get $func_idx) (i32.const 11))
        (then
          (if (ref.test (ref $FLOAT) (local.get $obj))
            (then (return (i32.const 1)))
          )
          (return (i32.const 0))
        )
      )
      ;; list = 13: check if obj is $PAIR, $EMPTY_LIST, or $LIST
      (if (i32.eq (local.get $func_idx) (i32.const 13))
        (then
          (if (ref.test (ref $PAIR) (local.get $obj))
            (then (return (i32.const 1)))
          )
          (if (ref.test (ref $EMPTY_LIST) (local.get $obj))
            (then (return (i32.const 1)))
          )
          (if (ref.test (ref $LIST) (local.get $obj))
            (then (return (i32.const 1)))
          )
          (return (i32.const 0))
        )
      )
      ;; dict = 18: check if obj is $DICT
      (if (i32.eq (local.get $func_idx) (i32.const 18))
        (then
          (if (ref.test (ref $DICT) (local.get $obj))
            (then (return (i32.const 1)))
          )
          (return (i32.const 0))
        )
      )
      ;; tuple = 19: check if obj is $TUPLE
      (if (i32.eq (local.get $func_idx) (i32.const 19))
        (then
          (if (ref.test (ref $TUPLE) (local.get $obj))
            (then (return (i32.const 1)))
          )
          (return (i32.const 0))
        )
      )
      ;; bytes = 30: check if obj is $BYTES
      (if (i32.eq (local.get $func_idx) (i32.const 30))
        (then
          (if (ref.test (ref $BYTES) (local.get $obj))
            (then (return (i32.const 1)))
          )
          (return (i32.const 0))
        )
      )
      ;; Unknown builtin - return False
      (return (i32.const 0))
    )
  )
  ;; cls must be CLASS
  (if (i32.eqz (ref.test (ref $CLASS) (local.get $cls)))
    (then (return (i32.const 0)))
  )
  (local.set $target (ref.cast (ref $CLASS) (local.get $cls)))
  ;; Check if target is "object" - all objects are instances of object
  (local.set $target_name (struct.get $CLASS 0 (local.get $target)))
  (if (i32.and
        (i32.eq (struct.get $STRING 1 (local.get $target_name)) (i32.const 0))
        (ref.is_null (struct.get $CLASS 2 (local.get $target))))
    (then
      ;; For object class, return True if obj is any instance (OBJECT or slotted)
      (if (ref.test (ref $INSTANCE_BASE) (local.get $obj))
        (then (return (i32.const 1)))
      )
      (return (i32.const 0))
    )
  )
  ;; obj must be an instance (OBJECT or slotted class instance)
  ;; $INSTANCE_BASE is the common base type for both
  (if (i32.eqz (ref.test (ref $INSTANCE_BASE) (local.get $obj)))
    (then (return (i32.const 0)))
  )
  ;; Get object's class via $INSTANCE_BASE (works for both OBJECT and slotted)
  (local.set $obj_class (struct.get $INSTANCE_BASE 0 (ref.cast (ref $INSTANCE_BASE) (local.get $obj))))
  (local.set $current (local.get $obj_class))
  ;; Walk up inheritance chain
  (block $done
    (loop $loop
      ;; Check if current equals target (same reference)
      (if (ref.eq (local.get $current) (local.get $target))
        (then (return (i32.const 1)))
      )
      ;; Move to base class
      (if (ref.is_null (struct.get $CLASS 2 (local.get $current)))
        (then (br $done))
      )
      (local.set $current (struct.get $CLASS 2 (local.get $current)))
      (br $loop)
    )
  )
  ;; Not found in inheritance chain
  (i32.const 0)
)

;; isinstance(obj, cls) - check if obj is an instance of cls (or tuple of classes)
(func $isinstance (param $args (ref null eq)) (param $env (ref null $ENV)) (result (ref null eq))
  (local $obj (ref null eq))
  (local $cls (ref null eq))
  (local $tuple_ref (ref $TUPLE))
  (local $data (ref $ARRAY_ANY))
  (local $len i32)
  (local $i i32)
  ;; Get both arguments
  (if (ref.is_null (local.get $args))
    (then (return (struct.new $BOOL (i32.const 0))))
  )
  (local.set $obj (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))
  (local.set $args (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $args))))
  (if (ref.is_null (local.get $args))
    (then (return (struct.new $BOOL (i32.const 0))))
  )
  (local.set $cls (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))
  ;; Check if cls is a TUPLE (tuple of types)
  (if (ref.test (ref $TUPLE) (local.get $cls))
    (then
      (local.set $tuple_ref (ref.cast (ref $TUPLE) (local.get $cls)))
      (local.set $data (struct.get $TUPLE $data (local.get $tuple_ref)))
      (local.set $len (struct.get $TUPLE $len (local.get $tuple_ref)))
      (local.set $i (i32.const 0))
      ;; Iterate through tuple elements and check each type
      (block $done
        (loop $loop
          (br_if $done (i32.ge_s (local.get $i) (local.get $len)))
          ;; Check if obj is instance of this type
          (if (call $isinstance_single (local.get $obj) (array.get $ARRAY_ANY (local.get $data) (local.get $i)))
            (then (return (struct.new $BOOL (i32.const 1))))
          )
          (local.set $i (i32.add (local.get $i) (i32.const 1)))
          (br $loop)
        )
      )
      ;; None of the types matched
      (return (struct.new $BOOL (i32.const 0)))
    )
  )
  ;; Single type - use helper function
  (struct.new $BOOL (call $isinstance_single (local.get $obj) (local.get $cls)))
)
"""

ISSUBCLASS_CODE = """
;; issubclass(cls, parent) - check if cls is a subclass of parent
(func $issubclass (param $args (ref null eq)) (param $env (ref null $ENV)) (result (ref null eq))
  (local $cls (ref null eq))
  (local $parent (ref null eq))
  (local $current (ref null $CLASS))
  (local $target (ref null $CLASS))
  (local $target_name (ref null $STRING))
  ;; Get both arguments
  (if (ref.is_null (local.get $args))
    (then (return (struct.new $BOOL (i32.const 0))))
  )
  (local.set $cls (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))
  (local.set $args (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $args))))
  (if (ref.is_null (local.get $args))
    (then (return (struct.new $BOOL (i32.const 0))))
  )
  (local.set $parent (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))
  ;; Both must be CLASS
  (if (i32.eqz (ref.test (ref $CLASS) (local.get $cls)))
    (then (return (struct.new $BOOL (i32.const 0))))
  )
  (if (i32.eqz (ref.test (ref $CLASS) (local.get $parent)))
    (then (return (struct.new $BOOL (i32.const 0))))
  )
  (local.set $current (ref.cast (ref $CLASS) (local.get $cls)))
  (local.set $target (ref.cast (ref $CLASS) (local.get $parent)))
  ;; Check if target is "object" (has empty name and null base)
  ;; In that case, all classes are subclasses of object
  (local.set $target_name (struct.get $CLASS 0 (local.get $target)))
  (if (i32.and
        (i32.eq (struct.get $STRING 1 (local.get $target_name)) (i32.const 0))
        (ref.is_null (struct.get $CLASS 2 (local.get $target))))
    (then (return (struct.new $BOOL (i32.const 1))))
  )
  ;; Walk up inheritance chain
  (block $done
    (loop $loop
      ;; Check if current equals target (same reference)
      (if (ref.eq (local.get $current) (local.get $target))
        (then (return (struct.new $BOOL (i32.const 1))))
      )
      ;; Move to base class
      (if (ref.is_null (struct.get $CLASS 2 (local.get $current)))
        (then (br $done))
      )
      (local.set $current (struct.get $CLASS 2 (local.get $current)))
      (br $loop)
    )
  )
  ;; Not found in inheritance chain
  (struct.new $BOOL (i32.const 0))
)
"""

CALLABLE_CODE = """
;; callable(obj) - check if obj is callable (function or class)
(func $callable (param $args (ref null eq)) (param $env (ref null $ENV)) (result (ref null eq))
  (local $obj (ref null eq))
  ;; Get argument
  (if (ref.is_null (local.get $args))
    (then (return (struct.new $BOOL (i32.const 0))))
  )
  (local.set $obj (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))
  ;; Check if CLOSURE (function)
  (if (ref.test (ref $CLOSURE) (local.get $obj))
    (then (return (struct.new $BOOL (i32.const 1))))
  )
  ;; Check if CLASS
  (if (ref.test (ref $CLASS) (local.get $obj))
    (then (return (struct.new $BOOL (i32.const 1))))
  )
  ;; Not callable
  (struct.new $BOOL (i32.const 0))
)
"""

HASATTR_CODE = """
;; hasattr(obj, name) - check if object has attribute
(func $hasattr (param $args (ref null eq)) (param $env (ref null $ENV)) (result (ref null eq))
  (local $obj (ref null eq))
  (local $name (ref null eq))
  (local $result (ref null eq))

  ;; Get arguments
  (if (ref.is_null (local.get $args))
    (then (return (struct.new $BOOL (i32.const 0))))
  )
  (if (i32.eqz (ref.test (ref $PAIR) (local.get $args)))
    (then (return (struct.new $BOOL (i32.const 0))))
  )
  (local.set $obj (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))
  (local.set $args (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $args))))

  (if (ref.is_null (local.get $args))
    (then (return (struct.new $BOOL (i32.const 0))))
  )
  (if (i32.eqz (ref.test (ref $PAIR) (local.get $args)))
    (then (return (struct.new $BOOL (i32.const 0))))
  )
  (local.set $name (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))

  ;; Try to get the attribute - if it returns null, attribute not found
  (local.set $result (call $object_getattr (local.get $obj) (local.get $name)))

  ;; If result is not null, attribute exists
  (if (i32.eqz (ref.is_null (local.get $result)))
    (then (return (struct.new $BOOL (i32.const 1))))
  )

  ;; Attribute not found
  (struct.new $BOOL (i32.const 0))
)
"""

GETATTR_CODE = """
;; getattr(obj, name[, default]) - get attribute with optional default
(func $getattr (param $args (ref null eq)) (param $env (ref null $ENV)) (result (ref null eq))
  (local $obj (ref null eq))
  (local $name (ref null eq))
  (local $default (ref null eq))
  (local $has_default i32)
  (local $result (ref null eq))

  ;; Get arguments
  (if (ref.is_null (local.get $args))
    (then (return (ref.null eq)))
  )
  (if (i32.eqz (ref.test (ref $PAIR) (local.get $args)))
    (then (return (ref.null eq)))
  )
  (local.set $obj (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))
  (local.set $args (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $args))))

  (if (ref.is_null (local.get $args))
    (then (return (ref.null eq)))
  )
  (if (i32.eqz (ref.test (ref $PAIR) (local.get $args)))
    (then (return (ref.null eq)))
  )
  (local.set $name (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))
  (local.set $args (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $args))))

  ;; Check for optional default argument
  (local.set $has_default (i32.const 0))
  (if (i32.and
        (i32.eqz (ref.is_null (local.get $args)))
        (ref.test (ref $PAIR) (local.get $args)))
    (then
      (local.set $default (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))
      (local.set $has_default (i32.const 1))
    )
  )

  ;; Get the attribute
  (local.set $result (call $object_getattr (local.get $obj) (local.get $name)))

  ;; If result is not null, return it
  (if (i32.eqz (ref.is_null (local.get $result)))
    (then (return (local.get $result)))
  )

  ;; If we have a default, return it
  (if (local.get $has_default)
    (then (return (local.get $default)))
  )

  ;; No default and attribute not found - return null
  (ref.null eq)
)
"""

SETATTR_CODE = """
;; setattr(obj, name, value) - set attribute
(func $setattr (param $args (ref null eq)) (param $env (ref null $ENV)) (result (ref null eq))
  (local $obj (ref null eq))
  (local $name (ref null eq))
  (local $value (ref null eq))

  ;; Get arguments
  (if (ref.is_null (local.get $args))
    (then (return (ref.null eq)))
  )
  (if (i32.eqz (ref.test (ref $PAIR) (local.get $args)))
    (then (return (ref.null eq)))
  )
  (local.set $obj (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))
  (local.set $args (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $args))))

  (if (ref.is_null (local.get $args))
    (then (return (ref.null eq)))
  )
  (if (i32.eqz (ref.test (ref $PAIR) (local.get $args)))
    (then (return (ref.null eq)))
  )
  (local.set $name (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))
  (local.set $args (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $args))))

  (if (ref.is_null (local.get $args))
    (then (return (ref.null eq)))
  )
  (if (i32.eqz (ref.test (ref $PAIR) (local.get $args)))
    (then (return (ref.null eq)))
  )
  (local.set $value (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))

  ;; Set the attribute
  (call $object_setattr (local.get $obj) (local.get $name) (local.get $value))
  (drop)

  ;; Return None
  (ref.null eq)
)
"""

TYPE_CODE = """
;; type(obj) - return the type of an object
;; Returns a CLOSURE for built-in types or CLASS for user-defined classes
(func $type (param $args (ref null eq)) (param $env (ref null $ENV)) (result (ref null eq))
  (local $obj (ref null eq))
  (local $builtins (ref null eq))
  ;; Get argument
  (if (ref.is_null (local.get $args))
    (then (return (ref.null eq)))
  )
  (local.set $obj (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))
  ;; Get builtins from env (env is the outer environment that contains builtins)
  (local.set $builtins (local.get $env))
  ;; For OBJECT, return its class
  (if (ref.test (ref $OBJECT) (local.get $obj))
    (then
      (return (struct.get $OBJECT $class (ref.cast (ref $OBJECT) (local.get $obj))))
    )
  )
  ;; For i31 (int), return int CLOSURE (index 6 in builtins, 0-indexed from end)
  (if (ref.test (ref i31) (local.get $obj))
    (then
      (return (struct.new $CLOSURE (ref.null $ENV) (i32.const 6)))
    )
  )
  ;; For INT64 (big int), also return int
  (if (ref.test (ref $INT64) (local.get $obj))
    (then
      (return (struct.new $CLOSURE (ref.null $ENV) (i32.const 6)))
    )
  )
  ;; For BOOL, return bool CLOSURE (index 7)
  (if (ref.test (ref $BOOL) (local.get $obj))
    (then
      (return (struct.new $CLOSURE (ref.null $ENV) (i32.const 7)))
    )
  )
  ;; For STRING, return str CLOSURE (index 8)
  (if (ref.test (ref $STRING) (local.get $obj))
    (then
      (return (struct.new $CLOSURE (ref.null $ENV) (i32.const 8)))
    )
  )
  ;; For FLOAT, return float CLOSURE (index 11)
  (if (ref.test (ref $FLOAT) (local.get $obj))
    (then
      (return (struct.new $CLOSURE (ref.null $ENV) (i32.const 11)))
    )
  )
  ;; For PAIR, EMPTY_LIST, or LIST, return list CLOSURE (index 13)
  (if (ref.test (ref $PAIR) (local.get $obj))
    (then
      (return (struct.new $CLOSURE (ref.null $ENV) (i32.const 13)))
    )
  )
  (if (ref.test (ref $EMPTY_LIST) (local.get $obj))
    (then
      (return (struct.new $CLOSURE (ref.null $ENV) (i32.const 13)))
    )
  )
  (if (ref.test (ref $LIST) (local.get $obj))
    (then
      (return (struct.new $CLOSURE (ref.null $ENV) (i32.const 13)))
    )
  )
  ;; For DICT, return dict CLOSURE (index 18)
  (if (ref.test (ref $DICT) (local.get $obj))
    (then
      (return (struct.new $CLOSURE (ref.null $ENV) (i32.const 18)))
    )
  )
  ;; For TUPLE, return tuple CLOSURE (index 19)
  (if (ref.test (ref $TUPLE) (local.get $obj))
    (then
      (return (struct.new $CLOSURE (ref.null $ENV) (i32.const 19)))
    )
  )
  ;; For BYTES, return bytes CLOSURE (index 30)
  (if (ref.test (ref $BYTES) (local.get $obj))
    (then
      (return (struct.new $CLOSURE (ref.null $ENV) (i32.const 30)))
    )
  )
  ;; For CLOSURE (function), return a function type marker
  (if (ref.test (ref $CLOSURE) (local.get $obj))
    (then
      ;; Return self - functions are their own type
      (return (local.get $obj))
    )
  )
  ;; For CLASS, return itself (type of a class is the class)
  (if (ref.test (ref $CLASS) (local.get $obj))
    (then
      (return (local.get $obj))
    )
  )
  ;; For None (null), return NoneType (we'll use None itself)
  (if (ref.is_null (local.get $obj))
    (then
      (return (ref.null eq))
    )
  )
  ;; Unknown type, return None
  (ref.null eq)
)
"""

DELATTR_CODE = """
;; delattr(obj, name) - delete attribute
(func $delattr (param $args (ref null eq)) (param $env (ref null $ENV)) (result (ref null eq))
  (local $obj (ref null eq))
  (local $name (ref null eq))

  ;; Get arguments
  (if (ref.is_null (local.get $args))
    (then (return (ref.null eq)))
  )
  (if (i32.eqz (ref.test (ref $PAIR) (local.get $args)))
    (then (return (ref.null eq)))
  )
  (local.set $obj (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))
  (local.set $args (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $args))))

  (if (ref.is_null (local.get $args))
    (then (return (ref.null eq)))
  )
  (if (i32.eqz (ref.test (ref $PAIR) (local.get $args)))
    (then (return (ref.null eq)))
  )
  (local.set $name (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))

  ;; Delete the attribute
  (call $object_delattr (local.get $obj) (local.get $name))
  (drop)

  ;; Return None
  (ref.null eq)
)
"""

ID_CODE = """
;; id(obj) - return identity (address/hash) of object
;; In WASM GC we don't have direct memory addresses, so we use a counter
(global $id_counter (mut i32) (i32.const 1000))

(func $id (param $args (ref null eq)) (param $env (ref null $ENV)) (result (ref null eq))
  (local $obj (ref null eq))
  ;; Get argument
  (if (ref.is_null (local.get $args))
    (then (return (ref.i31 (i32.const 0))))
  )
  (local.set $obj (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))
  ;; For null, return 0
  (if (ref.is_null (local.get $obj))
    (then (return (ref.i31 (i32.const 0))))
  )
  ;; For singletons, return fixed values
  (if (ref.eq (local.get $obj) (global.get $TRUE))
    (then (return (ref.i31 (i32.const 1))))
  )
  (if (ref.eq (local.get $obj) (global.get $FALSE))
    (then (return (ref.i31 (i32.const 2))))
  )
  ;; For integers, use the value itself (i31 are value types)
  (if (ref.test (ref i31) (local.get $obj))
    (then (return (ref.i31 (i32.add (i32.const 100) (i31.get_s (ref.cast (ref i31) (local.get $obj)))))))
  )
  ;; For other objects, return incrementing ID (not deterministic, but works)
  (global.set $id_counter (i32.add (global.get $id_counter) (i32.const 1)))
  (ref.i31 (global.get $id_counter))
)
"""

# Combined code for this module
INTROSPECTION_CODE = (
    ISINSTANCE_CODE
    + ISSUBCLASS_CODE
    + CALLABLE_CODE
    + HASATTR_CODE
    + GETATTR_CODE
    + SETATTR_CODE
    + TYPE_CODE
    + DELATTR_CODE
    + ID_CODE
)
