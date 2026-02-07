"""Matrix multiplication benchmark - native i32 version.

Naive O(n^3) matrix multiplication.
Uses i32 annotations for native WASM integer performance.
"""

from __future__ import annotations


def make_matrix(rows: i32, cols: i32, value: i32) -> list[list[int]]:
    """Create a rows x cols matrix filled with value."""
    m: list[list[int]] = []
    i: i32 = 0
    while i < rows:
        row: list[int] = []
        j: i32 = 0
        while j < cols:
            row.append(value)
            j = j + 1
        m.append(row)
        i = i + 1
    return m


def fill_matrix(m: list[list[int]], rows: i32, cols: i32) -> None:
    """Fill matrix with deterministic values."""
    i: i32 = 0
    while i < rows:
        j: i32 = 0
        while j < cols:
            m[i][j] = (i * cols + j) % 100
            j = j + 1
        i = i + 1


def matmul(a: list[list[int]], b: list[list[int]], c: list[list[int]], n: i32) -> None:
    """Multiply matrices a and b, store result in c."""
    i: i32 = 0
    while i < n:
        j: i32 = 0
        while j < n:
            total: i32 = 0
            k: i32 = 0
            while k < n:
                total = total + a[i][k] * b[k][j]
                k = k + 1
            c[i][j] = total
            j = j + 1
        i = i + 1


def matrix_sum(m: list[list[int]], n: i32) -> int:
    """Compute sum of all elements (for verification)."""
    total: int = 0  # Use int to avoid i32 overflow
    i: i32 = 0
    while i < n:
        j: i32 = 0
        while j < n:
            total = total + m[i][j]
            j = j + 1
        i = i + 1
    return total


# Benchmark parameters
N: i32 = 100  # Matrix size
ITERATIONS: i32 = 5

# Create matrices
a: list[list[int]] = make_matrix(N, N, 0)
b: list[list[int]] = make_matrix(N, N, 0)
c: list[list[int]] = make_matrix(N, N, 0)

fill_matrix(a, N, N)
fill_matrix(b, N, N)

# Run benchmark
iteration: i32 = 0
while iteration < ITERATIONS:
    matmul(a, b, c, N)
    iteration = iteration + 1

checksum: int = matrix_sum(c, N)  # Use int to avoid i32 overflow
print("Matrix multiply:", checksum)
