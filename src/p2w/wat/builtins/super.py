"""WAT builtin functions: Super and inheritance support."""

from __future__ import annotations

SUPER_CODE = """
;; super() or super(self) - return a super proxy for parent method access
;; When called with just self, gets self.__class__.__base__
(func $super (param $args (ref null eq)) (param $env (ref null $ENV)) (result (ref null eq))
  (local $self (ref null eq))
  (local $obj_class (ref null $CLASS))
  (local $base_class (ref null $CLASS))
  ;; Get first argument (self)
  (if (ref.is_null (local.get $args))
    (then (return (ref.null eq)))
  )
  (local.set $self (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))
  ;; self must be OBJECT
  (if (i32.eqz (ref.test (ref $OBJECT) (local.get $self)))
    (then (return (ref.null eq)))
  )
  ;; Get self's class
  (local.set $obj_class (struct.get $OBJECT 0 (ref.cast (ref $OBJECT) (local.get $self))))
  ;; Get base class
  (local.set $base_class (struct.get $CLASS 2 (local.get $obj_class)))
  (if (ref.is_null (local.get $base_class))
    (then (return (ref.null eq)))
  )
  ;; Return SUPER proxy - cast to non-null refs
  (struct.new $SUPER
    (ref.cast (ref $CLASS) (local.get $base_class))
    (ref.cast (ref $OBJECT) (local.get $self))
  )
)

;; super(Class, self) - explicit form: get parent of class matching name
;; First arg is the class NAME (string), second is self
;; Walks self's class hierarchy to find the class with that name
(func $super_explicit (param $class_name (ref null eq)) (param $self (ref null eq)) (result (ref null eq))
  (local $current_class (ref null $CLASS))
  (local $base_class (ref null $CLASS))
  (local $target_name (ref $STRING))
  (local $class_name_str (ref $STRING))
  ;; class_name must be a STRING
  (if (i32.eqz (ref.test (ref $STRING) (local.get $class_name)))
    (then (return (ref.null eq)))
  )
  (local.set $target_name (ref.cast (ref $STRING) (local.get $class_name)))
  ;; self must be OBJECT
  (if (i32.eqz (ref.test (ref $OBJECT) (local.get $self)))
    (then (return (ref.null eq)))
  )
  ;; Start with self's class and walk up the hierarchy
  (local.set $current_class (struct.get $OBJECT 0 (ref.cast (ref $OBJECT) (local.get $self))))
  (block $found
    (loop $search
      (br_if $found (ref.is_null (local.get $current_class)))
      ;; Get this class's name
      (local.set $class_name_str (struct.get $CLASS 0 (ref.cast (ref $CLASS) (local.get $current_class))))
      ;; Compare names
      (if (call $string_equals (local.get $class_name_str) (local.get $target_name))
        (then
          ;; Found the class - get its parent
          (local.set $base_class (struct.get $CLASS 2 (ref.cast (ref $CLASS) (local.get $current_class))))
          (if (ref.is_null (local.get $base_class))
            (then (return (ref.null eq)))
          )
          ;; Return SUPER proxy with parent class and original self
          (return (struct.new $SUPER
            (ref.cast (ref $CLASS) (local.get $base_class))
            (ref.cast (ref $OBJECT) (local.get $self))
          ))
        )
      )
      ;; Move to parent class
      (local.set $current_class (struct.get $CLASS 2 (ref.cast (ref $CLASS) (local.get $current_class))))
      (br $search)
    )
  )
  ;; Class not found in hierarchy - return null
  (ref.null eq)
)
"""
