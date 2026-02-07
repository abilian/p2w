# The Computer Language Benchmarks Game
# http://benchmarksgame.alioth.debian.org/
#
# adapted for p2w
# Single-threaded version with hardcoded test sequence

# A sample DNA sequence for testing (similar to what would come from stdin)
# In the real benchmark, this would be read from stdin (the >THREE section of fasta output)
TEST_SEQUENCE = (
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


def count_frequencies(sequence, frame):
    """Count nucleotide frequencies for a given frame size."""
    counts = {}
    seq_len = len(sequence)
    i = 0
    while i <= seq_len - frame:
        # Use slicing instead of char-by-char building (O(frame) vs O(frame^2))
        subseq = sequence[i : i + frame]

        if subseq in counts:
            counts[subseq] = counts[subseq] + 1
        else:
            counts[subseq] = 1
        i = i + 1
    return counts


def sort_by_frequency(counts):
    """Sort counts by frequency (descending) then by key (ascending)."""
    # Convert to list of (key, value) pairs
    items = []
    for key in counts:
        items.append((key, counts[key]))

    # Simple bubble sort by value (descending), then key (ascending)
    n = len(items)
    i = 0
    while i < n:
        j = 0
        while j < n - i - 1:
            swap = False
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


def format_frequencies(counts, total):
    """Format frequency output."""
    sorted_items = sort_by_frequency(counts)
    i = 0
    while i < len(sorted_items):
        item = sorted_items[i]
        freq = 100.0 * item[1] / total
        print(item[0], freq)
        i = i + 1
    print("")


def count_oligonucleotide(sequence, oligo):
    """Count occurrences of a specific oligonucleotide."""
    counts = count_frequencies(sequence, len(oligo))
    if oligo in counts:
        return counts[oligo]
    return 0


def main():
    sequence = TEST_SEQUENCE.upper()
    seq_len = len(sequence)

    # Output frequencies for 1-mers
    counts1 = count_frequencies(sequence, 1)
    format_frequencies(counts1, seq_len)

    # Output frequencies for 2-mers
    counts2 = count_frequencies(sequence, 2)
    format_frequencies(counts2, seq_len - 1)

    # Output counts for specific oligonucleotides
    oligos = ["GGT", "GGTA", "GGTATT", "GGTATTTTAATT", "GGTATTTTAATTTATAGT"]
    i = 0
    while i < len(oligos):
        oligo = oligos[i]
        count = count_oligonucleotide(sequence, oligo)
        print(count, oligo)
        i = i + 1


main()
