"""Fannkuch Redux benchmark - native i32 version.

Computes the maximum number of flips to sort a permutation.
Uses i32 annotations for native WASM integer performance.
"""

from __future__ import annotations


def factorial(n: i32) -> i32:
    """Compute n factorial."""
    result: i32 = 1
    for i in range(2, n + 1):
        result = result * i
    return result


def fannkuch(n: i32) -> None:
    """Run the fannkuch benchmark."""
    perm: list[int] = list(range(n))
    perm1: list[int] = list(range(n))
    count: list[int] = [0] * n

    max_flips: i32 = 0
    checksum: i32 = 0
    perm_count: i32 = 0

    r: i32 = n
    while True:
        # Generate next permutation
        while r > 1:
            count[r - 1] = r
            r = r - 1

        # Copy perm1 to perm
        for i in range(n):
            perm[i] = perm1[i]

        # Count flips
        flips: i32 = 0
        k: i32 = perm[0]
        while k != 0:
            # Reverse perm[0:k+1]
            i: i32 = 0
            j: i32 = k
            while i < j:
                tmp: i32 = perm[i]
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

            perm0: i32 = perm1[0]
            i: i32 = 0
            while i < r:
                j: i32 = i + 1
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
