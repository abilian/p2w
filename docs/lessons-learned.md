# Lessons Learned

Notes on what worked, what didn't, and what surprised us while building p2w.

## WASM GC is a great target for language compilers

WASM GC eliminates the need to implement a garbage collector. This is a huge win. Struct and array types map naturally to language-level objects, and the host engine (V8, SpiderMonkey) handles all the hard parts: generational collection, compaction, write barriers. In ~15k lines of Python, we have a compiler that handles closures, generators, exceptions, and classes — with zero GC bugs.

The downside is that you're locked into the type system WASM GC provides. You can't, say, store a tagged union in a single word. Everything is a reference, and the only unboxed reference type is i31ref.

## WASM GC uses structural typing, which causes real problems

WASM GC types are compared structurally, not nominally. Two struct types with the same field layout are the same type at runtime. This means `ref.test` and `ref.cast` can't distinguish them.

We hit this multiple times and had to add dummy fields to make types distinguishable:

- `$STRING` is `(struct i32 i32)` and `$BYTES` needed to be `(struct i32 i32 i32)` — an extra padding field just so `ref.test` can tell them apart
- `$STATICMETHOD` and `$CLASSMETHOD` both wrap a `$CLOSURE`, so we gave them different field orders: `(closure, padding)` vs `(padding, closure)`
- `$ELLIPSIS` uses a `f32` field (unused elsewhere) to be unique

These are ugly but effective. The alternative would be tagging everything with an integer discriminator, which has its own costs.

## The i31 boundary is a source of subtle bugs

WASM's i31ref stores integers from -2^30 to 2^30-1 (~plus/minus 1 billion). This covers most Python integers, but overflow is silent — values wrap without warning.

We chose a dual representation: i31ref for small integers, a boxed `$INT64` struct for anything larger. This means every integer operation must potentially check for overflow and promote. The compiler detects large integer literals at compile time, but runtime arithmetic can still overflow unexpectedly.

The worst bugs were in floor division and modulo with negative numbers. WASM's `div_s` truncates toward zero; Python's `//` rounds toward negative infinity. WASM's `rem_s` gives the sign of the dividend; Python's `%` gives the sign of the divisor. Property-based testing with Hypothesis caught both bugs — they were invisible in our hand-written test suite.

## Boxing is the dominant performance cost

Every Python value in p2w is a `(ref null eq)` — a generic reference. To use it as an integer, you cast to `i31`, extract the value, do arithmetic, and box the result back. In a tight loop, this overhead dominates.

The solution was escape analysis: if a variable is never passed to a function, stored in a container, or returned, it can live as a raw WASM local (`i32`, `i64`, or `f64`). This required:

1. Type inference to know what type a variable has
2. Escape analysis to know if it leaves its local scope
3. Native type tracking through the codegen phase (`has_native_value` flag)

The result: loop counters over `range()` become native i32 loops. Float variables annotated as `f64` stay unboxed. This is where the 3-10x speedup over CPython comes from — and it only works when type annotations provide enough information.

Without annotations, everything stays boxed, and performance is roughly on par with CPython.

## Slotted classes were the biggest single optimization win

Classes with `__slots__` compile to fixed WASM GC structs with direct field access. Without slots, attribute access is a PAIR chain scan — O(n) in the number of attributes. With slots, it's a single `struct.get` instruction.

On pystone, this one change took us from 3.4x to 7.4x vs CPython. The implementation was straightforward: detect `__slots__` at analysis time, generate a custom struct type per class, compile `obj.attr` to `struct.get` instead of a runtime lookup.

## Direct WAT output was the right choice — for now

We emit WAT text directly, with no intermediate representation. This keeps the compiler simple and the output readable (you can grep the generated WAT to debug issues). The `WATEmitter` handles indentation and string interning, and codegen functions just call `emitter.line(...)`.

The downside is that optimization passes are essentially impossible. We can't do dead code elimination, common subexpression elimination, or register allocation on a stream of text. If the project grows to need these, we'd need to add an IR. But for a side project, the simplicity has been worth it.

## Function inlining at the AST level works surprisingly well

Rather than adding an IR for optimization, we inline small functions by transforming the AST before codegen. The inliner identifies non-recursive, single-expression functions and substitutes their bodies at call sites. This is crude compared to a proper inlining pass, but it eliminates call overhead for helper functions and — crucially — allows type inference to propagate through the inlined code.

## Generators required a full state machine transformation

Without WASM stack switching (still not standardized), generators can't suspend and resume naturally. Each generator function is compiled into a state machine: yield points become numbered states, local variables are saved to a `$GENERATOR` struct, and `__next__()` dispatches to the right state.

This was significantly harder than expected. Yield expressions (as opposed to yield statements) require saving partial expression state. Yields inside loops need careful state numbering. `yield from` delegation is still incomplete because it adds another layer of state management.

## The JavaScript interop works well as a handle-based bridge

JS objects can't cross into WASM GC directly. Our solution: JS objects stay in a JS-side table, and WASM holds integer handles (indices into that table). The compiler recognizes `import js` and routes attribute access and method calls through WAT wrapper functions that marshal arguments (strings as offset+length pairs, numbers as f64).

This works cleanly for DOM manipulation and Canvas drawing. The main limitation is that the compiler must know which methods exist — we have specialized handlers for ~25 common DOM/Canvas methods, with a generic fallback for the rest. Adding new methods means adding new WAT wrappers.

## Python's `ast` module is an underrated compiler frontend

Using Python's built-in parser eliminated an entire compiler phase. We get a correct, well-tested AST for free, including all Python 3.12 syntax. The `match/case` statement (Python 3.10+) turned out to be excellent for writing codegen — pattern matching on AST nodes is more readable than `isinstance` chains and extracts fields in one step.

The downside: we're tied to CPython's AST representation, which changes between Python versions. And we can't extend the syntax (no custom operators or annotations beyond what Python allows).

## Property-based testing found bugs that unit tests missed

Hypothesis generates random Python expressions and checks that p2w produces the same output as CPython. This caught the floor division and modulo sign bugs mentioned above, which had been in the compiler since the beginning. No amount of hand-written tests for `10 // 3` and `7 % 4` would have found that `-4 // 75` returns the wrong result.

The lesson: for a compiler, testing equivalence with a reference implementation on random inputs is far more effective than testing specific cases.

## Hash tables were necessary earlier than expected

The initial design used PAIR chains (linked lists) for everything: function arguments, list elements, dict entries. This works for small collections but breaks completely at scale — dict lookup is O(n), which makes any real Python program unusably slow.

We implemented hash tables from scratch in WAT: bucket arrays, chained entries, hash functions for each Python type, and a resize strategy. This was a substantial effort (~500 lines of WAT), but it made dicts and sets usable for the first time.

## What we'd do differently

**Start with array-backed lists.** We began with PAIR chains (following the Scheme inspiration) and added array-backed `$LIST` later. The migration touched almost every codegen module. Starting with arrays would have saved significant rework.

**Add an IR earlier — maybe.** Direct WAT emission is simple, but it makes multi-pass optimization impossible. On the other hand, an IR would have slowed early development. The right time to add one would be when optimization becomes the bottleneck, which hasn't happened yet.

**Invest in property-based testing from day one.** The bugs it found were old and deeply embedded. Earlier testing would have caught them before they became entrenched.

## What's still hard

- **async/await**: Requires WASM stack switching, which isn't standardized yet
- **Full exception hierarchy**: We have try/except/finally, but `except ValueError` doesn't check the exception type — it catches everything
- **Modules**: The compiler processes one file at a time, with no import system
- **Dynamic features**: `getattr`/`setattr`, metaclasses, and other reflection features would require a much heavier runtime
