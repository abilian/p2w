"""Sieve of Eratosthenes benchmark.

Classic prime number sieve algorithm.
Adapted for p2w.
"""

from __future__ import annotations


def sieve(n: int) -> int:
    """Find all primes up to n using the Sieve of Eratosthenes."""
    # Create a list of booleans (1 = prime, 0 = not prime)
    is_prime: list[int] = []
    for i in range(n + 1):
        if i < 2:
            is_prime.append(0)
        else:
            is_prime.append(1)

    # Sieve
    i: int = 2
    while i * i <= n:
        if is_prime[i] == 1:
            j: int = i * i
            while j <= n:
                is_prime[j] = 0
                j = j + i
        i = i + 1

    # Count primes
    count: int = 0
    for i in range(n + 1):
        if is_prime[i] == 1:
            count = count + 1

    return count


# Benchmark: find primes up to 10000, multiple iterations
ITERATIONS: int = 10
N: int = 10000
EXPECTED: int = 1229  # Number of primes <= 10000

for iteration in range(ITERATIONS):
    result: int = sieve(N)
    if result != EXPECTED:
        print("ERROR: expected", EXPECTED, "got", result)

print("Sieve:", result, "primes")
