"""WAT helper functions: JavaScript interop functions."""

from __future__ import annotations

JS_INTEROP_CODE = """

;; Globals
(global $callback_table (mut (ref null $ARRAY_ANY)) (ref.null $ARRAY_ANY))
(global $callback_count (mut i32) (i32.const 0))


;; ============================================================================
;; JavaScript Interop Helpers
;; ============================================================================

;; js_console_log_str: log a string to console (wrapper for $js_console_log_import)
(func $js_console_log_str (param $s (ref $STRING)) (result (ref null eq))
  (call $js_console_log_import
    (struct.get $STRING 0 (local.get $s))
    (struct.get $STRING 1 (local.get $s)))
  (ref.null eq)
)


;; js_console_log_value: log any value to console (converts to string first)
(func $js_console_log_value (param $v (ref null eq)) (result (ref null eq))
  (local $s (ref $STRING))
  (local.set $s (call $value_to_string (local.get $v)))
  (call $js_console_log_str (local.get $s))
)


;; js_alert_str: show alert with string
(func $js_alert_str (param $s (ref $STRING)) (result (ref null eq))
  (call $js_alert_import
    (struct.get $STRING 0 (local.get $s))
    (struct.get $STRING 1 (local.get $s)))
  (ref.null eq)
)


;; js_alert_value: show alert with any value
(func $js_alert_value (param $v (ref null eq)) (result (ref null eq))
  (local $s (ref $STRING))
  (local.set $s (call $value_to_string (local.get $v)))
  (call $js_alert_str (local.get $s))
)


;; js_get_element_helper: get DOM element by ID string, return handle
(func $js_get_element_helper (param $id (ref $STRING)) (result i32)
  (call $js_get_element_by_id_import
    (struct.get $STRING 0 (local.get $id))
    (struct.get $STRING 1 (local.get $id)))
)


;; js_set_element_text: set text content of DOM element
(func $js_set_element_text (param $handle i32) (param $text (ref $STRING))
  (call $js_set_text_content_import
    (local.get $handle)
    (struct.get $STRING 0 (local.get $text))
    (struct.get $STRING 1 (local.get $text)))
)


;; js_set_element_html: set innerHTML of DOM element
(func $js_set_element_html (param $handle i32) (param $html (ref $STRING))
  (call $js_set_inner_html_import
    (local.get $handle)
    (struct.get $STRING 0 (local.get $html))
    (struct.get $STRING 1 (local.get $html)))
)


;; ============================================================================
;; JavaScript Interop - Document Methods
;; ============================================================================

;; js_document_get_element_by_id: document.getElementById(id) - takes string value, returns handle as i31
(func $js_document_get_element_by_id (param $id (ref null eq)) (result (ref null eq))
  (local $handle i32)
  (local $str (ref null $STRING))
  ;; Convert to string
  (if (ref.test (ref $STRING) (local.get $id))
    (then
      (local.set $str (ref.cast (ref $STRING) (local.get $id)))
    )
    (else
      (local.set $str (call $value_to_string (local.get $id)))
    )
  )
  ;; Call import with string
  (local.set $handle (call $js_get_element_by_id_import
    (struct.get $STRING 0 (ref.cast (ref $STRING) (local.get $str)))
    (struct.get $STRING 1 (ref.cast (ref $STRING) (local.get $str)))))
  ;; Return handle as i31
  (ref.i31 (local.get $handle))
)


;; js_document_create_element: document.createElement(tag) - returns handle as i31
(func $js_document_create_element (param $tag (ref null eq)) (result (ref null eq))
  (local $str (ref null $STRING))
  (local $handle i32)
  ;; Convert to string
  (if (ref.test (ref $STRING) (local.get $tag))
    (then
      (local.set $str (ref.cast (ref $STRING) (local.get $tag)))
    )
    (else
      (local.set $str (call $value_to_string (local.get $tag)))
    )
  )
  ;; Call import
  (local.set $handle (call $js_create_element_import
    (struct.get $STRING 0 (ref.cast (ref $STRING) (local.get $str)))
    (struct.get $STRING 1 (ref.cast (ref $STRING) (local.get $str)))))
  ;; Return handle as i31
  (ref.i31 (local.get $handle))
)


;; ============================================================================
;; JavaScript Interop - Element Methods
;; ============================================================================

;; js_element_append_child: element.appendChild(child)
(func $js_element_append_child (param $parent (ref null eq)) (param $child (ref null eq)) (result (ref null eq))
  (local $parent_handle i32)
  (local $child_handle i32)
  ;; Extract handles
  (local.set $parent_handle (i31.get_s (ref.cast (ref i31) (local.get $parent))))
  (local.set $child_handle (i31.get_s (ref.cast (ref i31) (local.get $child))))
  ;; Call import
  (call $js_append_child_import (local.get $parent_handle) (local.get $child_handle))
  ;; Return child (like DOM appendChild)
  (local.get $child)
)


;; js_canvas_get_context: canvas.getContext(type) - returns context handle as i31
(func $js_canvas_get_context (param $canvas (ref null eq)) (param $context_type (ref null eq)) (result (ref null eq))
  (local $canvas_handle i32)
  (local $str (ref null $STRING))
  (local $ctx_handle i32)
  ;; Extract canvas handle
  (local.set $canvas_handle (i31.get_s (ref.cast (ref i31) (local.get $canvas))))
  ;; Convert context type to string
  (if (ref.test (ref $STRING) (local.get $context_type))
    (then
      (local.set $str (ref.cast (ref $STRING) (local.get $context_type)))
    )
    (else
      (local.set $str (call $value_to_string (local.get $context_type)))
    )
  )
  ;; Call import
  (local.set $ctx_handle (call $js_get_context_import
    (local.get $canvas_handle)
    (struct.get $STRING 0 (ref.cast (ref $STRING) (local.get $str)))
    (struct.get $STRING 1 (ref.cast (ref $STRING) (local.get $str)))))
  ;; Return handle as i31
  (ref.i31 (local.get $ctx_handle))
)


;; js_canvas_fill_rect: ctx.fillRect(x, y, w, h)
(func $js_canvas_fill_rect (param $ctx (ref null eq)) (param $x (ref null eq)) (param $y (ref null eq)) (param $w (ref null eq)) (param $h (ref null eq)) (result (ref null eq))
  (local $handle i32)
  (local.set $handle (i31.get_s (ref.cast (ref i31) (local.get $ctx))))
  (call $js_canvas_fill_rect_import
    (local.get $handle)
    (call $to_f64 (local.get $x))
    (call $to_f64 (local.get $y))
    (call $to_f64 (local.get $w))
    (call $to_f64 (local.get $h)))
  (ref.null eq)
)


;; js_canvas_fill_text: ctx.fillText(text, x, y)
(func $js_canvas_fill_text (param $ctx (ref null eq)) (param $text (ref null eq)) (param $x (ref null eq)) (param $y (ref null eq)) (result (ref null eq))
  (local $handle i32)
  (local $str (ref null $STRING))
  (local.set $handle (i31.get_s (ref.cast (ref i31) (local.get $ctx))))
  (local.set $str (call $value_to_string (local.get $text)))
  (call $js_canvas_fill_text_import
    (local.get $handle)
    (struct.get $STRING 0 (ref.cast (ref $STRING) (local.get $str)))
    (struct.get $STRING 1 (ref.cast (ref $STRING) (local.get $str)))
    (call $to_f64 (local.get $x))
    (call $to_f64 (local.get $y)))
  (ref.null eq)
)


;; js_canvas_begin_path: ctx.beginPath()
(func $js_canvas_begin_path (param $ctx (ref null eq)) (result (ref null eq))
  (local $handle i32)
  (local.set $handle (i31.get_s (ref.cast (ref i31) (local.get $ctx))))
  (call $js_canvas_begin_path_import (local.get $handle))
  (ref.null eq)
)


;; js_canvas_move_to: ctx.moveTo(x, y)
(func $js_canvas_move_to (param $ctx (ref null eq)) (param $x (ref null eq)) (param $y (ref null eq)) (result (ref null eq))
  (local $handle i32)
  (local.set $handle (i31.get_s (ref.cast (ref i31) (local.get $ctx))))
  (call $js_canvas_move_to_import
    (local.get $handle)
    (call $to_f64 (local.get $x))
    (call $to_f64 (local.get $y)))
  (ref.null eq)
)


;; js_canvas_line_to: ctx.lineTo(x, y)
(func $js_canvas_line_to (param $ctx (ref null eq)) (param $x (ref null eq)) (param $y (ref null eq)) (result (ref null eq))
  (local $handle i32)
  (local.set $handle (i31.get_s (ref.cast (ref i31) (local.get $ctx))))
  (call $js_canvas_line_to_import
    (local.get $handle)
    (call $to_f64 (local.get $x))
    (call $to_f64 (local.get $y)))
  (ref.null eq)
)


;; js_canvas_stroke: ctx.stroke()
(func $js_canvas_stroke (param $ctx (ref null eq)) (result (ref null eq))
  (local $handle i32)
  (local.set $handle (i31.get_s (ref.cast (ref i31) (local.get $ctx))))
  (call $js_canvas_stroke_import (local.get $handle))
  (ref.null eq)
)


;; js_canvas_set_fill_style: ctx.fillStyle = value
(func $js_canvas_set_fill_style (param $ctx (ref null eq)) (param $value (ref null eq)) (result (ref null eq))
  (local $handle i32)
  (local $str (ref null $STRING))
  (local.set $handle (i31.get_s (ref.cast (ref i31) (local.get $ctx))))
  (local.set $str (call $value_to_string (local.get $value)))
  (call $js_canvas_set_fill_style_import
    (local.get $handle)
    (struct.get $STRING 0 (ref.cast (ref $STRING) (local.get $str)))
    (struct.get $STRING 1 (ref.cast (ref $STRING) (local.get $str))))
  (ref.null eq)
)


;; js_canvas_set_stroke_style: ctx.strokeStyle = value
(func $js_canvas_set_stroke_style (param $ctx (ref null eq)) (param $value (ref null eq)) (result (ref null eq))
  (local $handle i32)
  (local $str (ref null $STRING))
  (local.set $handle (i31.get_s (ref.cast (ref i31) (local.get $ctx))))
  (local.set $str (call $value_to_string (local.get $value)))
  (call $js_canvas_set_stroke_style_import
    (local.get $handle)
    (struct.get $STRING 0 (ref.cast (ref $STRING) (local.get $str)))
    (struct.get $STRING 1 (ref.cast (ref $STRING) (local.get $str))))
  (ref.null eq)
)


;; js_canvas_set_line_width: ctx.lineWidth = value
(func $js_canvas_set_line_width (param $ctx (ref null eq)) (param $value (ref null eq)) (result (ref null eq))
  (local $handle i32)
  (local.set $handle (i31.get_s (ref.cast (ref i31) (local.get $ctx))))
  (call $js_canvas_set_line_width_import
    (local.get $handle)
    (call $to_f64 (local.get $value)))
  (ref.null eq)
)


;; js_canvas_set_font: ctx.font = value
(func $js_canvas_set_font (param $ctx (ref null eq)) (param $value (ref null eq)) (result (ref null eq))
  (local $handle i32)
  (local $str (ref null $STRING))
  (local.set $handle (i31.get_s (ref.cast (ref i31) (local.get $ctx))))
  (local.set $str (call $value_to_string (local.get $value)))
  (call $js_canvas_set_font_import
    (local.get $handle)
    (struct.get $STRING 0 (ref.cast (ref $STRING) (local.get $str)))
    (struct.get $STRING 1 (ref.cast (ref $STRING) (local.get $str))))
  (ref.null eq)
)


;; init_callback_table: initialize the callback table (called at startup)
(func $init_callback_table
  (global.set $callback_table (array.new_default $ARRAY_ANY (i32.const 256)))
)


;; register_callback: store a closure and return its index
(func $register_callback (param $handler (ref null eq)) (result i32)
  (local $idx i32)
  (local $table (ref $ARRAY_ANY))
  ;; Initialize table if needed
  (if (ref.is_null (global.get $callback_table))
    (then (call $init_callback_table))
  )
  (local.set $table (ref.cast (ref $ARRAY_ANY) (global.get $callback_table)))
  ;; Get current index and increment
  (local.set $idx (global.get $callback_count))
  (global.set $callback_count (i32.add (local.get $idx) (i32.const 1)))
  ;; Store the closure
  (array.set $ARRAY_ANY (local.get $table) (local.get $idx) (local.get $handler))
  ;; Return the index
  (local.get $idx)
)


;; get_callback: retrieve a closure by index
(func $get_callback (param $idx i32) (result (ref null eq))
  (local $table (ref $ARRAY_ANY))
  (if (ref.is_null (global.get $callback_table))
    (then (return (ref.null eq)))
  )
  (local.set $table (ref.cast (ref $ARRAY_ANY) (global.get $callback_table)))
  (if (i32.ge_u (local.get $idx) (global.get $callback_count))
    (then (return (ref.null eq)))
  )
  (array.get $ARRAY_ANY (local.get $table) (local.get $idx))
)


;; js_element_add_event_listener: element.addEventListener(type, handler)
(func $js_element_add_event_listener (param $element (ref null eq)) (param $event_type (ref null eq)) (param $handler (ref null eq)) (result (ref null eq))
  (local $elem_handle i32)
  (local $type_str (ref null $STRING))
  (local $callback_idx i32)
  ;; Extract element handle
  (local.set $elem_handle (i31.get_s (ref.cast (ref i31) (local.get $element))))
  ;; Convert event type to string
  (if (ref.test (ref $STRING) (local.get $event_type))
    (then
      (local.set $type_str (ref.cast (ref $STRING) (local.get $event_type)))
    )
    (else
      (local.set $type_str (call $value_to_string (local.get $event_type)))
    )
  )
  ;; Register the full closure (not just func index) in callback table
  (local.set $callback_idx (call $register_callback (local.get $handler)))
  ;; Call import with callback table index
  (call $js_add_event_listener_import
    (local.get $elem_handle)
    (struct.get $STRING 0 (ref.cast (ref $STRING) (local.get $type_str)))
    (struct.get $STRING 1 (ref.cast (ref $STRING) (local.get $type_str)))
    (local.get $callback_idx))
  ;; Return None
  (ref.null eq)
)


;; js_event_prevent_default: event.preventDefault()
(func $js_event_prevent_default (param $event (ref null eq)) (result (ref null eq))
  (local $event_handle i32)
  ;; Extract event handle
  (local.set $event_handle (i31.get_s (ref.cast (ref i31) (local.get $event))))
  ;; Call import
  (call $js_prevent_default_import (local.get $event_handle))
  ;; Return None
  (ref.null eq)
)


;; ============================================================================
;; JavaScript Interop - Property Access
;; ============================================================================

;; js_get_property: get property from JS object
(func $js_get_property (param $obj (ref null eq)) (param $prop_name (ref null eq)) (result (ref null eq))
  (local $obj_handle i32)
  (local $prop_str (ref null $STRING))
  (local $result_offset i32)
  (local $result_len i32)
  ;; Extract object handle
  (local.set $obj_handle (i31.get_s (ref.cast (ref i31) (local.get $obj))))
  ;; Convert property name to string
  (if (ref.test (ref $STRING) (local.get $prop_name))
    (then
      (local.set $prop_str (ref.cast (ref $STRING) (local.get $prop_name)))
    )
    (else
      (local.set $prop_str (call $value_to_string (local.get $prop_name)))
    )
  )
  ;; Call import - returns offset to string heap where result is stored
  (local.set $result_offset (global.get $string_heap))
  (local.set $result_len (call $js_get_property_import
    (local.get $obj_handle)
    (struct.get $STRING 0 (ref.cast (ref $STRING) (local.get $prop_str)))
    (struct.get $STRING 1 (ref.cast (ref $STRING) (local.get $prop_str)))
    (local.get $result_offset)))
  ;; Update string heap
  (global.set $string_heap (i32.add (global.get $string_heap) (local.get $result_len)))
  ;; Return result as STRING (or handle if it's an object - TODO: improve this)
  (struct.new $STRING (local.get $result_offset) (local.get $result_len))
)


;; js_set_property: set property on JS object
(func $js_set_property (param $obj (ref null eq)) (param $prop_name (ref null eq)) (param $value (ref null eq)) (result (ref null eq))
  (local $obj_handle i32)
  (local $prop_str (ref null $STRING))
  (local $value_str (ref null $STRING))
  ;; Extract object handle
  (local.set $obj_handle (i31.get_s (ref.cast (ref i31) (local.get $obj))))
  ;; Convert property name to string
  (if (ref.test (ref $STRING) (local.get $prop_name))
    (then
      (local.set $prop_str (ref.cast (ref $STRING) (local.get $prop_name)))
    )
    (else
      (local.set $prop_str (call $value_to_string (local.get $prop_name)))
    )
  )
  ;; Convert value to string
  (local.set $value_str (call $value_to_string (local.get $value)))
  ;; Call import
  (call $js_set_property_import
    (local.get $obj_handle)
    (struct.get $STRING 0 (ref.cast (ref $STRING) (local.get $prop_str)))
    (struct.get $STRING 1 (ref.cast (ref $STRING) (local.get $prop_str)))
    (struct.get $STRING 0 (ref.cast (ref $STRING) (local.get $value_str)))
    (struct.get $STRING 1 (ref.cast (ref $STRING) (local.get $value_str))))
  ;; Return None
  (ref.null eq)
)


;; js_call_method: generic method call on JS object
(func $js_call_method (param $obj (ref null eq)) (param $method_name (ref null eq)) (param $args (ref null eq)) (result (ref null eq))
  (local $obj_handle i32)
  (local $method_str (ref null $STRING))
  (local $args_offset i32)
  (local $result i32)
  ;; Extract object handle
  (local.set $obj_handle (i31.get_s (ref.cast (ref i31) (local.get $obj))))
  ;; Convert method name to string
  (if (ref.test (ref $STRING) (local.get $method_name))
    (then
      (local.set $method_str (ref.cast (ref $STRING) (local.get $method_name)))
    )
    (else
      (local.set $method_str (call $value_to_string (local.get $method_name)))
    )
  )
  ;; For now, just call with no args (TODO: serialize args)
  (local.set $args_offset (i32.const 0))
  ;; Call import
  (local.set $result (call $js_call_method_import
    (local.get $obj_handle)
    (struct.get $STRING 0 (ref.cast (ref $STRING) (local.get $method_str)))
    (struct.get $STRING 1 (ref.cast (ref $STRING) (local.get $method_str)))
    (local.get $args_offset)))
  ;; Return result as handle
  (ref.i31 (local.get $result))
)

"""
