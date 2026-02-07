"""Matrix multiplication benchmark.

Naive O(n^3) matrix multiplication.
Adapted for p2w.
"""

from __future__ import annotations


def make_matrix(rows: int, cols: int, value: int) -> list[list[int]]:
    """Create a rows x cols matrix filled with value."""
    m: list[list[int]] = []
    for i in range(rows):
        row: list[int] = []
        for j in range(cols):
            row.append(value)
        m.append(row)
    return m


def fill_matrix(m: list[list[int]], rows: int, cols: int) -> None:
    """Fill matrix with deterministic values."""
    for i in range(rows):
        for j in range(cols):
            m[i][j] = (i * cols + j) % 100


def matmul(a: list[list[int]], b: list[list[int]], c: list[list[int]], n: int) -> None:
    """Multiply matrices a and b, store result in c."""
    for i in range(n):
        for j in range(n):
            total: int = 0
            for k in range(n):
                total = total + a[i][k] * b[k][j]
            c[i][j] = total


def matrix_sum(m: list[list[int]], n: int) -> int:
    """Compute sum of all elements (for verification)."""
    total: int = 0
    for i in range(n):
        for j in range(n):
            total = total + m[i][j]
    return total


# Benchmark parameters
N: int = 100  # Matrix size
ITERATIONS: int = 5

# Create matrices
a: list[list[int]] = make_matrix(N, N, 0)
b: list[list[int]] = make_matrix(N, N, 0)
c: list[list[int]] = make_matrix(N, N, 0)

fill_matrix(a, N, N)
fill_matrix(b, N, N)

# Run benchmark
for iteration in range(ITERATIONS):
    matmul(a, b, c, N)

checksum: int = matrix_sum(c, N)
print("Matrix multiply:", checksum)
