# JavaScript Interop

## Architecture Overview

The interop is a **handle-based bridge** with four layers:

```
Python source  →  Compiler codegen  →  WAT wrappers  →  JS host (loader.js)
```

## 1. Python Side — Handle-Based Object Model

Python code uses a `js` module that exposes browser globals:

```python
import js
canvas = js.document.getElementById("chart")
ctx = canvas.getContext("2d")
ctx.fillRect(10, 20, 100, 50)
```

JS objects are never materialized in WASM. They're represented as **opaque integer handles** (indices into a JS-side object table). Reserved handles: `1=document`, `2=window`, `3=console`.

## 2. Compiler — Recognizing JS Patterns

When `import js` is seen (`stmt_handlers.py:330`), the compiler sets `ctx.js_imported = True`.

From there, attribute access and method calls on `js.*` or known JS handle variables are dispatched specially:

- **`js.document`** — emits `(ref.i31 (i32.const 1))` — the hardcoded handle
- **`element.getContext("2d")`** — emits `(call $js_canvas_get_context ...)` — a known method
- **Property assignment** like `ctx.fillStyle = "red"` — emits `(call $js_canvas_set_fill_style ...)`

The compiler tracks which variables hold JS handles (`ctx.js_handle_vars` in `context.py:128`) so that subsequent method calls on those variables are also routed through the JS interop path.

The dispatch logic lives in `js_interop.py`, which has specialized handlers for ~25 common DOM/Canvas methods, with a generic `$js_call_method` fallback for unrecognized ones.

## 3. WAT Layer — Wrappers + Imports

Two files cooperate:

**`wat/imports.py`** — Declares raw WASM imports from the `"js"` namespace:

```wat
(import "js" "get_element_by_id" (func $js_get_element_by_id_import (param i32) (param i32) (result i32)))
(import "js" "canvas_fill_rect" (func $js_canvas_fill_rect_import (param i32) (param f64) (param f64) (param f64) (param f64)))
```

All strings are passed as `(offset, length)` pairs pointing into WASM linear memory. Numeric args are passed as native `f64`.

**`wat/helpers/js_interop.py`** — Higher-level WAT functions that unwrap p2w's boxed values before calling the raw imports:

```
$js_document_get_element_by_id(ref null eq) → ref null eq
```

This extracts the STRING's memory offset/length, calls the raw import, and wraps the returned i32 handle back into an `i31` ref.

**Callback table** — For event handlers, closures are stored in a `$callback_table` (256-slot array). `$register_callback` stores a closure and returns an integer index that JS can use to call back into WASM.

## 4. JavaScript Host — `loader.js`

Each demo ships a `loader.js` that provides the actual implementations:

**Object handle table:**

```javascript
// Reserved: 0=null, 1=document, 2=window, 3=console
const objects = [null, document, window, console];
function addObject(obj) { objects.push(obj); return objects.length - 1; }
function getObject(handle) { return objects[handle]; }
```

**String bridge:**

```javascript
function readString(offset, length) {
    return new TextDecoder('utf-8').decode(new Uint8Array(memory.buffer, offset, length));
}
```

**DOM operations** — Each imported function reads string args from WASM memory, calls the real DOM API, and returns handles:

```javascript
get_element_by_id(offset, length) {
    const id = readString(offset, length);
    return addObject(document.getElementById(id));
}
```

**Event callbacks** — When an event fires, JS calls back into WASM:

```javascript
element.addEventListener(eventType, (event) => {
    const eventHandle = addObject(event);
    wasmInstance.exports.event_callback(callbackIdx, eventHandle);
});
```

## Data Flow Example

```python
canvas = js.document.getElementById("chart")
```

1. **Compiler** sees `js.document` — emits `(ref.i31 (i32.const 1))` (document handle)
2. **Compiler** sees `.getElementById("chart")` on a JS handle — emits `(call $js_document_get_element_by_id)`
3. **WAT wrapper** extracts the string `"chart"` from the STRING struct (offset + length), calls `$js_get_element_by_id_import`
4. **JS host** reads `"chart"` from WASM memory, calls `document.getElementById("chart")`, stores the DOM element in the object table, returns handle `4`
5. **WAT wrapper** wraps `4` as `(ref.i31 (i32.const 4))`, returns it
6. **Compiler** records `canvas` in `js_handle_vars` so future calls like `canvas.getContext(...)` are also routed through JS interop
