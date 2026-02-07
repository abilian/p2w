"""WASM runner: compile WAT to WASM and execute with Node.js."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

# JavaScript runner that provides the host environment (ES module syntax)
_JS_RUNNER = """\
import { readFileSync } from 'fs';

// Read WASM file
const wasmBuffer = readFileSync(process.argv[2]);

// Capture output as byte buffer (for proper UTF-8 handling)
const outputBytes = [];

// Memory reference (set after instantiation)
let wasmMemory = null;

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
      // BigInt values from WASM are automatically converted to JavaScript BigInt
      const str = value.toString();
      for (let i = 0; i < str.length; i++) {
        outputBytes.push(str.charCodeAt(i));
      }
    },
    write_f64: (value) => {
      // Format float to include .0 for whole numbers (Python repr style)
      let str = value.toString();
      if (Number.isFinite(value) && !str.includes('.') && !str.includes('e')) {
        str += '.0';
      }
      for (let i = 0; i < str.length; i++) {
        outputBytes.push(str.charCodeAt(i));
      }
    },
    // Convert f64 to string, write to memory at offset, return length
    f64_to_string: (value, offset) => {
      // Format float to include .0 for whole numbers (Python repr style)
      let str = value.toString();
      if (Number.isFinite(value) && !str.includes('.') && !str.includes('e')) {
        str += '.0';
      }
      const bytes = new TextEncoder().encode(str);
      const mem = new Uint8Array(wasmMemory.buffer);
      mem.set(bytes, offset);
      return bytes.length;
    },
    // Format f64 with precision, write to memory at offset, return length
    f64_format_precision: (value, precision, offset) => {
      const str = value.toFixed(precision);
      const bytes = new TextEncoder().encode(str);
      const mem = new Uint8Array(wasmMemory.buffer);
      mem.set(bytes, offset);
      return bytes.length;
    },
    // Math.pow for non-integer exponents
    math_pow: (base, exp) => Math.pow(base, exp),
  },
  // JavaScript interop stubs (no-op in Node.js test environment)
  js: {
    // Console
    console_log: (offset, length) => {},
    alert: (offset, length) => {},

    // Document methods
    get_element_by_id: (offset, length) => 0,
    create_element: (offset, length) => 0,
    query_selector: (handle, offset, length) => 0,

    // Canvas
    get_context: (handle, typeOffset, typeLength) => 0,
    canvas_fill_rect: (handle, x, y, w, h) => {},
    canvas_fill_text: (handle, textOffset, textLength, x, y) => {},
    canvas_begin_path: (handle) => {},
    canvas_move_to: (handle, x, y) => {},
    canvas_line_to: (handle, x, y) => {},
    canvas_stroke: (handle) => {},
    canvas_set_fill_style: (handle, offset, length) => {},
    canvas_set_stroke_style: (handle, offset, length) => {},
    canvas_set_line_width: (handle, width) => {},
    canvas_set_font: (handle, offset, length) => {},

    // Element content
    set_text_content: (handle, offset, length) => {},
    get_text_content: (handle, resultOffset) => 0,
    set_inner_html: (handle, offset, length) => {},
    get_inner_html: (handle, resultOffset) => 0,

    // Element properties
    get_property: (handle, nameOffset, nameLength, resultOffset) => 0,
    set_property: (handle, nameOffset, nameLength, valueOffset, valueLength) => {},
    get_value: (handle, resultOffset) => 0,
    set_value: (handle, offset, length) => {},

    // Element tree manipulation
    append_child: (parentHandle, childHandle) => {},
    remove_child: (parentHandle, childHandle) => {},
    set_attribute: (handle, nameOffset, nameLength, valueOffset, valueLength) => {},

    // Class manipulation
    add_class: (handle, offset, length) => {},
    remove_class: (handle, offset, length) => {},
    toggle_class: (handle, offset, length) => {},

    // Events
    add_event_listener: (handle, eventOffset, eventLength, callbackIdx) => {},
    prevent_default: (handle) => {},

    // Generic method call
    call_method: (handle, nameOffset, nameLength, argsOffset) => 0,
  },
};

// Instantiate and run
try {
  const result = await WebAssembly.instantiate(wasmBuffer, importObject);
  // Get memory reference for f64_to_string
  wasmMemory = result.instance.exports.memory;
  const exitCode = result.instance.exports._start();
  // Decode output bytes as UTF-8
  const output = new TextDecoder('utf-8').decode(new Uint8Array(outputBytes));
  process.stdout.write(output);
  process.exit(exitCode);
} catch (err) {
  console.error('WASM execution error:', err);
  process.exit(1);
}
"""


def wat_to_wasm(wat_code: str) -> bytes:
    """Convert WAT to WASM binary using wasm-tools.

    Args:
        wat_code: WebAssembly Text format code.

    Returns:
        WASM binary bytes.

    Raises:
        subprocess.CalledProcessError: If wasm-tools fails.
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".wat", delete=False) as wat_file:
        wat_file.write(wat_code)
        wat_path = Path(wat_file.name)

    wasm_path = wat_path.with_suffix(".wasm")

    try:
        subprocess.run(
            ["wasm-tools", "parse", str(wat_path), "-o", str(wasm_path)],
            check=True,
            capture_output=True,
            text=True,
        )
        return wasm_path.read_bytes()
    finally:
        wat_path.unlink(missing_ok=True)
        wasm_path.unlink(missing_ok=True)


def run_wasm(wasm_bytes: bytes) -> str:
    """Run WASM binary with Node.js and return output.

    Args:
        wasm_bytes: WASM binary bytes.

    Returns:
        Standard output from execution.

    Raises:
        subprocess.CalledProcessError: If Node.js execution fails.
    """
    with tempfile.NamedTemporaryFile(suffix=".wasm", delete=False) as wasm_file:
        wasm_file.write(wasm_bytes)
        wasm_path = Path(wasm_file.name)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".mjs", delete=False) as js_file:
        js_file.write(_JS_RUNNER)
        js_path = Path(js_file.name)

    try:
        result = subprocess.run(
            ["node", str(js_path), str(wasm_path)],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        return result.stdout
    finally:
        wasm_path.unlink(missing_ok=True)
        js_path.unlink(missing_ok=True)


def run_wat(wat_code: str) -> str:
    """Compile WAT to WASM and run it.

    Args:
        wat_code: WebAssembly Text format code.

    Returns:
        Standard output from execution.
    """
    wasm_bytes = wat_to_wasm(wat_code)
    return run_wasm(wasm_bytes)


def run_python(source: str) -> str:
    """Run Python source code and capture output.

    Args:
        source: Python source code.

    Returns:
        Standard output from execution.
    """
    result = subprocess.run(
        ["python", "-c", source],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout
