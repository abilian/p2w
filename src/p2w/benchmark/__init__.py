"""Robust multi-runtime benchmark suite for p2w.

This package provides statistically rigorous benchmarking with:
- Adaptive run counts targeting CV < 1%
- Support for CPython, PyPy, and Node.js (WASM) runtimes
- SQLite-based result storage and comparison
"""

from __future__ import annotations

from p2w.benchmark.database import BenchmarkDatabase, BenchmarkResult, Session
from p2w.benchmark.runner import BenchmarkRunner, BenchmarkSuite, load_suite_config
from p2w.benchmark.runtimes import RuntimeInfo, detect_runtimes
from p2w.benchmark.stats import BenchmarkStats, run_until_stable

__all__ = [
    "BenchmarkDatabase",
    "BenchmarkResult",
    "BenchmarkRunner",
    "BenchmarkStats",
    "BenchmarkSuite",
    "RuntimeInfo",
    "Session",
    "detect_runtimes",
    "load_suite_config",
    "run_until_stable",
]
