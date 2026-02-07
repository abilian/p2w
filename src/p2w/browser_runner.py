"""Browser WASM runner: simulates browser JS environment in Node.js for testing."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from p2w.compiler import compile_to_wat
from p2w.runner import wat_to_wasm

# JavaScript runner that simulates browser environment with logging
_JS_BROWSER_RUNNER = """\
import { readFileSync } from 'fs';

// Read WASM file
const wasmBuffer = readFileSync(process.argv[2]);

// Memory reference (set after instantiation)
let wasmMemory = null;

// Object table for simulating DOM handles (like browser loader.js)
const objectTable = [null, {id: 'document'}, {id: 'window'}, {id: 'console'}];
let nextHandle = 4;

function addObject(obj) {
    const handle = nextHandle++;
    objectTable[handle] = obj;
    return handle;
}

function getObject(handle) {
    return objectTable[handle] || null;
}

// Read string from WASM memory
function readString(offset, length) {
    if (!wasmMemory || offset < 0 || length < 0) return '';
    try {
        const bytes = new Uint8Array(wasmMemory.buffer, offset, length);
        return new TextDecoder('utf-8').decode(bytes);
    } catch (e) {
        console.error('readString error:', e);
        return '';
    }
}

// Capture output
const outputBytes = [];
const jsLogs = [];

// Host imports
const importObject = {
  env: {
    write_char: (byte) => {
      outputBytes.push(byte);
    },
    write_i32: (value) => {
      const str = value.toString();
      for (let i = 0; i < str.length; i++) {
        outputBytes.push(str.charCodeAt(i));
      }
    },
    write_i64: (value) => {
      const str = value.toString();
      for (let i = 0; i < str.length; i++) {
        outputBytes.push(str.charCodeAt(i));
      }
    },
    write_f64: (value) => {
      const str = value.toString();
      for (let i = 0; i < str.length; i++) {
        outputBytes.push(str.charCodeAt(i));
      }
    },
    f64_to_string: (value, offset) => {
      const str = value.toString();
      const bytes = new TextEncoder().encode(str);
      const mem = new Uint8Array(wasmMemory.buffer);
      mem.set(bytes, offset);
      return bytes.length;
    },
    f64_format_precision: (value, precision, offset) => {
      const str = value.toFixed(precision);
      const bytes = new TextEncoder().encode(str);
      const mem = new Uint8Array(wasmMemory.buffer);
      mem.set(bytes, offset);
      return bytes.length;
    },
    math_pow: (base, exp) => Math.pow(base, exp),
  },
  js: {
    // Console - log to jsLogs array
    console_log: (offset, length) => {
      const msg = readString(offset, length);
      jsLogs.push({type: 'console.log', msg});
    },
    alert: (offset, length) => {
      const msg = readString(offset, length);
      jsLogs.push({type: 'alert', msg});
    },

    // Document methods - return mock handles
    get_element_by_id: (offset, length) => {
      const id = readString(offset, length);
      jsLogs.push({type: 'getElementById', id});
      // Return a mock element handle
      return addObject({type: 'element', id});
    },
    create_element: (offset, length) => {
      const tag = readString(offset, length);
      jsLogs.push({type: 'createElement', tag});
      return addObject({type: 'element', tag});
    },
    query_selector: (handle, offset, length) => {
      const selector = readString(offset, length);
      jsLogs.push({type: 'querySelector', handle, selector});
      return addObject({type: 'element', selector});
    },

    // Canvas - return mock context handle
    get_context: (handle, typeOffset, typeLength) => {
      const contextType = readString(typeOffset, typeLength);
      jsLogs.push({type: 'getContext', handle, contextType});
      return addObject({type: 'context2d', parent: handle});
    },
    canvas_fill_rect: (handle, x, y, w, h) => {
      jsLogs.push({type: 'fillRect', handle, x, y, w, h});
    },
    canvas_fill_text: (handle, textOffset, textLength, x, y) => {
      const text = readString(textOffset, textLength);
      jsLogs.push({type: 'fillText', handle, text, x, y});
    },
    canvas_begin_path: (handle) => {
      jsLogs.push({type: 'beginPath', handle});
    },
    canvas_move_to: (handle, x, y) => {
      jsLogs.push({type: 'moveTo', handle, x, y});
    },
    canvas_line_to: (handle, x, y) => {
      jsLogs.push({type: 'lineTo', handle, x, y});
    },
    canvas_stroke: (handle) => {
      jsLogs.push({type: 'stroke', handle});
    },
    canvas_set_fill_style: (handle, offset, length) => {
      const style = readString(offset, length);
      jsLogs.push({type: 'setFillStyle', handle, style});
    },
    canvas_set_stroke_style: (handle, offset, length) => {
      const style = readString(offset, length);
      jsLogs.push({type: 'setStrokeStyle', handle, style});
    },
    canvas_set_line_width: (handle, width) => {
      jsLogs.push({type: 'setLineWidth', handle, width});
    },
    canvas_set_font: (handle, offset, length) => {
      const font = readString(offset, length);
      jsLogs.push({type: 'setFont', handle, font});
    },

    // Element content
    set_text_content: (handle, offset, length) => {
      const text = readString(offset, length);
      jsLogs.push({type: 'setTextContent', handle, text});
    },
    get_text_content: (handle, resultOffset) => {
      jsLogs.push({type: 'getTextContent', handle});
      return 0;
    },
    set_inner_html: (handle, offset, length) => {
      const html = readString(offset, length);
      jsLogs.push({type: 'setInnerHTML', handle, html});
    },
    get_inner_html: (handle, resultOffset) => {
      jsLogs.push({type: 'getInnerHTML', handle});
      return 0;
    },

    // Element properties
    get_property: (handle, nameOffset, nameLength, resultOffset) => {
      const name = readString(nameOffset, nameLength);
      jsLogs.push({type: 'getProperty', handle, name});
      return 0;
    },
    set_property: (handle, nameOffset, nameLength, valueOffset, valueLength) => {
      const name = readString(nameOffset, nameLength);
      const value = readString(valueOffset, valueLength);
      jsLogs.push({type: 'setProperty', handle, name, value});
    },
    get_value: (handle, resultOffset) => {
      jsLogs.push({type: 'getValue', handle});
      return 0;
    },
    set_value: (handle, offset, length) => {
      const value = readString(offset, length);
      jsLogs.push({type: 'setValue', handle, value});
    },

    // Element tree manipulation
    append_child: (parentHandle, childHandle) => {
      jsLogs.push({type: 'appendChild', parentHandle, childHandle});
    },
    remove_child: (parentHandle, childHandle) => {
      jsLogs.push({type: 'removeChild', parentHandle, childHandle});
    },
    set_attribute: (handle, nameOffset, nameLength, valueOffset, valueLength) => {
      const name = readString(nameOffset, nameLength);
      const value = readString(valueOffset, valueLength);
      jsLogs.push({type: 'setAttribute', handle, name, value});
    },

    // Class manipulation
    add_class: (handle, offset, length) => {
      const className = readString(offset, length);
      jsLogs.push({type: 'addClass', handle, className});
    },
    remove_class: (handle, offset, length) => {
      const className = readString(offset, length);
      jsLogs.push({type: 'removeClass', handle, className});
    },
    toggle_class: (handle, offset, length) => {
      const className = readString(offset, length);
      jsLogs.push({type: 'toggleClass', handle, className});
    },

    // Events
    add_event_listener: (handle, eventOffset, eventLength, callbackIdx) => {
      const eventType = readString(eventOffset, eventLength);
      jsLogs.push({type: 'addEventListener', handle, eventType, callbackIdx});
    },
    prevent_default: (handle) => {
      jsLogs.push({type: 'preventDefault', handle});
    },

    // Generic method call
    call_method: (handle, nameOffset, nameLength, argsOffset) => {
      const methodName = readString(nameOffset, nameLength);
      jsLogs.push({type: 'callMethod', handle, methodName});
      return 0;
    },
  },
};

// Instantiate and run
try {
  const result = await WebAssembly.instantiate(wasmBuffer, importObject);
  wasmMemory = result.instance.exports.memory;

  if (result.instance.exports._start) {
    const exitCode = result.instance.exports._start();

    // Output results as JSON
    const output = Buffer.from(outputBytes).toString('utf-8');
    console.log(JSON.stringify({
      success: true,
      exitCode,
      output,
      jsLogs,
    }));
  } else {
    console.log(JSON.stringify({
      success: false,
      error: 'No _start export found',
      jsLogs,
    }));
  }
} catch (err) {
  // Output error as JSON
  const output = Buffer.from(outputBytes).toString('utf-8');
  console.log(JSON.stringify({
    success: false,
    error: err.message,
    stack: err.stack,
    output,
    jsLogs,
  }));
  process.exit(1);
}
"""


def run_browser_wasm(wasm_bytes: bytes) -> dict:
    """Run WASM with simulated browser environment, return structured results."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Write JavaScript runner
        js_path = tmppath / "runner.mjs"
        js_path.write_text(_JS_BROWSER_RUNNER)

        # Write WASM file
        wasm_path = tmppath / "module.wasm"
        wasm_path.write_bytes(wasm_bytes)

        # Run with Node.js
        result = subprocess.run(
            ["node", str(js_path), str(wasm_path)],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

        # Parse JSON output
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {
                "success": False,
                "error": f"Failed to parse output: {result.stdout}",
                "stderr": result.stderr,
            }


def compile_and_run_browser(source: str) -> dict:
    """Compile Python source and run with browser simulation."""
    try:
        wat = compile_to_wat(source)
        wasm = wat_to_wasm(wat)
        return run_browser_wasm(wasm)
    except Exception as e:  # noqa: BLE001
        return {
            "success": False,
            "error": f"Compilation failed: {e}",
            "phase": "compile",
        }


def run_demo_file(filepath: str) -> dict:
    """Run a demo Python file with browser simulation."""
    source = Path(filepath).read_text()
    return compile_and_run_browser(source)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m p2w.browser_runner <python_file>")
        sys.exit(1)

    result = run_demo_file(sys.argv[1])

    if result.get("success"):
        print("✓ Success!")
        print(f"Exit code: {result.get('exitCode')}")
        if result.get("output"):
            print(f"Output:\n{result.get('output')}")
        if js_logs := result.get("jsLogs"):
            print(f"JS calls: {len(js_logs)}")
            for log in js_logs[:20]:  # Show first 20
                print(f"  {log}")
            if len(js_logs) > 20:
                print(f"  ... and {len(js_logs) - 20} more")
    else:
        print("✗ Failed!")
        print(f"Error: {result.get('error')}")
        if result.get("stack"):
            print(f"Stack: {result.get('stack')}")
        if result.get("output"):
            print(f"Output before error:\n{result.get('output')}")
        if js_logs := result.get("jsLogs"):
            print("JS calls before error:")
            for log in js_logs:
                print(f"  {log}")
        sys.exit(1)
