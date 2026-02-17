# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-02-17

### Fixed

- Floor division (`//`) now correctly rounds toward negative infinity for negative numbers
- Modulo (`%`) now correctly returns result with sign of divisor (Python semantics)
- Removed duplicate type analysis pass in inference phase
- Fixed dict comprehension tuple unpacking in escape analysis

### Added

- `p2w-benchmark check` command for detecting performance regressions between sessions
- Property-based testing with hypothesis for compiler correctness verification
- Comprehensive test suite additions (171 new tests):
  - Type inference unit tests
  - AST analysis unit tests
  - Large integer boundary tests (i31/INT64 transitions)
  - Generator corner case tests
  - Exception handling tests
  - Property-based compilation tests
- Architecture documentation (`docs/architecture.md`)
- Mermaid diagrams for compilation pipeline and type system

### Changed

- Simplified `$int_div` and `$int_mod` runtime functions using new native helpers
- Added native `$i32_floordiv`, `$i32_mod`, `$i64_floordiv`, `$i64_mod` WAT helpers

## [0.1.0] - 2026-02-09

Initial public release.

### Features

- Python-to-WAT compiler supporting a substantial Python subset
- Data types: integers (arbitrary precision), floats, booleans, strings, bytes, lists, tuples, dicts, sets
- Control flow: if/elif/else, for/while loops, break/continue, match statements
- Functions: definitions, default arguments, *args/**kwargs, closures, lambdas, decorators
- Classes: inheritance, properties, static/class methods, special methods
- Comprehensions: list, dict, set, generator expressions
- Exception handling: try/except/finally, raise, exception chaining
- Context managers, generators, f-strings, walrus operator
- JavaScript interop via `js` module for browser integration
- WASM GC for automatic memory management

### Included

- 104 golden test programs in `programs/internal/`
- Two benchmark suites (`programs/benchmarks/`, `programs/benchmarks-alioth/`)
- Two browser demos (`demos/data-dashboard`, `demos/simulation`)
