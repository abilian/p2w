# The Computer Language Benchmarks Game
# http://benchmarksgame.alioth.debian.org/
#
# adapted for p2w
# Single-threaded version without generators or bisect

# ALU sequence
ALU: str = (
    "GGCCGGGCGCGGTGGCTCACGCCTGTAATCCCAGCACTTTGG"
    "GAGGCCGAGGCGGGCGGATCACCTGAGGTCAGGAGTTCGAGA"
    "CCAGCCTGGCCAACATGGTGAAACCCCGTCTCTACTAAAAAT"
    "ACAAAAATTAGCCGGGCGTGGTGGCGCGCGCCTGTAATCCCA"
    "GCTACTCGGGAGGCTGAGGCAGGAGAATCGCTTGAACCCGGG"
    "AGGCGGAGGTTGCAGTGAGCCGAGATCGCGCCACTGCACTCC"
    "AGCCTGGGCGACAGAGCGAGACTCCGTCTCAAAAA"
)

# Random number generator state (mutable list to allow modification)
RANDOM_SEED: list[int] = [42]
IM: int = 139968
IA: int = 3877
IC: int = 29573


def gen_random() -> float:
    """Linear congruential generator."""
    RANDOM_SEED[0] = (RANDOM_SEED[0] * IA + IC) % IM
    return RANDOM_SEED[0] / IM


def make_cumulative(table: list) -> tuple[list[float], list[str]]:
    """Convert probability table to cumulative probabilities."""
    probs: list[float] = []
    chars: list[str] = []
    cp: float = 0.0
    i: int = 0
    while i < len(table):
        pair = table[i]
        cp = cp + pair[1]
        probs.append(cp)
        chars.append(pair[0])
        i = i + 1
    return (probs, chars)


def select_random(probs: list[float], chars: list[str]) -> str:
    """Select a character based on cumulative probabilities."""
    r: float = gen_random()
    # Linear search (simple and works for small tables)
    i: int = 0
    while i < len(probs):
        if r < probs[i]:
            return chars[i]
        i = i + 1
    return chars[len(chars) - 1]


def repeat_fasta(src: str, n: int) -> None:
    """Generate repeating sequence."""
    width: int = 60
    src_len: int = len(src)
    # Create extended source for direct slicing (3x is enough for any width)
    extended: str = src + src + src

    pos: int = 0
    remaining: int = n
    while remaining > 0:
        line_len: int = 0
        if remaining < width:
            line_len = remaining
        else:
            line_len = width

        # Use slicing instead of char-by-char building (O(W) vs O(W^2))
        line: str = extended[pos : pos + line_len]

        print(line)
        pos = (pos + line_len) % src_len
        remaining = remaining - line_len


def random_fasta(table: list, n: int) -> None:
    """Generate random sequence based on probability table."""
    width: int = 60
    probs: list[float]
    chars: list[str]
    probs, chars = make_cumulative(table)

    remaining: int = n
    while remaining > 0:
        line_len: int = 0
        if remaining < width:
            line_len = remaining
        else:
            line_len = width

        # Build line using list+join pattern (O(W) instead of O(W²))
        line_parts: list[str] = []
        i: int = 0
        while i < line_len:
            line_parts.append(select_random(probs, chars))
            i = i + 1
        line: str = "".join(line_parts)

        print(line)
        remaining = remaining - line_len


def main(n: int) -> None:
    # IUB ambiguity codes
    iub: list = [
        ("a", 0.27),
        ("c", 0.12),
        ("g", 0.12),
        ("t", 0.27),
        ("B", 0.02),
        ("D", 0.02),
        ("H", 0.02),
        ("K", 0.02),
        ("M", 0.02),
        ("N", 0.02),
        ("R", 0.02),
        ("S", 0.02),
        ("V", 0.02),
        ("W", 0.02),
        ("Y", 0.02),
    ]

    # Homo sapiens frequency
    homosapiens: list = [
        ("a", 0.3029549426680),
        ("c", 0.1979883004921),
        ("g", 0.1975473066391),
        ("t", 0.3015094502008),
    ]

    print(">ONE Homo sapiens alu")
    repeat_fasta(ALU, n * 2)

    print(">TWO IUB ambiguity codes")
    random_fasta(iub, n * 3)

    print(">THREE Homo sapiens frequency")
    random_fasta(homosapiens, n * 5)


# Default argument for testing
main(1000)
