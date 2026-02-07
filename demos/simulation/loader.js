/**
 * p2w WASM Browser Loader
 *
 * This module loads and runs p2w-compiled WASM modules in the browser,
 * providing the necessary host imports for I/O and JavaScript interop.
 */

// Object handle table (JS objects stored here, WASM uses indices)
// Reserved handles: 0=null, 1=document, 2=window, 3=console
const objectTable = [null, null, null, null];

// WASM instance reference (for callbacks)
let wasmInstance = null;

// WASM memory reference (set after instantiation)
let wasmMemory = null;

// Output capture for console (can be redirected to DOM element)
let outputElement = null;

/**
 * Initialize reserved handles after DOM is ready
 */
function initReservedHandles() {
    objectTable[1] = document;
    objectTable[2] = window;
    objectTable[3] = console;
}

/**
 * Read a string from WASM memory
 * @param {number} offset - Byte offset in memory
 * @param {number} length - Number of bytes
 * @returns {string} Decoded UTF-8 string
 */
function readString(offset, length) {
    if (!wasmMemory) {
        console.error('readString called but wasmMemory not initialized');
        return '';
    }
    if (offset < 0 || length < 0) {
        console.error(`Invalid string params: offset=${offset}, length=${length}`);
        return '';
    }
    try {
        const bytes = new Uint8Array(wasmMemory.buffer, offset, length);
        return new TextDecoder('utf-8').decode(bytes);
    } catch (e) {
        console.error(`readString error at offset=${offset}, length=${length}:`, e);
        return '';
    }
}

/**
 * Write a string to WASM memory (for returning strings to WASM)
 * @param {string} str - String to write
 * @param {number} offset - Byte offset in memory
 * @returns {number} Number of bytes written
 */
function writeString(str, offset) {
    const bytes = new TextEncoder().encode(str);
    const mem = new Uint8Array(wasmMemory.buffer);
    mem.set(bytes, offset);
    return bytes.length;
}

/**
 * Add an object to the handle table
 * @param {any} obj - Object to store
 * @returns {number} Handle (index in table)
 */
function addObject(obj) {
    if (obj === null || obj === undefined) return 0;
    const handle = objectTable.length;
    objectTable.push(obj);
    return handle;
}

/**
 * Get an object from the handle table
 * @param {number} handle - Handle (index in table)
 * @returns {any} Object or null
 */
function getObject(handle) {
    return objectTable[handle] || null;
}

// Host imports for the "env" namespace (basic I/O)
const envImports = {
    write_char: (byte) => {
        const char = String.fromCharCode(byte);
        if (outputElement) {
            outputElement.textContent += char;
        }
        if (byte === 10) {
            console.log('[WASM output]');
        }
    },
    write_i32: (value) => {
        const str = value.toString();
        if (outputElement) {
            outputElement.textContent += str;
        }
    },
    write_i64: (value) => {
        const str = value.toString();
        if (outputElement) {
            outputElement.textContent += str;
        }
    },
    write_f64: (value) => {
        const str = value.toString();
        if (outputElement) {
            outputElement.textContent += str;
        }
    },
    f64_to_string: (value, offset) => {
        return writeString(value.toString(), offset);
    },
    f64_format_precision: (value, precision, offset) => {
        return writeString(value.toFixed(precision), offset);
    },
    math_pow: (base, exp) => Math.pow(base, exp),
};

// Host imports for the "js" namespace (JavaScript interop)
const jsImports = {
    // Console
    console_log: (offset, length) => {
        const str = readString(offset, length);
        console.log('[p2w]', str);
    },

    alert: (offset, length) => {
        const str = readString(offset, length);
        window.alert(str);
    },

    // Document methods
    get_element_by_id: (offset, length) => {
        const id = readString(offset, length);
        const element = document.getElementById(id);
        return addObject(element);
    },

    create_element: (offset, length) => {
        const tag = readString(offset, length);
        const element = document.createElement(tag);
        return addObject(element);
    },

    query_selector: (handle, offset, length) => {
        const parent = getObject(handle) || document;
        const selector = readString(offset, length);
        const element = parent.querySelector(selector);
        return addObject(element);
    },

    // Canvas
    get_context: (handle, typeOffset, typeLength) => {
        const canvas = getObject(handle);
        if (canvas && canvas.getContext) {
            const contextType = readString(typeOffset, typeLength);
            const ctx = canvas.getContext(contextType);
            return addObject(ctx);
        }
        return 0;
    },

    canvas_fill_rect: (handle, x, y, w, h) => {
        const ctx = getObject(handle);
        if (ctx && ctx.fillRect) {
            ctx.fillRect(x, y, w, h);
        }
    },

    canvas_fill_text: (handle, textOffset, textLength, x, y) => {
        const ctx = getObject(handle);
        if (ctx && ctx.fillText) {
            const text = readString(textOffset, textLength);
            ctx.fillText(text, x, y);
        }
    },

    canvas_begin_path: (handle) => {
        const ctx = getObject(handle);
        if (ctx && ctx.beginPath) {
            ctx.beginPath();
        }
    },

    canvas_move_to: (handle, x, y) => {
        const ctx = getObject(handle);
        if (ctx && ctx.moveTo) {
            ctx.moveTo(x, y);
        }
    },

    canvas_line_to: (handle, x, y) => {
        const ctx = getObject(handle);
        if (ctx && ctx.lineTo) {
            ctx.lineTo(x, y);
        }
    },

    canvas_stroke: (handle) => {
        const ctx = getObject(handle);
        if (ctx && ctx.stroke) {
            ctx.stroke();
        }
    },

    canvas_set_fill_style: (handle, offset, length) => {
        const ctx = getObject(handle);
        if (ctx) {
            ctx.fillStyle = readString(offset, length);
        }
    },

    canvas_set_stroke_style: (handle, offset, length) => {
        const ctx = getObject(handle);
        if (ctx) {
            ctx.strokeStyle = readString(offset, length);
        }
    },

    canvas_set_line_width: (handle, width) => {
        const ctx = getObject(handle);
        if (ctx) {
            ctx.lineWidth = width;
        }
    },

    canvas_set_font: (handle, offset, length) => {
        const ctx = getObject(handle);
        if (ctx) {
            ctx.font = readString(offset, length);
        }
    },

    // Element content
    set_text_content: (handle, offset, length) => {
        const element = getObject(handle);
        if (element) {
            element.textContent = readString(offset, length);
        }
    },

    get_text_content: (handle, resultOffset) => {
        const element = getObject(handle);
        if (element) {
            return writeString(element.textContent || '', resultOffset);
        }
        return 0;
    },

    set_inner_html: (handle, offset, length) => {
        const element = getObject(handle);
        if (element) {
            element.innerHTML = readString(offset, length);
        }
    },

    get_inner_html: (handle, resultOffset) => {
        const element = getObject(handle);
        if (element) {
            return writeString(element.innerHTML || '', resultOffset);
        }
        return 0;
    },

    // Element properties
    get_property: (handle, nameOffset, nameLength, resultOffset) => {
        const obj = getObject(handle);
        if (obj) {
            const name = readString(nameOffset, nameLength);
            const value = obj[name];
            if (typeof value === 'string') {
                return writeString(value, resultOffset);
            } else if (typeof value === 'object' && value !== null) {
                // Return as handle
                return addObject(value);
            } else if (value !== undefined) {
                return writeString(String(value), resultOffset);
            }
        }
        return 0;
    },

    set_property: (handle, nameOffset, nameLength, valueOffset, valueLength) => {
        const obj = getObject(handle);
        if (obj) {
            const name = readString(nameOffset, nameLength);
            const value = readString(valueOffset, valueLength);
            obj[name] = value;
        }
    },

    get_value: (handle, resultOffset) => {
        const element = getObject(handle);
        if (element && 'value' in element) {
            return writeString(element.value, resultOffset);
        }
        return 0;
    },

    set_value: (handle, offset, length) => {
        const element = getObject(handle);
        if (element && 'value' in element) {
            element.value = readString(offset, length);
        }
    },

    // Element tree manipulation
    append_child: (parentHandle, childHandle) => {
        const parent = getObject(parentHandle);
        const child = getObject(childHandle);
        if (parent && child) {
            parent.appendChild(child);
        }
    },

    remove_child: (parentHandle, childHandle) => {
        const parent = getObject(parentHandle);
        const child = getObject(childHandle);
        if (parent && child) {
            parent.removeChild(child);
        }
    },

    set_attribute: (handle, nameOffset, nameLength, valueOffset, valueLength) => {
        const element = getObject(handle);
        if (element) {
            const name = readString(nameOffset, nameLength);
            const value = readString(valueOffset, valueLength);
            element.setAttribute(name, value);
        }
    },

    // Class manipulation
    add_class: (handle, offset, length) => {
        const element = getObject(handle);
        if (element && element.classList) {
            element.classList.add(readString(offset, length));
        }
    },

    remove_class: (handle, offset, length) => {
        const element = getObject(handle);
        if (element && element.classList) {
            element.classList.remove(readString(offset, length));
        }
    },

    toggle_class: (handle, offset, length) => {
        const element = getObject(handle);
        if (element && element.classList) {
            element.classList.toggle(readString(offset, length));
        }
    },

    // Events
    add_event_listener: (handle, eventOffset, eventLength, callbackIdx) => {
        const element = getObject(handle);
        if (element) {
            const eventType = readString(eventOffset, eventLength);
            element.addEventListener(eventType, (event) => {
                // Store event in handle table
                const eventHandle = addObject(event);
                // Call back into WASM if event_callback is exported
                if (wasmInstance && wasmInstance.exports.event_callback) {
                    wasmInstance.exports.event_callback(callbackIdx, eventHandle);
                } else {
                    console.log(`[p2w] Event '${eventType}' fired, callback index: ${callbackIdx}`);
                }
            });
        }
    },

    prevent_default: (handle) => {
        const event = getObject(handle);
        if (event && event.preventDefault) {
            event.preventDefault();
        }
    },

    // Generic method call
    call_method: (handle, nameOffset, nameLength, argsOffset) => {
        const obj = getObject(handle);
        if (obj) {
            const name = readString(nameOffset, nameLength);
            if (typeof obj[name] === 'function') {
                // TODO: Deserialize args from argsOffset
                const result = obj[name]();
                if (typeof result === 'object' && result !== null) {
                    return addObject(result);
                }
                return 0;
            }
        }
        return 0;
    },
};

/**
 * Load and instantiate a p2w WASM module
 * @param {string} wasmPath - Path to .wasm file
 * @param {Object} options - Options
 * @param {HTMLElement} options.output - Element for print output
 * @returns {Promise<WebAssembly.Instance>} WASM instance
 */
export async function loadp2w(wasmPath, options = {}) {
    if (options.output) {
        outputElement = options.output;
    }

    // Initialize reserved handles
    initReservedHandles();
    console.log('[p2w] Reserved handles initialized:', objectTable.slice(0, 4));

    const importObject = {
        env: envImports,
        js: jsImports,
    };

    try {
        console.log('[p2w] Fetching WASM from:', wasmPath);
        const response = await fetch(wasmPath);
        if (!response.ok) {
            throw new Error(`Failed to fetch WASM: ${response.status} ${response.statusText}`);
        }
        const bytes = await response.arrayBuffer();
        console.log('[p2w] WASM fetched, size:', bytes.byteLength, 'bytes');

        console.log('[p2w] Instantiating WASM module...');
        const result = await WebAssembly.instantiate(bytes, importObject);
        console.log('[p2w] WASM instantiated successfully');

        // Store instance for callbacks
        wasmInstance = result.instance;

        // Get memory reference
        wasmMemory = result.instance.exports.memory;
        console.log('[p2w] Memory initialized, buffer size:', wasmMemory.buffer.byteLength);

        // List exports
        console.log('[p2w] Exports:', Object.keys(result.instance.exports));

        return result.instance;
    } catch (err) {
        console.error('[p2w] Failed to load WASM module:', err);
        console.error('[p2w] Error stack:', err.stack);
        throw err;
    }
}

/**
 * Load, instantiate, and run a p2w WASM module
 * @param {string} wasmPath - Path to .wasm file
 * @param {Object} options - Options
 * @returns {Promise<number>} Exit code from _start
 */
export async function runp2w(wasmPath, options = {}) {
    const instance = await loadp2w(wasmPath, options);

    if (instance.exports._start) {
        const exitCode = instance.exports._start();
        console.log(`WASM exited with code: ${exitCode}`);
        return exitCode;
    } else {
        console.warn('No _start function exported');
        return -1;
    }
}

// Export utilities for advanced use
export { readString, writeString, addObject, getObject, objectTable };
