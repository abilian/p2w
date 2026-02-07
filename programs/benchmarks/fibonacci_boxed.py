"""Fibonacci benchmark - iterative version with boxed types.

Computes Fibonacci numbers using iterative algorithm.
Uses boxed Python int types for comparison with native types.
"""

from __future__ import annotations


def fib(n: int) -> int:
    """Compute the n-th Fibonacci number iteratively."""
    a = 0
    b = 1
    i = 0
    while i < n:
        tmp = a + b
        a = b
        b = tmp
        i = i + 1
    return a


# Benchmark: compute fib(30) multiple times for more stable timing
N = 30
ITERATIONS = 10000  # Run many iterations to get measurable time

result = 0
iter_count = 0
while iter_count < ITERATIONS:
    result = fib(N)
    iter_count = iter_count + 1

print("fib(30) =", result, "(ran 10000 iterations)")
