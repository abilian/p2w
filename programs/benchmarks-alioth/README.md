# Alioth Benchmark Game - p2w vs GCC

This directory contains benchmarks from the [Debian Benchmark Game](https://benchmarksgame-team.pages.debian.net/benchmarksgame/) adapted for p2w comparison.

## Benchmarks

The following benchmarks are included:

| Benchmark | Description |
|-----------|-------------|
| binarytrees | Allocate, traverse, and deallocate binary trees |
| nbody | N-body simulation (planetary orbit calculation) |
| spectralnorm | Calculate spectral norm of a matrix |
| mandelbrot | Generate Mandelbrot set fractal |
| fannkuchredux | Indexed-access to tiny integer-sequence |

## Running Benchmarks

```bash
# Run all benchmarks
uv run python programs/benchmarks-alioth/run_benchmarks.py

# Run specific benchmark
uv run python programs/benchmarks-alioth/run_benchmarks.py --benchmark nbody

# Save results to database
uv run python programs/benchmarks-alioth/run_benchmarks.py --save -d "description"

# List saved sessions
uv run python programs/benchmarks-alioth/run_benchmarks.py --list

# Compare sessions
uv run python programs/benchmarks-alioth/run_benchmarks.py --compare 1 2

# Customize runs
uv run python programs/benchmarks-alioth/run_benchmarks.py --warmup 3 --runs 10
```

## Results Interpretation

The ratio shown is `p2w_time / gcc_time`:
- Ratio < 1.0: p2w is faster than GCC
- Ratio = 1.0: same speed
- Ratio > 1.0: p2w is slower than GCC

GEOMEAN is the geometric mean of all ratios, which is appropriate for comparing ratios/speedups.

## Directory Structure

```
programs/benchmarks-alioth/
├── run_benchmarks.py     # Benchmark runner script
├── benchmark_results.db  # SQLite database with results (created on --save)
├── python/               # Python benchmarks adapted for p2w
│   ├── binarytrees.py
│   ├── [...]
│   └── fannkuchredux.py
└── gcc/                  # GCC C source files for baseline
    ├── [same].gcc
```

## Notes

- Python programs are adapted to use only features supported by p2w
- GCC programs are compiled with `-O3 -ffast-math`
- Some benchmarks have been modified for fair comparison (e.g., mandelbrot counts pixels instead of producing PBM output)
