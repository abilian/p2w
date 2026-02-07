"""Sieve of Eratosthenes benchmark - native i32 version.

Classic prime number sieve algorithm.
Uses i32 annotations for native WASM integer performance.
"""

from __future__ import annotations


def sieve(n: i32) -> i32:
    """Find all primes up to n using the Sieve of Eratosthenes."""
    # Create a list of booleans (1 = prime, 0 = not prime)
    is_prime: list[int] = []
    for i in range(n + 1):
        if i < 2:
            is_prime.append(0)
        else:
            is_prime.append(1)

    # Sieve
    i: i32 = 2
    while i * i <= n:
        if is_prime[i] == 1:
            j: i32 = i * i
            while j <= n:
                is_prime[j] = 0
                j = j + i
        i = i + 1

    # Count primes
    count: i32 = 0
    for i in range(n + 1):
        if is_prime[i] == 1:
            count = count + 1

    return count


# Benchmark: find primes up to 10000, multiple iterations
ITERATIONS: i32 = 10
N: i32 = 10000
EXPECTED: i32 = 1229  # Number of primes <= 10000

for iteration in range(ITERATIONS):
    result: i32 = sieve(N)
    if result != EXPECTED:
        print("ERROR: expected", EXPECTED, "got", result)

print("Sieve:", result, "primes")
