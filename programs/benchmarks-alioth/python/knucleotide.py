# The Computer Language Benchmarks Game
# http://benchmarksgame.alioth.debian.org/
#
# adapted for p2w
# Single-threaded version with hardcoded test sequence

# A sample DNA sequence for testing (similar to what would come from stdin)
# In the real benchmark, this would be read from stdin (the >THREE section of fasta output)
TEST_SEQUENCE: str = (
    "GGTATTTTAATTTATAGT"
    "CGATCGATCGATCGATCG"
    "ATCGATCGATCGATCGAT"
    "GGTATTTTAATTTATAGT"
    "AAAAAACCCCCCGGGGGG"
    "TTTTTTAAAAACCCCCGG"
    "GGGGTTTTTAAAACCCCG"
    "GGGTTTTAAAACCCGGGT"
    "TTTAAAACCGGGTTTTAA"
    "AACCCGGGTTTTAAAACG"
) * 100  # Repeat to make it larger for benchmarking


def count_frequencies(sequence: str, frame: int) -> dict[str, int]:
    """Count nucleotide frequencies for a given frame size."""
    counts: dict[str, int] = {}
    seq_len: int = len(sequence)
    i: int = 0
    while i <= seq_len - frame:
        # Use slicing instead of char-by-char building (O(frame) vs O(frame^2))
        subseq: str = sequence[i : i + frame]

        if subseq in counts:
            counts[subseq] = counts[subseq] + 1
        else:
            counts[subseq] = 1
        i = i + 1
    return counts


def sort_by_frequency(counts: dict[str, int]) -> list:
    """Sort counts by frequency (descending) then by key (ascending)."""
    # Convert to list of (key, value) pairs
    items: list = []
    for key in counts:
        items.append((key, counts[key]))

    # Simple bubble sort by value (descending), then key (ascending)
    n: int = len(items)
    i: int = 0
    while i < n:
        j: int = 0
        while j < n - i - 1:
            swap: bool = False
            if items[j][1] < items[j + 1][1]:
                swap = True
            if items[j][1] == items[j + 1][1] and items[j][0] > items[j + 1][0]:
                swap = True
            if swap:
                tmp = items[j]
                items[j] = items[j + 1]
                items[j + 1] = tmp
            j = j + 1
        i = i + 1
    return items


def format_frequencies(counts: dict[str, int], total: int) -> None:
    """Format frequency output."""
    sorted_items: list = sort_by_frequency(counts)
    i: int = 0
    while i < len(sorted_items):
        item = sorted_items[i]
        freq: float = 100.0 * item[1] / total
        print(item[0], freq)
        i = i + 1
    print("")


def count_oligonucleotide(sequence: str, oligo: str) -> int:
    """Count occurrences of a specific oligonucleotide."""
    counts: dict[str, int] = count_frequencies(sequence, len(oligo))
    if oligo in counts:
        return counts[oligo]
    return 0


def main() -> None:
    sequence: str = TEST_SEQUENCE.upper()
    seq_len: int = len(sequence)

    # Output frequencies for 1-mers
    counts1: dict[str, int] = count_frequencies(sequence, 1)
    format_frequencies(counts1, seq_len)

    # Output frequencies for 2-mers
    counts2: dict[str, int] = count_frequencies(sequence, 2)
    format_frequencies(counts2, seq_len - 1)

    # Output counts for specific oligonucleotides
    oligos: list[str] = ["GGT", "GGTA", "GGTATT", "GGTATTTTAATT", "GGTATTTTAATTTATAGT"]
    i: int = 0
    while i < len(oligos):
        oligo: str = oligos[i]
        count: int = count_oligonucleotide(sequence, oligo)
        print(count, oligo)
        i = i + 1


main()
