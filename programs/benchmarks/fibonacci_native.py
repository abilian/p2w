"""Fibonacci benchmark - iterative version with native types.

Computes Fibonacci numbers using iterative algorithm.
Uses native i32 types for maximum performance.
"""

from __future__ import annotations


def fib(n: i32) -> i32:
    """Compute the n-th Fibonacci number iteratively."""
    a: i32 = 0
    b: i32 = 1
    i: i32 = 0
    while i < n:
        tmp: i32 = a + b
        a = b
        b = tmp
        i = i + 1
    return a


# Benchmark: compute fib(30) multiple times for more stable timing
N: i32 = 30
ITERATIONS: i32 = 10000  # Run many iterations to get measurable time

result: i32 = 0
iter_count: i32 = 0
while iter_count < ITERATIONS:
    result = fib(N)
    iter_count = iter_count + 1

print("fib(30) =", result, "(ran 10000 iterations)")
