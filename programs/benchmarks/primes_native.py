"""Prime counting benchmark - native i32 version.

Count primes using trial division.
Uses i32 annotations for native WASM integer performance.
"""

from __future__ import annotations


def is_prime(n: i32) -> i32:
    """Check if n is prime using trial division."""
    if n < 2:
        return 0
    if n == 2:
        return 1
    if n % 2 == 0:
        return 0

    i: i32 = 3
    while i * i <= n:
        if n % i == 0:
            return 0
        i = i + 2

    return 1


def count_primes(limit: i32) -> i32:
    """Count all primes up to limit."""
    count: i32 = 0
    for n in range(limit + 1):
        count = count + is_prime(n)
    return count


# Benchmark: count primes multiple times
LIMIT: i32 = 10000
ITERATIONS: i32 = 10
EXPECTED: i32 = 1229  # Number of primes <= 10000

for iteration in range(ITERATIONS):
    result: i32 = count_primes(LIMIT)
    if result != EXPECTED:
        print("ERROR: expected", EXPECTED, "got", result)

print("Primes:", result)
