# The Computer Language Benchmarks Game
# http://benchmarksgame.alioth.debian.org/
#
# Contributed by Sebastien Loisel
# Fixed by Isaac Gouy
# Sped up by Josh Goldfoot
# Dirtily sped up by Simon Descarpentries
# Used list comprehension by Vadim Zelenin
# adapted for p2w
#
# Single-threaded version without list comprehensions


def sqrt(x: float) -> float:
    # Newton's method for square root
    if x <= 0.0:
        return 0.0
    guess: float = x / 2.0
    i: int = 0
    while i < 20:
        guess = (guess + x / guess) / 2.0
        i = i + 1
    return guess


def eval_A(i: int, j: int) -> float:
    ij: int = i + j
    return 1.0 / (ij * (ij + 1) / 2 + i + 1)


def eval_A_times_u(u, n: int):
    result = []
    i: int = 0
    while i < n:
        partial_sum: float = 0.0
        j: int = 0
        while j < n:
            partial_sum = partial_sum + eval_A(i, j) * u[j]
            j = j + 1
        result.append(partial_sum)
        i = i + 1
    return result


def eval_At_times_u(u, n: int):
    result = []
    i: int = 0
    while i < n:
        partial_sum: float = 0.0
        j: int = 0
        while j < n:
            partial_sum = partial_sum + eval_A(j, i) * u[j]
            j = j + 1
        result.append(partial_sum)
        i = i + 1
    return result


def eval_AtA_times_u(u, n: int):
    return eval_At_times_u(eval_A_times_u(u, n), n)


def main(n: int) -> None:
    # Initialize u to all 1s
    u = []
    i: int = 0
    while i < n:
        u.append(1.0)
        i = i + 1

    # Power iteration
    dummy: int = 0
    while dummy < 10:
        v = eval_AtA_times_u(u, n)
        u = eval_AtA_times_u(v, n)
        dummy = dummy + 1

    # Compute result
    vBv: float = 0.0
    vv: float = 0.0

    i = 0
    while i < n:
        vBv = vBv + u[i] * v[i]
        vv = vv + v[i] * v[i]
        i = i + 1

    result: float = sqrt(vBv / vv)
    print(result)


# Default argument for testing
main(100)
