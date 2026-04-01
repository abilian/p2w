# Known Bugs and Limitations

Last updated: 2026-04-01 (v0.2.2)

## Test Suite Status

- 647 passed, 20 skipped, 4 xfailed
- 93 out of 95 golden programs working (98%)

## Bugs

### Programs that compile but produce wrong output

These 4 programs compile and run but produce output that doesn't match CPython (xfail in test suite):

- `builtins_iteration_simple.py` — iteration builtins not fully matching CPython behavior
- `builtins_iteration_tools.py` — iteration tool builtins not fully matching
- `builtins_map_filter_edge.py` — edge cases in map/filter
- `builtins_numeric_extra.py` — numeric builtin edge cases

### JS interop incomplete edges

- `$js_get_property` returns results as STRING or handle, but doesn't always detect which (`wat/helpers/js_interop.py:403`)
- Generic `$js_call_method` doesn't serialize arguments to JS yet (`wat/helpers/js_interop.py:455`)

## Unimplemented Features

### Exception handling gaps

| Feature | Status |
|---------|--------|
| Exception hierarchy (`except ValueError`) | Catches everything, doesn't check type |
| `return` inside `try/finally` | Not implemented |
| Bare `raise` (re-raise current exception) | Not implemented |
| `IndexError` on out-of-bounds access | Not raised (undefined behavior) |
| `KeyError` on missing dict key | Not raised |
| `ZeroDivisionError` | Not raised |

### Generator gaps

| Feature | Status |
|---------|--------|
| `yield from` delegation | Not implemented (blocks `generators.py`) |
| `send()` and `throw()` methods | Not implemented (blocks `generator_protocol.py`) |
| Yield expressions in computations | Not working (`x = yield value`) |
| Generator state preservation | Partial — local vars across multiple yields can be lost |
| Empty generator with early return | Not working |

### Large integer (INT64) gaps

| Feature | Status |
|---------|--------|
| Bitwise `&`, `\|`, `^`, `~` on INT64 | Not implemented (only works on i31 range) |
| `<<`, `>>` producing INT64 results | Not implemented |

### Language features not supported

| Feature | Reason |
|---------|--------|
| `async` / `await` | Requires WASM stack switching (not standardized) |
| Multi-file modules / `import` | Single-file compilation only |
| `**rest` capture in match patterns | Not implemented |
| Complex starred unpack targets | Partial support |
| Some augmented assignment targets | Only `Name`, `Subscript`, `Attribute` supported |
| `del` on non-Name targets | Not implemented |
| Metaclasses | Not planned |
| `__del__` finalizers | Impossible with WASM GC (no weak refs, no finalization) |
| WASM debugging / source maps | Tooling immature |
| SIMD optimizations | Not planned for now |

## Performance Limitations

| Area | Issue | Speedup |
|------|-------|---------|
| matmul | Nested list access `a[i][k] * b[k][j]` is inherently slow with Python-style 2D lists | 4.0x |
| mandelbrot | Float loop overhead, could benefit from further native type optimization | 6.2x |
| Untyped code | Without type annotations, everything stays boxed — no speedup over CPython | ~1x |

Current GEOMEAN speedup: **9.46x** vs CPython (with type annotations on hot paths).

## Programs Out of Scope

| Program | Blocker |
|---------|---------|
| `async.py` | Requires async/await (WASM stack switching not standardized) |
| `generator_protocol.py` | Requires `send()` / `throw()` |
