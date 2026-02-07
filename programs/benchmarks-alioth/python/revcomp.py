# The Computer Language Benchmarks Game
# http://benchmarksgame.alioth.debian.org/
#
# adapted for p2w
# Single-threaded version with hardcoded test sequence

# Complement table
COMPLEMENT = {
    "A": "T",
    "T": "A",
    "C": "G",
    "G": "C",
    "a": "T",
    "t": "A",
    "c": "G",
    "g": "C",
    "B": "V",
    "V": "B",
    "D": "H",
    "H": "D",
    "K": "M",
    "M": "K",
    "N": "N",
    "R": "Y",
    "Y": "R",
    "S": "S",
    "W": "W",
    "U": "A",
    "b": "V",
    "v": "B",
    "d": "H",
    "h": "D",
    "k": "M",
    "m": "K",
    "n": "N",
    "r": "Y",
    "y": "R",
    "s": "S",
    "w": "W",
    "u": "A",
}

# Sample FASTA input (normally would come from stdin)
FASTA_INPUT = """>ONE Homo sapiens alu
GGCCGGGCGCGGTGGCTCACGCCTGTAATCCCAGCACTTTGGGAGGCCGAGGCGGGCGGA
TCACCTGAGGTCAGGAGTTCGAGACCAGCCTGGCCAACATGGTGAAACCCCGTCTCTACT
AAAAATACAAAAATTAGCCGGGCGTGGTGGCGCGCGCCTGTAATCCCAGCTACTCGGGAG
GCTGAGGCAGGAGAATCGCTTGAACCCGGGAGGCGGAGGTTGCAGTGAGCCGAGATCGCG
CCACTGCACTCCAGCCTGGGCGACAGAGCGAGACTCCGTCTCAAAAA
>TWO IUB ambiguity codes
TAGGDHACHATCRYGMKWSYYBVNN
>THREE Homo sapiens frequency
ATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGC
"""


def reverse_complement(sequence):
    """Compute reverse complement of a DNA sequence."""
    # Reverse the string using slice (O(N) with memory.copy)
    reversed_seq = sequence[::-1]

    # Build complement using list+join pattern (O(N) instead of O(N²))
    result_parts = []
    i = 0
    while i < len(reversed_seq):
        base = reversed_seq[i]
        if base in COMPLEMENT:
            result_parts.append(COMPLEMENT[base])
        else:
            result_parts.append(base)
        i = i + 1

    return "".join(result_parts)


def format_sequence(seq, width):
    """Format sequence with line breaks."""
    i = 0
    while i < len(seq):
        end = i + width
        if end > len(seq):
            end = len(seq)
        # Use slicing instead of char-by-char building (O(W) vs O(W^2))
        line = seq[i:end]
        print(line)
        i = i + width


def process_fasta(fasta_input):
    """Process FASTA input and output reverse complements."""
    lines = fasta_input.split("\n")
    header = ""
    sequence_parts = []

    i = 0
    while i < len(lines):
        line = lines[i]
        if len(line) > 0:
            if line[0] == ">":
                # Output previous sequence if exists
                if len(sequence_parts) > 0:
                    print(header)
                    sequence = "".join(sequence_parts)
                    rc = reverse_complement(sequence)
                    format_sequence(rc, 60)
                    sequence_parts = []
                header = line
            else:
                sequence_parts.append(line)
        i = i + 1

    # Output last sequence
    if len(sequence_parts) > 0:
        print(header)
        sequence = "".join(sequence_parts)
        rc = reverse_complement(sequence)
        format_sequence(rc, 60)


def main():
    # Process the test input multiple times for benchmarking
    fasta_repeated = FASTA_INPUT * 10
    process_fasta(fasta_repeated)


main()
