# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
