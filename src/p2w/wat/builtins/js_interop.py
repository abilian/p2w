"""WAT builtin functions: JavaScript interop builtins."""

from __future__ import annotations

JS_LOG_CODE = """
;; js_log(value) - log value to browser console
(func $js_log (param $args (ref null eq)) (param $env (ref null $ENV)) (result (ref null eq))
  (local $val (ref null eq))
  (local $str (ref $STRING))
  ;; Get first argument
  (if (ref.is_null (local.get $args))
    (then (return (ref.null eq)))
  )
  (local.set $val (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))
  ;; Convert to string and log
  (local.set $str (call $value_to_string (local.get $val)))
  (call $js_console_log_str (local.get $str))
)
"""

JS_ALERT_CODE = """
;; js_alert(value) - show alert dialog in browser
(func $js_alert (param $args (ref null eq)) (param $env (ref null $ENV)) (result (ref null eq))
  (local $val (ref null eq))
  (local $str (ref $STRING))
  ;; Get first argument
  (if (ref.is_null (local.get $args))
    (then (return (ref.null eq)))
  )
  (local.set $val (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))
  ;; Convert to string and alert
  (local.set $str (call $value_to_string (local.get $val)))
  (call $js_alert_str (local.get $str))
)
"""

JS_GET_ELEMENT_CODE = """
;; js_get_element(id) - get DOM element by ID, return handle (i32 wrapped in i31)
(func $js_get_element (param $args (ref null eq)) (param $env (ref null $ENV)) (result (ref null eq))
  (local $id_val (ref null eq))
  (local $id_str (ref $STRING))
  (local $handle i32)
  ;; Get first argument (ID string)
  (if (ref.is_null (local.get $args))
    (then (return (ref.i31 (i32.const 0))))
  )
  (local.set $id_val (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))
  ;; Must be a string
  (if (i32.eqz (ref.test (ref $STRING) (local.get $id_val)))
    (then (return (ref.i31 (i32.const 0))))
  )
  (local.set $id_str (ref.cast (ref $STRING) (local.get $id_val)))
  ;; Get element handle via helper
  (local.set $handle (call $js_get_element_helper (local.get $id_str)))
  (ref.i31 (local.get $handle))
)
"""

JS_SET_TEXT_CODE = """
;; js_set_text(handle, text) - set text content of DOM element
(func $js_set_text (param $args (ref null eq)) (param $env (ref null $ENV)) (result (ref null eq))
  (local $handle_val (ref null eq))
  (local $text_val (ref null eq))
  (local $handle i32)
  (local $text_str (ref $STRING))
  (local $rest (ref null eq))
  ;; Get first argument (handle)
  (if (ref.is_null (local.get $args))
    (then (return (ref.null eq)))
  )
  (local.set $handle_val (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $args))))
  ;; Get second argument (text)
  (local.set $rest (struct.get $PAIR 1 (ref.cast (ref $PAIR) (local.get $args))))
  (if (ref.is_null (local.get $rest))
    (then (return (ref.null eq)))
  )
  (local.set $text_val (struct.get $PAIR 0 (ref.cast (ref $PAIR) (local.get $rest))))
  ;; Extract handle (i31)
  (if (i32.eqz (ref.test (ref i31) (local.get $handle_val)))
    (then (return (ref.null eq)))
  )
  (local.set $handle (i31.get_s (ref.cast (ref i31) (local.get $handle_val))))
  ;; Convert text to string
  (local.set $text_str (call $value_to_string (local.get $text_val)))
  ;; Set text content
  (call $js_set_element_text (local.get $handle) (local.get $text_str))
  (ref.null eq)
)
"""

# Combined code for this module
JS_INTEROP_CODE = JS_LOG_CODE + JS_ALERT_CODE + JS_GET_ELEMENT_CODE + JS_SET_TEXT_CODE
