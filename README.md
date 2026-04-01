# p2w - Python to WebAssembly Compiler

**p2w** compiles a substantial subset of Python to WebAssembly, leveraging WASM GC for automatic memory management.

## Features

### Supported Python Features

- **Data types**: integers (arbitrary precision), floats, booleans, strings, bytes, lists, tuples, dicts, sets
- **Control flow**: if/elif/else, for/while loops, break/continue, match statements
- **Functions**: definitions, default arguments, *args/**kwargs, closures, lambdas, decorators
- **Classes**: inheritance, properties, static/class methods, special methods (`__init__`, `__str__`, etc.)
- **Comprehensions**: list, dict, set, generator expressions
- **Exception handling**: try/except/finally, raise, exception chaining
- **Context managers**: `with` statement
- **Generators**: yield, generator functions
- **Other**: f-strings, type annotations (ignored at runtime), walrus operator, unpacking

### JavaScript Interop

p2w provides seamless JavaScript interoperability via the `js` module:

```python
import js

canvas = js.document.getElementById("chart")
ctx = canvas.getContext("2d")
ctx.fillRect(0, 0, 100, 100)
js.console.log("Hello from Python!")
```

## What Works

### Browser Demos

The `demos/` directory contains two browser demos:

- **data-dashboard**: Bar chart visualization using Canvas API
- **simulation**: Physics simulation with real-time rendering

NB: They are not working yet. They were ported from <https://github.com/abilian/prescrypt/tree/main/demos> but never finished.

### Golden Programs

The `programs/internal/` directory contains **104 test programs** covering the supported Python subset. These serve as both regression tests and documentation of working features, including:

- Classes with inheritance, properties, and special methods
- Generators and comprehensions
- Exception handling with chaining
- Context managers
- Match statements
- F-strings and string operations
- Collection types and methods

### Benchmarks

Two benchmark suites validate correctness and measure performance:

**`programs/benchmarks/`** - Classic benchmarks adapted for p2w:
- fibonacci, primes, sieve, matmul
- fannkuch, binarytrees, nbody
- mandelbrot, spectralnorm, fasta
- pystone

**`programs/benchmarks-alioth/`** - Benchmarks from the [Debian Benchmark Game](https://benchmarksgame-team.pages.debian.net/benchmarksgame/) with GCC baseline comparison:
- binarytrees, nbody, spectralnorm, mandelbrot, fannkuchredux
- Includes a runner script for automated comparison against GCC (`-O3 -ffast-math`)

## Installation

```bash
# Clone the repository
git clone https://git.sr.ht/~sfermigier/p2w
cd p2w

# Install with uv
uv sync
```

## Usage

### Quick Start

Given a Python source file `fib.py`:

```python
def fib(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a

print(fib(30))
```

The simplest way to compile and run it:

```bash
uv run p2w -r fib.py
# Output: 832040
```

### Step by Step

If you want to inspect or keep the intermediate files:

```bash
# 1. Compile Python to WAT (WebAssembly Text format)
uv run p2w fib.py -o fib.wat

# 2. Convert WAT to WASM binary (requires wasm-tools)
wasm-tools parse fib.wat -o fib.wasm
```

The generated WASM cannot run standalone — it imports host functions for I/O (`write_char`, `write_i32`, etc.). The `p2w -r` flag handles this automatically by generating a Node.js loader that provides these imports and runs the module. For browser execution, see the demos in `demos/`.

### CLI Options

```
p2w [-h] [-o OUTPUT] [-r] [-v] [-d] [-V] source

  -o, --output FILE   write WAT to file instead of stdout
  -r, --run           compile and run immediately (requires wasm-tools + Node.js)
  -v, --verbose       show compilation details on stderr
  -d, --debug         dump AST and debug info to stderr
  -V, --version       show version
```

### As a Library

```python
from p2w import compile_to_wat

wat_code = compile_to_wat('print("hello")')
```

## Examples

### Fibonacci

```python
def fib(n: int) -> int:
    a, b = 0, 1
    for i in range(n):
        a, b = b, a + b
    return a

print(f"fib(30) = {fib(30)}")
```

### Browser Demo

The `demos/` directory contains browser examples:

- **data-dashboard**: Interactive bar chart visualization
- **simulation**: Physics simulation

To run a demo:

```bash
cd demos/data-dashboard
make  # Builds app.wasm
# Serve with any HTTP server and open index.html
```

## Development

```bash
# Run tests
make test

# Run linting and type checking
make lint

# Format code
make format

# Run tests with coverage
make test-cov
```

### Test Structure

- `tests/a_unit/` - Unit tests
- `tests/b_integration/` - Integration tests
- `tests/c_e2e/` - End-to-end tests

## Architecture

p2w follows a 7-phase compilation pipeline:

1. **Parse**: Python source → AST (using Python's `ast` module)
2. **Inline**: Small functions inlined at call sites
3. **Analyze**: Scope analysis, variable collection, generator detection
4. **Infer types**: Forward-flow type inference, escape analysis, native type eligibility
5. **Generate code**: AST → WAT via singledispatch visitor pattern
6. **Emit**: WAT output combining user code with runtime library (types, builtins, helpers)
7. **Assemble**: WAT → WASM (via `wasm-tools`)

The generated WASM uses GC extensions for automatic memory management. Execution requires a JavaScript host (Node.js or browser) that provides I/O and runtime imports.

See [`docs/architecture.md`](docs/architecture.md) for full details including the type system, runtime architecture, calling convention, and JavaScript interop.

## Requirements

- Python 3.12+
- [wasm-tools](https://github.com/bytecodealliance/wasm-tools) (for WAT to WASM conversion)
- [Node.js](https://nodejs.org/) 22+ (for running compiled WASM via `p2w -r`)
- For browser execution: any browser with WASM GC support (recent Chrome/Firefox)

## Prior Art and References

It's too long at this point to cite every influence and/or alternative. Here are a few that stand out:

- [Compiling Scheme to WebAssembly](https://eli.thegreenplace.net/2026/compiling-scheme-to-webassembly/) - Huge influence on unstucking the project
- [Compylo](https://github.com/abilian/compylo) - A previous attempt, started by Ethan Zouzoulkowsky (then student at EPITA) in 2023
- [Prescrypt](https://github.com/abilian/prescrypt) - A Python->JS compiler, itself based on [PScript](https://github.com/flexxui/pscript/)

## License

MIT
