"""Spectral Norm benchmark.

Computes the spectral norm of an infinite matrix A.
Adapted for p2w (no sys.argv, no math.sqrt).
"""

from __future__ import annotations


def eval_A(i: int, j: int) -> float:
    """Compute element (i,j) of matrix A."""
    ij: int = i + j
    return 1.0 / (ij * (ij + 1) / 2 + i + 1)


def eval_A_times_u(u: list[float]) -> list[float]:
    """Compute A * u."""
    result: list[float] = []
    n: int = len(u)
    for i in range(n):
        total: float = 0.0
        for j in range(n):
            uj: float = u[j]
            aij: float = eval_A(i, j)
            total = total + aij * uj
        result.append(total)
    return result


def eval_At_times_u(u: list[float]) -> list[float]:
    """Compute A^T * u."""
    result: list[float] = []
    n: int = len(u)
    for i in range(n):
        total: float = 0.0
        for j in range(n):
            uj: float = u[j]
            aji: float = eval_A(j, i)
            total = total + aji * uj
        result.append(total)
    return result


def eval_AtA_times_u(u: list[float]) -> list[float]:
    """Compute A^T * A * u."""
    return eval_At_times_u(eval_A_times_u(u))


def main(n: int) -> None:
    """Run the spectral norm benchmark."""
    u: list[float] = [1.0] * n

    for dummy in range(10):
        v: list[float] = eval_AtA_times_u(u)
        u = eval_AtA_times_u(v)

    vBv: float = 0.0
    vv: float = 0.0

    m: int = len(u)
    for i in range(m):
        ui: float = u[i]
        vi: float = v[i]
        vBv = vBv + ui * vi
        vv = vv + vi * vi

    result: float = (vBv / vv) ** 0.5
    print(f"{result:.9f}")


# Benchmark with n=100
main(100)
