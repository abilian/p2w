"""WAT import declarations for the host environment."""

from __future__ import annotations

IMPORTS_CODE = """
(import "env" "write_char" (func $write_char (param i32)))
(import "env" "write_i32" (func $write_i32 (param i32)))
(import "env" "write_i64" (func $write_i64 (param i64)))
(import "env" "write_f64" (func $write_f64 (param f64)))
(import "env" "f64_to_string" (func $f64_to_string (param f64) (param i32) (result i32)))
(import "env" "f64_format_precision" (func $f64_format_precision (param f64) (param i32) (param i32) (result i32)))

;; JavaScript interop imports (for browser environment)
;; These pass string data as (offset, length) pairs from linear memory
;; Import names have _import suffix to avoid conflicts with builtin wrapper functions

;; Console
(import "js" "console_log" (func $js_console_log_import (param i32) (param i32)))
(import "js" "alert" (func $js_alert_import (param i32) (param i32)))

;; Document methods
(import "js" "get_element_by_id" (func $js_get_element_by_id_import (param i32) (param i32) (result i32)))
(import "js" "create_element" (func $js_create_element_import (param i32) (param i32) (result i32)))
(import "js" "query_selector" (func $js_query_selector_import (param i32) (param i32) (param i32) (result i32)))

;; Element content
(import "js" "set_text_content" (func $js_set_text_content_import (param i32) (param i32) (param i32)))
(import "js" "get_text_content" (func $js_get_text_content_import (param i32) (param i32) (result i32)))
(import "js" "set_inner_html" (func $js_set_inner_html_import (param i32) (param i32) (param i32)))
(import "js" "get_inner_html" (func $js_get_inner_html_import (param i32) (param i32) (result i32)))

;; Element properties
(import "js" "get_property" (func $js_get_property_import (param i32) (param i32) (param i32) (param i32) (result i32)))
(import "js" "set_property" (func $js_set_property_import (param i32) (param i32) (param i32) (param i32) (param i32)))
(import "js" "get_value" (func $js_get_value_import (param i32) (param i32) (result i32)))
(import "js" "set_value" (func $js_set_value_import (param i32) (param i32) (param i32)))

;; Element tree manipulation
(import "js" "append_child" (func $js_append_child_import (param i32) (param i32)))
(import "js" "remove_child" (func $js_remove_child_import (param i32) (param i32)))
(import "js" "set_attribute" (func $js_set_attribute_import (param i32) (param i32) (param i32) (param i32) (param i32)))

;; Class manipulation
(import "js" "add_class" (func $js_add_class_import (param i32) (param i32) (param i32)))
(import "js" "remove_class" (func $js_remove_class_import (param i32) (param i32) (param i32)))
(import "js" "toggle_class" (func $js_toggle_class_import (param i32) (param i32) (param i32)))

;; Canvas
(import "js" "get_context" (func $js_get_context_import (param i32) (param i32) (param i32) (result i32)))
(import "js" "canvas_fill_rect" (func $js_canvas_fill_rect_import (param i32) (param f64) (param f64) (param f64) (param f64)))
(import "js" "canvas_fill_text" (func $js_canvas_fill_text_import (param i32) (param i32) (param i32) (param f64) (param f64)))
(import "js" "canvas_begin_path" (func $js_canvas_begin_path_import (param i32)))
(import "js" "canvas_move_to" (func $js_canvas_move_to_import (param i32) (param f64) (param f64)))
(import "js" "canvas_line_to" (func $js_canvas_line_to_import (param i32) (param f64) (param f64)))
(import "js" "canvas_stroke" (func $js_canvas_stroke_import (param i32)))
(import "js" "canvas_set_fill_style" (func $js_canvas_set_fill_style_import (param i32) (param i32) (param i32)))
(import "js" "canvas_set_stroke_style" (func $js_canvas_set_stroke_style_import (param i32) (param i32) (param i32)))
(import "js" "canvas_set_line_width" (func $js_canvas_set_line_width_import (param i32) (param f64)))
(import "js" "canvas_set_font" (func $js_canvas_set_font_import (param i32) (param i32) (param i32)))

;; Events
(import "js" "add_event_listener" (func $js_add_event_listener_import (param i32) (param i32) (param i32) (param i32)))
(import "js" "prevent_default" (func $js_prevent_default_import (param i32)))

;; Generic method call (for extensibility)
(import "js" "call_method" (func $js_call_method_import (param i32) (param i32) (param i32) (param i32) (result i32)))

;; Math functions (for pow with non-integer exponents)
(import "env" "math_pow" (func $math_pow (param f64) (param f64) (result f64)))

;; String heap for runtime-allocated strings
(global $string_heap (mut i32) (i32.const 65536))

;; Temporary storage for dict.pop() to cache updated dict between calls
(global $tmp_pop_dict (mut (ref null eq)) (ref.null eq))
"""

# These globals must come after type definitions
POST_TYPES_GLOBALS = """
;; Ellipsis singleton (uses f32 field to be structurally unique)
(global $ellipsis (ref $ELLIPSIS) (struct.new $ELLIPSIS (f32.const 0)))

;; Boolean singletons for identity comparison (True is True, False is False)
(global $TRUE (ref $BOOL) (struct.new $BOOL (i32.const 1)))
(global $FALSE (ref $BOOL) (struct.new $BOOL (i32.const 0)))
"""
