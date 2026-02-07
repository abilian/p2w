"""Prime counting benchmark.

Count primes using trial division.
Adapted for p2w.
"""

from __future__ import annotations


def is_prime(n: int) -> int:
    """Check if n is prime using trial division."""
    if n < 2:
        return 0
    if n == 2:
        return 1
    if n % 2 == 0:
        return 0

    i: int = 3
    while i * i <= n:
        if n % i == 0:
            return 0
        i = i + 2

    return 1


def count_primes(limit: int) -> int:
    """Count all primes up to limit."""
    count: int = 0
    for n in range(limit + 1):
        count = count + is_prime(n)
    return count


# Benchmark: count primes multiple times
LIMIT: int = 10000
ITERATIONS: int = 10
EXPECTED: int = 1229  # Number of primes <= 10000

for iteration in range(ITERATIONS):
    result: int = count_primes(LIMIT)
    if result != EXPECTED:
        print("ERROR: expected", EXPECTED, "got", result)

print("Primes:", result)
