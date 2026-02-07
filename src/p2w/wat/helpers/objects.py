"""WAT helper functions: Object and class operations."""

from __future__ import annotations

OBJECTS_CODE = """

;; object_delitem: call __delitem__ on object
(func $object_delitem (param $obj (ref null eq)) (param $key (ref null eq)) (result (ref null eq))
  (local $method (ref null eq))
  (local $method_name (ref $STRING))
  (local $offset i32)
  (local $closure (ref null $CLOSURE))

  ;; Create "__delitem__" string
  (local.set $offset (global.get $string_heap))
  (i32.store8 (local.get $offset) (i32.const 95))  ;; _
  (i32.store8 (i32.add (local.get $offset) (i32.const 1)) (i32.const 95))  ;; _
  (i32.store8 (i32.add (local.get $offset) (i32.const 2)) (i32.const 100)) ;; d
  (i32.store8 (i32.add (local.get $offset) (i32.const 3)) (i32.const 101)) ;; e
  (i32.store8 (i32.add (local.get $offset) (i32.const 4)) (i32.const 108)) ;; l
  (i32.store8 (i32.add (local.get $offset) (i32.const 5)) (i32.const 105)) ;; i
  (i32.store8 (i32.add (local.get $offset) (i32.const 6)) (i32.const 116)) ;; t
  (i32.store8 (i32.add (local.get $offset) (i32.const 7)) (i32.const 101)) ;; e
  (i32.store8 (i32.add (local.get $offset) (i32.const 8)) (i32.const 109)) ;; m
  (i32.store8 (i32.add (local.get $offset) (i32.const 9)) (i32.const 95))  ;; _
  (i32.store8 (i32.add (local.get $offset) (i32.const 10)) (i32.const 95)) ;; _
  (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 11)))
  (local.set $method_name (struct.new $STRING (local.get $offset) (i32.const 11)))

  ;; Look up __delitem__ method
  (local.set $method (call $object_getattr (local.get $obj) (local.get $method_name)))

  ;; If method not found, just return the object
  (if (ref.is_null (local.get $method))
    (then (return (local.get $obj)))
  )

  ;; Call __delitem__(self, key)
  (local.set $closure (ref.cast (ref $CLOSURE) (local.get $method)))
  (drop (call_indirect (type $FUNC)
    (struct.new $PAIR (local.get $obj)
      (struct.new $PAIR (local.get $key) (ref.null eq)))
    (struct.get $CLOSURE 0 (local.get $closure))
    (struct.get $CLOSURE 1 (local.get $closure))
  ))

  ;; Return the object
  (local.get $obj)
)


;; class_to_string: convert CLASS to string "<class 'ClassName'>"
(func $class_to_string (param $cls (ref $CLASS)) (result (ref $STRING))
  (local $offset i32)
  (local $name (ref $STRING))
  (local $prefix (ref $STRING))
  (local $suffix (ref $STRING))
  (local $result (ref $STRING))

  (local.set $name (struct.get $CLASS 0 (local.get $cls)))

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

  ;; Create "'>" suffix (2 chars)
  (local.set $offset (global.get $string_heap))
  (i32.store8 (local.get $offset) (i32.const 39))   ;; '
  (i32.store8 (i32.add (local.get $offset) (i32.const 1)) (i32.const 62))   ;; >
  (global.set $string_heap (i32.add (global.get $string_heap) (i32.const 2)))
  (local.set $suffix (struct.new $STRING (local.get $offset) (i32.const 2)))

  ;; Concatenate: "<class '" + name + "'>"
  (local.set $result (call $string_concat (local.get $prefix) (local.get $name)))
  (call $string_concat (local.get $result) (local.get $suffix))
)


;; Polymorphic count method - dispatches based on runtime type
(func $method_count (param $obj (ref null eq)) (param $arg (ref null eq)) (result (ref null eq))
  ;; If it's a STRING, call $string_count
  (if (ref.test (ref $STRING) (local.get $obj))
    (then (return (call $string_count (local.get $obj) (local.get $arg))))
  )
  ;; Otherwise treat as list, call $list_count
  (call $list_count (local.get $obj) (local.get $arg))
)


;; Polymorphic pop with argument - for both list.pop(index) and dict.pop(key)
;; Returns the popped value
;; Polymorphic copy - dispatches to list_copy or dict_copy based on type
(func $method_copy (param $obj (ref null eq)) (result (ref null eq))
  ;; Check if obj is a $DICT wrapper
  (if (ref.test (ref $DICT) (local.get $obj))
    (then (return (call $dict_copy (local.get $obj))))
  )
  ;; Otherwise it's a list/set - use list_copy
  (call $list_copy (local.get $obj))
)


(func $method_pop_arg (param $obj (ref null eq)) (param $arg (ref null eq)) (result (ref null eq))
  (local $value (ref null eq))
  (local $updated (ref null eq))
  ;; Check if obj is a dict (wrapped in $DICT) or if arg is a STRING (heuristic)
  (if (i32.or (ref.test (ref $DICT) (local.get $obj)) (ref.test (ref $STRING) (local.get $arg)))
    (then
      ;; Call $dict_pop with null default - returns (value, updated_dict)
      (call $dict_pop (local.get $obj) (local.get $arg) (ref.null eq))
      (local.set $updated)
      (local.set $value)
      ;; Cache the updated dict for $method_pop_arg_update
      (global.set $tmp_pop_dict (local.get $updated))
      (return (local.get $value))
    )
  )
  ;; Otherwise treat as list.pop(index)
  (call $list_pop_at (local.get $obj) (local.get $arg))
)


;; Polymorphic pop with default - for dict.pop(key, default)
(func $method_pop_arg_default (param $obj (ref null eq)) (param $arg (ref null eq)) (param $default (ref null eq)) (result (ref null eq))
  (local $value (ref null eq))
  (local $updated (ref null eq))
  ;; Check if obj is a dict
  (if (i32.or (ref.test (ref $DICT) (local.get $obj)) (ref.test (ref $STRING) (local.get $arg)))
    (then
      ;; Call $dict_pop with provided default
      (call $dict_pop (local.get $obj) (local.get $arg) (local.get $default))
      (local.set $updated)
      (local.set $value)
      ;; Cache the updated dict for $method_pop_arg_update
      (global.set $tmp_pop_dict (local.get $updated))
      (return (local.get $value))
    )
  )
  ;; For lists, pop doesn't take a default - just ignore it
  (call $list_pop_at (local.get $obj) (local.get $arg))
)


;; Polymorphic pop update - returns the updated collection after pop
;; For lists, this handles the pop at index 0 case
;; For dicts, returns the cached updated dict from $method_pop_arg
(func $method_pop_arg_update (param $obj (ref null eq)) (param $arg (ref null eq)) (result (ref null eq))
  ;; If obj is a dict or arg is a STRING, return the cached updated dict
  (if (i32.or (ref.test (ref $DICT) (local.get $obj)) (ref.test (ref $STRING) (local.get $arg)))
    (then (return (global.get $tmp_pop_dict)))
  )
  ;; Otherwise treat as list.pop(index) - return updated list
  (call $list_pop_at_rest (local.get $obj) (local.get $arg))
)


;; =============================================================================
;; Object and Class Operations
;; =============================================================================

;; unwrap_self: extract real self from SUPER proxy or return object as-is
;; Used for method calls to ensure we pass the real self, not the super proxy
(func $unwrap_self (param $obj (ref null eq)) (result (ref null eq))
  ;; If SUPER, return the wrapped self
  (if (ref.test (ref $SUPER) (local.get $obj))
    (then
      (return (struct.get $SUPER 1 (ref.cast (ref $SUPER) (local.get $obj))))
    )
  )
  ;; Otherwise return as-is
  (local.get $obj)
)


;; maybe_call_property_getter: if value is a PROPERTY, call its getter with self
;; Otherwise return the value as-is
(func $maybe_call_property_getter
  (param $self (ref null eq))
  (param $value (ref null eq))
  (result (ref null eq))
  (local $prop (ref $PROPERTY))
  (local $getter (ref null $CLOSURE))
  (local $args (ref null eq))

  ;; Check if value is a PROPERTY
  (if (result (ref null eq))
    (ref.test (ref $PROPERTY) (local.get $value))
    (then
      ;; It's a property - call its getter with self
      (local.set $prop (ref.cast (ref $PROPERTY) (local.get $value)))
      (local.set $getter (struct.get $PROPERTY 0 (local.get $prop)))

      ;; If getter is null, return null
      (if (result (ref null eq))
        (ref.is_null (local.get $getter))
        (then (ref.null eq))
        (else
          ;; Build args: PAIR(self, null)
          (local.set $args (struct.new $PAIR
            (local.get $self)
            (ref.null eq)
          ))
          ;; Call the getter
          (call_indirect (type $FUNC)
            (local.get $args)
            (struct.get $CLOSURE 0 (ref.cast (ref $CLOSURE) (local.get $getter)))
            (struct.get $CLOSURE 1 (ref.cast (ref $CLOSURE) (local.get $getter)))
          )
        )
      )
    )
    (else
      ;; Not a property - return as-is
      (local.get $value)
    )
  )
)


;; maybe_call_property_setter: if attr is a PROPERTY, call its setter
;; Returns 1 if it was a property (setter called or no setter), 0 otherwise
(func $maybe_call_property_setter
  (param $self (ref null eq))
  (param $attr (ref null eq))
  (param $value (ref null eq))
  (result i32)
  (local $prop (ref $PROPERTY))
  (local $setter (ref null $CLOSURE))
  (local $args (ref null eq))

  ;; Check if attr is a PROPERTY
  (if (result i32)
    (ref.test (ref $PROPERTY) (local.get $attr))
    (then
      ;; It's a property - call its setter
      (local.set $prop (ref.cast (ref $PROPERTY) (local.get $attr)))
      (local.set $setter (struct.get $PROPERTY 1 (local.get $prop)))

      ;; If setter is null, raise AttributeError (property is read-only)
      (if (ref.is_null (local.get $setter))
        (then (call $throw_attribute_error (ref.null eq)))
        (else
          ;; Build args: PAIR(self, PAIR(value, null))
          (local.set $args (struct.new $PAIR
            (local.get $self)
            (struct.new $PAIR
              (local.get $value)
              (ref.null eq)
            )
          ))
          ;; Call the setter
          (drop (call_indirect (type $FUNC)
            (local.get $args)
            (struct.get $CLOSURE 0 (ref.cast (ref $CLOSURE) (local.get $setter)))
            (struct.get $CLOSURE 1 (ref.cast (ref $CLOSURE) (local.get $setter)))
          ))
        )
      )
      (i32.const 1)  ;; Was a property
    )
    (else
      ;; Not a property
      (i32.const 0)
    )
  )
)


;; object_getattr: get attribute value from object, class, or super proxy
;; Returns null if attribute not found
(func $object_getattr (param $obj (ref null eq)) (param $name (ref null eq)) (result (ref null eq))
  (local $attrs (ref null eq))
  (local $pair (ref null $PAIR))
  (local $kv (ref null $PAIR))

  ;; Check if obj is null - return null (handles super() on class with no parent)
  (if (ref.is_null (local.get $obj))
    (then (return (ref.null eq)))
  )

  ;; Check if obj is i31 (JS handle) - return the method NAME for call_method_dispatch
  ;; (JS methods are called dynamically, so we pass the name through)
  (if (ref.test (ref i31) (local.get $obj))
    (then
      (return (local.get $name))
    )
  )

  ;; Check if obj is a SUPER proxy - look up method in parent class
  (if (ref.test (ref $SUPER) (local.get $obj))
    (then
      ;; For SUPER, look up method in the parent class directly
      (return (call $class_lookup_method
        (struct.get $SUPER 0 (ref.cast (ref $SUPER) (local.get $obj)))
        (local.get $name)
      ))
    )
  )

  ;; Check if obj is an EXCEPTION - handle special attributes
  (if (ref.test (ref $EXCEPTION) (local.get $obj))
    (then
      ;; Check for __cause__ attribute
      (if (call $strings_equal
            (ref.cast (ref $STRING) (local.get $name))
            (call $make_string_cause))
        (then
          (return (struct.get $EXCEPTION $cause (ref.cast (ref $EXCEPTION) (local.get $obj))))
        )
      )
      ;; Check for args attribute (message wrapped in a tuple)
      (if (call $strings_equal
            (ref.cast (ref $STRING) (local.get $name))
            (call $make_string_args))
        (then
          ;; Return message wrapped in a single-element tuple to match Python's e.args
          (return (call $make_tuple_1 (struct.get $EXCEPTION $message (ref.cast (ref $EXCEPTION) (local.get $obj)))))
        )
      )
      ;; Not found
      (return (ref.null eq))
    )
  )

  ;; Check if obj is a CLASS - look up attribute in class dict directly
  (if (ref.test (ref $CLASS) (local.get $obj))
    (then
      (return (call $class_lookup_method
        (ref.cast (ref $CLASS) (local.get $obj))
        (local.get $name)
      ))
    )
  )

  ;; Check if obj is a slotted instance (INSTANCE_BASE but not OBJECT)
  ;; Slotted instances use struct fields instead of attribute dict
  (if (i32.and
        (ref.test (ref $INSTANCE_BASE) (local.get $obj))
        (i32.eqz (ref.test (ref $OBJECT) (local.get $obj))))
    (then
      ;; Call generated dispatch function for slotted attribute access
      (return (call $slotted_dispatch_getattr (local.get $obj) (local.get $name)))
    )
  )

  ;; Get attributes dict from object (instance)
  (local.set $attrs (struct.get $OBJECT $attrs (ref.cast (ref $OBJECT) (local.get $obj))))

  ;; Search for attribute by name (like dict_get)
  (block $not_found
    (loop $search
      (br_if $not_found (ref.is_null (local.get $attrs)))
      (local.set $pair (ref.cast (ref $PAIR) (local.get $attrs)))
      (local.set $kv (ref.cast (ref $PAIR) (struct.get $PAIR 0 (local.get $pair))))

      ;; Compare key (first element of kv pair)
      (if (call $strings_equal
            (ref.cast (ref $STRING) (struct.get $PAIR 0 (local.get $kv)))
            (ref.cast (ref $STRING) (local.get $name)))
        (then
          ;; Found - return value (second element of kv pair)
          (return (struct.get $PAIR 1 (local.get $kv)))
        )
      )

      ;; Move to next
      (local.set $attrs (struct.get $PAIR 1 (local.get $pair)))
      (br $search)
    )
  )

  ;; Not found in instance attrs, try class methods
  ;; Check if result is a PROPERTY - if so, call its getter with self
  (call $maybe_call_property_getter
    (local.get $obj)
    (call $class_lookup_method
      (struct.get $OBJECT $class (ref.cast (ref $OBJECT) (local.get $obj)))
      (local.get $name)
    )
  )
)


;; object_setattr: set attribute value on object or class
;; Returns the object (for chaining)
(func $object_setattr (param $obj (ref null eq)) (param $name (ref null eq)) (param $value (ref null eq)) (result (ref null eq))
  (local $attrs (ref null eq))
  (local $pair (ref null $PAIR))
  (local $kv (ref null $PAIR))
  (local $obj_ref (ref $OBJECT))
  (local $class_ref (ref $CLASS))

  ;; Check if obj is null
  (if (ref.is_null (local.get $obj))
    (then (call $throw_attribute_error (ref.null eq)))
  )

  ;; Check if obj is i31 (JS handle) - delegate to JS property setter
  (if (ref.test (ref i31) (local.get $obj))
    (then
      (return (call $js_set_property (local.get $obj) (local.get $name) (local.get $value)))
    )
  )

  ;; Check if obj is SUPER - cannot set attributes on super()
  (if (ref.test (ref $SUPER) (local.get $obj))
    (then (call $throw_attribute_error (ref.null eq)))
  )

  ;; Check if obj is a CLASS - set class attribute
  (if (ref.test (ref $CLASS) (local.get $obj))
    (then
      (local.set $class_ref (ref.cast (ref $CLASS) (local.get $obj)))
      (local.set $attrs (struct.get $CLASS $methods (local.get $class_ref)))

      ;; Search for existing class attribute
      (block $class_not_found
        (block $class_found
          (loop $class_search
            (br_if $class_not_found (ref.is_null (local.get $attrs)))
            (local.set $pair (ref.cast (ref $PAIR) (local.get $attrs)))
            (local.set $kv (ref.cast (ref $PAIR) (struct.get $PAIR 0 (local.get $pair))))

            (if (call $strings_equal
                  (ref.cast (ref $STRING) (struct.get $PAIR 0 (local.get $kv)))
                  (ref.cast (ref $STRING) (local.get $name)))
              (then
                ;; Found - update value in place
                (struct.set $PAIR 1 (local.get $kv) (local.get $value))
                (br $class_found)
              )
            )

            (local.set $attrs (struct.get $PAIR 1 (local.get $pair)))
            (br $class_search)
          )
        )
        ;; Found and updated
        (return (local.get $obj))
      )

      ;; Not found - add new class attribute at front
      (local.set $kv (struct.new $PAIR (local.get $name) (local.get $value)))
      (struct.set $CLASS $methods (local.get $class_ref)
        (struct.new $PAIR (local.get $kv) (struct.get $CLASS $methods (local.get $class_ref)))
      )
      (return (local.get $obj))
    )
  )

  ;; Check if obj is a slotted instance (INSTANCE_BASE but not OBJECT)
  ;; Slotted instances use struct fields instead of attribute dict
  (if (i32.and
        (ref.test (ref $INSTANCE_BASE) (local.get $obj))
        (i32.eqz (ref.test (ref $OBJECT) (local.get $obj))))
    (then
      ;; Call generated dispatch function for slotted attribute setting
      (return (call $slotted_dispatch_setattr (local.get $obj) (local.get $name) (local.get $value)))
    )
  )

  ;; Regular OBJECT
  (local.set $obj_ref (ref.cast (ref $OBJECT) (local.get $obj)))

  ;; First check if class has a PROPERTY for this attribute
  ;; If so, call the property setter instead of setting instance attr
  (if (call $maybe_call_property_setter
        (local.get $obj)
        (call $class_lookup_method
          (struct.get $OBJECT $class (local.get $obj_ref))
          (local.get $name)
        )
        (local.get $value)
      )
    (then
      ;; Property setter was called, return obj
      (return (local.get $obj))
    )
  )

  (local.set $attrs (struct.get $OBJECT $attrs (local.get $obj_ref)))

  ;; Search for existing attribute
  (block $not_found
    (block $found
      (loop $search
        (br_if $not_found (ref.is_null (local.get $attrs)))
        (local.set $pair (ref.cast (ref $PAIR) (local.get $attrs)))
        (local.set $kv (ref.cast (ref $PAIR) (struct.get $PAIR 0 (local.get $pair))))

        ;; Compare key
        (if (call $strings_equal
              (ref.cast (ref $STRING) (struct.get $PAIR 0 (local.get $kv)))
              (ref.cast (ref $STRING) (local.get $name)))
          (then
            ;; Found - update value in place
            (struct.set $PAIR 1 (local.get $kv) (local.get $value))
            (br $found)
          )
        )

        (local.set $attrs (struct.get $PAIR 1 (local.get $pair)))
        (br $search)
      )
    )
    ;; Found and updated, return object
    (return (local.get $obj))
  )

  ;; Not found - add new attribute at front
  ;; Create new key-value pair
  (local.set $kv (struct.new $PAIR (local.get $name) (local.get $value)))
  ;; Prepend to attrs list
  (struct.set $OBJECT $attrs (local.get $obj_ref)
    (struct.new $PAIR (local.get $kv) (struct.get $OBJECT $attrs (local.get $obj_ref)))
  )

  (local.get $obj)
)


;; object_delattr: delete attribute from object (or call property deleter)
;; Returns the object
(func $object_delattr (param $obj (ref null eq)) (param $name (ref null eq)) (result (ref null eq))
  (local $obj_ref (ref $OBJECT))
  (local $attrs (ref null eq))
  (local $prev (ref null $PAIR))
  (local $pair (ref null $PAIR))
  (local $kv (ref null $PAIR))
  (local $prop_attr (ref null eq))
  (local $prop (ref $PROPERTY))
  (local $deleter (ref null $CLOSURE))
  (local $args (ref null eq))

  ;; Check if obj is null or SUPER - cannot delete attributes on super()
  (if (ref.is_null (local.get $obj))
    (then (call $throw_attribute_error (ref.null eq)))
  )
  (if (ref.test (ref $SUPER) (local.get $obj))
    (then (call $throw_attribute_error (ref.null eq)))
  )

  ;; Only handle OBJECT
  (if (i32.eqz (ref.test (ref $OBJECT) (local.get $obj)))
    (then (return (local.get $obj)))
  )

  (local.set $obj_ref (ref.cast (ref $OBJECT) (local.get $obj)))

  ;; Check if class has a PROPERTY with a deleter for this attribute
  (local.set $prop_attr
    (call $class_lookup_method
      (struct.get $OBJECT $class (local.get $obj_ref))
      (local.get $name)
    )
  )

  (if (ref.test (ref $PROPERTY) (local.get $prop_attr))
    (then
      ;; It's a property - call its deleter
      (local.set $prop (ref.cast (ref $PROPERTY) (local.get $prop_attr)))
      (local.set $deleter (struct.get $PROPERTY 2 (local.get $prop)))

      (if (i32.eqz (ref.is_null (local.get $deleter)))
        (then
          ;; Build args: PAIR(self, null)
          (local.set $args (struct.new $PAIR
            (local.get $obj)
            (ref.null eq)
          ))
          ;; Call the deleter
          (drop (call_indirect (type $FUNC)
            (local.get $args)
            (struct.get $CLOSURE 0 (ref.cast (ref $CLOSURE) (local.get $deleter)))
            (struct.get $CLOSURE 1 (ref.cast (ref $CLOSURE) (local.get $deleter)))
          ))
        )
      )
      (return (local.get $obj))
    )
  )

  ;; Not a property - remove from instance attrs
  ;; Note: For simplicity, we just set the value to null rather than removing
  ;; the entry from the chain (proper deletion would require more complex list surgery)
  (local.set $attrs (struct.get $OBJECT $attrs (local.get $obj_ref)))

  (block $not_found
    (loop $search
      (br_if $not_found (ref.is_null (local.get $attrs)))
      (local.set $pair (ref.cast (ref $PAIR) (local.get $attrs)))
      (local.set $kv (ref.cast (ref $PAIR) (struct.get $PAIR 0 (local.get $pair))))

      (if (call $strings_equal
            (ref.cast (ref $STRING) (struct.get $PAIR 0 (local.get $kv)))
            (ref.cast (ref $STRING) (local.get $name)))
        (then
          ;; Found - set value to null (marks as deleted)
          (struct.set $PAIR 1 (local.get $kv) (ref.null eq))
          (return (local.get $obj))
        )
      )

      (local.set $attrs (struct.get $PAIR 1 (local.get $pair)))
      (br $search)
    )
  )

  (local.get $obj)
)


;; class_getmethod: get method from class, bound to self
;; Returns a closure with self captured, or null if not found
(func $class_getmethod (param $class (ref $CLASS)) (param $name (ref null eq)) (param $self (ref null eq)) (result (ref null eq))
  (local $methods (ref null eq))
  (local $pair (ref null $PAIR))
  (local $kv (ref null $PAIR))
  (local $method (ref null eq))

  (local.set $methods (struct.get $CLASS $methods (local.get $class)))

  ;; Search for method by name
  (block $not_found
    (loop $search
      (br_if $not_found (ref.is_null (local.get $methods)))
      (local.set $pair (ref.cast (ref $PAIR) (local.get $methods)))
      (local.set $kv (ref.cast (ref $PAIR) (struct.get $PAIR 0 (local.get $pair))))

      ;; Compare method name
      (if (call $strings_equal
            (ref.cast (ref $STRING) (struct.get $PAIR 0 (local.get $kv)))
            (ref.cast (ref $STRING) (local.get $name)))
        (then
          ;; Found method - create bound method (closure with self in env)
          (local.set $method (struct.get $PAIR 1 (local.get $kv)))
          ;; Return a new closure with self bound in environment
          (return
            (struct.new $CLOSURE
              (struct.new $ENV
                (struct.get $CLOSURE 0 (ref.cast (ref $CLOSURE) (local.get $method)))
                (struct.new $PAIR (local.get $self) (ref.null eq))
              )
              (struct.get $CLOSURE 1 (ref.cast (ref $CLOSURE) (local.get $method)))
            )
          )
        )
      )

      (local.set $methods (struct.get $PAIR 1 (local.get $pair)))
      (br $search)
    )
  )

  ;; Not found - return null
  (ref.null eq)
)


;; object_call_method: call a method on an object
;; This is a helper for obj.method(args) calls
(func $object_call_method (param $obj (ref null eq)) (param $name (ref null eq)) (param $args (ref null eq)) (param $env (ref null $ENV)) (result (ref null eq))
  (local $method (ref null eq))
  (local $closure (ref $CLOSURE))

  ;; Get the bound method
  (local.set $method (call $object_getattr (local.get $obj) (local.get $name)))

  (if (ref.is_null (local.get $method))
    (then (return (ref.null eq)))  ;; Method not found
  )

  ;; Call the method (it's a closure with self already bound)
  (local.set $closure (ref.cast (ref $CLOSURE) (local.get $method)))
  (call_indirect (type $FUNC)
    (local.get $args)
    (struct.get $CLOSURE 0 (local.get $closure))
    (struct.get $CLOSURE 1 (local.get $closure))
  )
)


;; instantiate_class: create a new instance of a class
;; Takes the class, init method name, args PAIR chain, env - returns the new object
(func $instantiate_class (param $class (ref $CLASS)) (param $init_name (ref null eq)) (param $args (ref null eq)) (param $env (ref null $ENV)) (result (ref null eq))
  (local $obj (ref $OBJECT))
  (local $init_method (ref null eq))
  (local $init_closure (ref $CLOSURE))
  (local $init_args (ref null eq))

  ;; Create new object with empty attrs
  (local.set $obj (struct.new $OBJECT
    (local.get $class)
    (ref.null eq)  ;; empty attrs
  ))

  ;; Look up __init__ method directly from class methods dict
  (local.set $init_method (call $class_lookup_method
    (local.get $class)
    (local.get $init_name)
  ))

  ;; If __init__ exists, call it with self prepended to args
  (if (ref.test (ref $CLOSURE) (local.get $init_method))
    (then
      (local.set $init_closure (ref.cast (ref $CLOSURE) (local.get $init_method)))
      ;; Prepend self to args: PAIR(self, args)
      (local.set $init_args (struct.new $PAIR
        (local.get $obj)
        (local.get $args)
      ))
      ;; Call __init__ with (self, *args)
      (drop (call_indirect (type $FUNC)
        (local.get $init_args)
        (struct.get $CLOSURE 0 (local.get $init_closure))
        (struct.get $CLOSURE 1 (local.get $init_closure))
      ))
    )
  )

  ;; Return the new object
  (local.get $obj)
)


;; call_or_instantiate: call a callable (CLOSURE or CLASS) with args
;; If callable is a CLASS, instantiate it and call __init__
;; If callable is a CLOSURE, call it directly
;; Takes: callable, init_name (string "__init__"), args
(func $call_or_instantiate (param $callable (ref null eq)) (param $init_name (ref null eq)) (param $args (ref null eq)) (param $env (ref null $ENV)) (result (ref null eq))
  (local $closure (ref $CLOSURE))

  ;; Check if callable is a CLASS
  (if (result (ref null eq))
    (ref.test (ref $CLASS) (local.get $callable))
    (then
      ;; Class instantiation
      (call $instantiate_class
        (ref.cast (ref $CLASS) (local.get $callable))
        (local.get $init_name)
        (local.get $args)
        (local.get $env)
      )
    )
    (else
      ;; Closure call
      (local.set $closure (ref.cast (ref $CLOSURE) (local.get $callable)))
      (call_indirect (type $FUNC)
        (local.get $args)
        (struct.get $CLOSURE 0 (local.get $closure))
        (struct.get $CLOSURE 1 (local.get $closure))
      )
    )
  )
)


;; class_lookup_method: look up method by name, searching inheritance chain
;; Returns the raw closure/value or null
(func $class_lookup_method (param $class (ref $CLASS)) (param $name (ref null eq)) (result (ref null eq))
  (local $current_class (ref null $CLASS))
  (local $methods (ref null eq))
  (local $pair (ref null $PAIR))
  (local $kv (ref null $PAIR))

  (local.set $current_class (local.get $class))

  ;; Search up the inheritance chain
  (block $not_found_anywhere
    (loop $class_loop
      (br_if $not_found_anywhere (ref.is_null (local.get $current_class)))

      ;; Search in current class's methods dict
      (local.set $methods (struct.get $CLASS $methods (local.get $current_class)))

      (block $not_in_this_class
        (loop $search
          (br_if $not_in_this_class (ref.is_null (local.get $methods)))
          (local.set $pair (ref.cast (ref $PAIR) (local.get $methods)))
          (local.set $kv (ref.cast (ref $PAIR) (struct.get $PAIR 0 (local.get $pair))))

          ;; Compare method name
          (if (call $strings_equal
                (ref.cast (ref $STRING) (struct.get $PAIR 0 (local.get $kv)))
                (ref.cast (ref $STRING) (local.get $name)))
            (then
              ;; Found method - return the raw closure/value
              (return (struct.get $PAIR 1 (local.get $kv)))
            )
          )

          (local.set $methods (struct.get $PAIR 1 (local.get $pair)))
          (br $search)
        )
      )

      ;; Not found in this class, try base class
      (local.set $current_class (struct.get $CLASS 2 (local.get $current_class)))
      (br $class_loop)
    )
  )

  ;; Not found anywhere in inheritance chain - return null
  (ref.null eq)
)


;; call_method_dispatch: call a method handling @staticmethod/@classmethod
;; Takes: object, method (possibly wrapped in STATICMETHOD/CLASSMETHOD), args (without self)
;; Returns the method call result
(func $call_method_dispatch
  (param $obj (ref null eq))
  (param $method (ref null eq))
  (param $args (ref null eq))
  (result (ref null eq))
  (local $closure (ref null $CLOSURE))
  (local $call_args (ref null eq))
  (local $class (ref null $CLASS))

  ;; Check if object is i31 (JS handle) - use JS method call
  (if (ref.test (ref i31) (local.get $obj))
    (then
      ;; method parameter contains the method name as STRING when object is JS handle
      (return (call $js_call_method (local.get $obj) (local.get $method) (local.get $args)))
    )
  )

  ;; Check if method is null
  (if (ref.is_null (local.get $method))
    (then (return (ref.null eq)))
  )

  ;; Check for @staticmethod wrapper - call WITHOUT self
  (if (ref.test (ref $STATICMETHOD) (local.get $method))
    (then
      ;; Unwrap the closure from STATICMETHOD (field 0)
      (local.set $closure
        (struct.get $STATICMETHOD 0 (ref.cast (ref $STATICMETHOD) (local.get $method))))
      ;; Call with args as-is (no self prepended)
      (return (call_indirect (type $FUNC)
        (local.get $args)
        (struct.get $CLOSURE 0 (ref.cast (ref $CLOSURE) (local.get $closure)))
        (struct.get $CLOSURE 1 (ref.cast (ref $CLOSURE) (local.get $closure)))
      ))
    )
  )

  ;; Check for @classmethod wrapper - prepend CLASS instead of self
  (if (ref.test (ref $CLASSMETHOD) (local.get $method))
    (then
      ;; Unwrap the closure from CLASSMETHOD (field 1, field 0 is tag)
      (local.set $closure
        (struct.get $CLASSMETHOD 1 (ref.cast (ref $CLASSMETHOD) (local.get $method))))
      ;; Get the class from the object
      (if (ref.test (ref $OBJECT) (local.get $obj))
        (then
          (local.set $class
            (struct.get $OBJECT $class (ref.cast (ref $OBJECT) (local.get $obj))))
        )
        (else
          ;; obj is already a CLASS
          (local.set $class (ref.cast (ref $CLASS) (local.get $obj)))
        )
      )
      ;; Prepend class to args: PAIR(class, args)
      (local.set $call_args (struct.new $PAIR
        (local.get $class)
        (local.get $args)
      ))
      ;; Call with (cls, *args)
      (return (call_indirect (type $FUNC)
        (local.get $call_args)
        (struct.get $CLOSURE 0 (ref.cast (ref $CLOSURE) (local.get $closure)))
        (struct.get $CLOSURE 1 (ref.cast (ref $CLOSURE) (local.get $closure)))
      ))
    )
  )

  ;; Regular method - prepend self to args
  (local.set $closure (ref.cast (ref $CLOSURE) (local.get $method)))
  ;; Unwrap self from SUPER if needed
  (local.set $call_args (struct.new $PAIR
    (call $unwrap_self (local.get $obj))
    (local.get $args)
  ))
  ;; Call with (self, *args)
  (call_indirect (type $FUNC)
    (local.get $call_args)
    (struct.get $CLOSURE 0 (ref.cast (ref $CLOSURE) (local.get $closure)))
    (struct.get $CLOSURE 1 (ref.cast (ref $CLOSURE) (local.get $closure)))
  )
)

"""
