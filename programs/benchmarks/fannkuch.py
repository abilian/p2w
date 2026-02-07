"""Fannkuch Redux benchmark.

Computes the maximum number of flips to sort a permutation.
Adapted for p2w (no sys.argv, no generators, no multiprocessing).
"""

from __future__ import annotations


def factorial(n: int) -> int:
    """Compute n factorial."""
    result: int = 1
    for i in range(2, n + 1):
        result = result * i
    return result


def fannkuch(n: int) -> None:
    """Run the fannkuch benchmark."""
    perm: list[int] = list(range(n))
    perm1: list[int] = list(range(n))
    count: list[int] = [0] * n

    max_flips: int = 0
    checksum: int = 0
    perm_count: int = 0

    r: int = n
    while True:
        # Generate next permutation
        while r > 1:
            count[r - 1] = r
            r = r - 1

        # Copy perm1 to perm
        for i in range(n):
            perm[i] = perm1[i]

        # Count flips
        flips: int = 0
        k: int = perm[0]
        while k != 0:
            # Reverse perm[0:k+1]
            i: int = 0
            j: int = k
            while i < j:
                tmp: int = perm[i]
                perm[i] = perm[j]
                perm[j] = tmp
                i = i + 1
                j = j - 1
            flips = flips + 1
            k = perm[0]

        if flips > max_flips:
            max_flips = flips

        if perm_count % 2 == 0:
            checksum = checksum + flips
        else:
            checksum = checksum - flips

        # Next permutation
        while True:
            if r == n:
                print(checksum)
                print(f"Pfannkuchen({n}) = {max_flips}")
                return

            perm0: int = perm1[0]
            i: int = 0
            while i < r:
                j: int = i + 1
                perm1[i] = perm1[j]
                i = j
            perm1[r] = perm0

            count[r] = count[r] - 1
            if count[r] > 0:
                break
            r = r + 1

        perm_count = perm_count + 1


# Benchmark with n=9 (reasonable size for p2w)
fannkuch(9)
