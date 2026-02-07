"""Fibonacci benchmark - iterative version.

Computes Fibonacci numbers using iterative algorithm.
This is adapted for p2w (no sys.argv).
"""

from __future__ import annotations


def fib(n: int) -> int:
    """Compute the n-th Fibonacci number iteratively."""
    a: int = 0
    b: int = 1
    for i in range(n):
        tmp: int = a + b
        a = b
        b = tmp
    return a


# Benchmark: compute fib(30) multiple times for more stable timing
N: int = 30
ITERATIONS: int = 10000  # Run many iterations to get measurable time

result: int = 0
for _ in range(ITERATIONS):
    result = fib(N)

print(f"fib({N}) = {result} (ran {ITERATIONS} iterations)")
