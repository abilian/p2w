"""FASTA benchmark.

Generates DNA sequences using various algorithms.
Adapted for p2w (no generators, no bisect).
"""

from __future__ import annotations

ALU: str = (
    "GGCCGGGCGCGGTGGCTCACGCCTGTAATCCCAGCACTTTGG"
    "GAGGCCGAGGCGGGCGGATCACCTGAGGTCAGGAGTTCGAGA"
    "CCAGCCTGGCCAACATGGTGAAACCCCGTCTCTACTAAAAAT"
    "ACAAAAATTAGCCGGGCGTGGTGGCGCGCGCCTGTAATCCCA"
    "GCTACTCGGGAGGCTGAGGCAGGAGAATCGCTTGAACCCGGG"
    "AGGCGGAGGTTGCAGTGAGCCGAGATCGCGCCACTGCACTCC"
    "AGCCTGGGCGACAGAGCGAGACTCCGTCTCAAAAA"
)

# Random number generator state
random_seed: int = 42
IA: int = 3877
IC: int = 29573
IM: int = 139968
IMF: float = 139968.0


def gen_random() -> float:
    global random_seed
    random_seed = (random_seed * IA + IC) % IM
    return random_seed / IMF


def make_cumulative(table: list) -> tuple:
    """Convert probability table to cumulative probabilities."""
    probs: list[float] = []
    chars: list[str] = []
    cumul: float = 0.0
    for pair in table:
        char: str = pair[0]
        prob: float = pair[1]
        cumul = cumul + prob
        probs.append(cumul)
        chars.append(char)
    return probs, chars


def bisect_search(probs: list[float], val: float) -> int:
    """Find index where val would be inserted to keep probs sorted."""
    lo: int = 0
    hi: int = len(probs)
    while lo < hi:
        mid: int = (lo + hi) // 2
        if probs[mid] < val:
            lo = mid + 1
        else:
            hi = mid
    return lo


def repeat_fasta(src: str, n: int) -> None:
    """Generate repeated sequence."""
    width: int = 60
    r: int = len(src)
    # Create extended source
    s: str = src + src + src

    j: int = 0
    while j < n // width:
        i: int = j * width % r
        line: str = ""
        for k in range(width):
            line = line + s[i + k]
        print(line)
        j = j + 1

    remainder: int = n % width
    if remainder > 0:
        start: int = (n // width * width) % r
        line2: str = ""
        for k in range(remainder):
            line2 = line2 + s[start + k]
        print(line2)


def random_fasta(table: list, n: int) -> None:
    """Generate random sequence based on probability table."""
    width: int = 60
    probs: list[float]
    chars: list[str]
    probs, chars = make_cumulative(table)

    j: int = 0
    while j < n // width:
        line: str = ""
        for i in range(width):
            r: float = gen_random()
            idx: int = bisect_search(probs, r)
            line = line + chars[idx]
        print(line)
        j = j + 1

    remainder: int = n % width
    if remainder > 0:
        line2: str = ""
        for i in range(remainder):
            r2: float = gen_random()
            idx2: int = bisect_search(probs, r2)
            line2 = line2 + chars[idx2]
        print(line2)


def main(n: int) -> None:
    # Homo sapiens frequency table
    homosapiens: list = [
        ("a", 0.3029549426680),
        ("c", 0.1979883004921),
        ("g", 0.1975473066391),
        ("t", 0.3015094502008),
    ]

    print(">ONE Homo sapiens alu")
    repeat_fasta(ALU, n * 2)

    print(">THREE Homo sapiens frequency")
    random_fasta(homosapiens, n * 5)


# Benchmark with n=25000 (matching alioth)
main(25000)
