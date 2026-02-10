# The Computer Language Benchmarks Game
# http://benchmarksgame.alioth.debian.org/
#
# contributed by Miroslav Rubanets
# adapted for  single-threaded p2w
#
# Simple fannkuch-redux implementation


def fannkuch(n: int) -> None:
    # Initialize permutation
    perm: list[int] = []
    i: i32 = 0
    while i < n:
        perm.append(i)
        i = i + 1

    # Initialize count
    count: list[int] = []
    i = 0
    while i < n:
        count.append(0)
        i = i + 1

    max_flips: int = 0
    checksum: int = 0
    sign: int = 1

    perm_count: int = 0
    m: int = n - 1

    # Copy for permutation work
    perm1: list[int] = []
    i = 0
    while i < n:
        perm1.append(i)
        i = i + 1

    while True:
        # Copy perm1 to perm
        i = 0
        while i < n:
            perm[i] = perm1[i]
            i = i + 1

        # Count flips
        k: int = perm[0]
        if k != 0:
            flips: int = 0
            while k != 0:
                # Reverse perm[0:k+1]
                lo: i32 = 0
                hi: int = k
                while lo < hi:
                    tmp: int = perm[lo]
                    perm[lo] = perm[hi]
                    perm[hi] = tmp
                    lo = lo + 1
                    hi = hi - 1
                flips = flips + 1
                k = perm[0]

            if flips > max_flips:
                max_flips = flips
            checksum = checksum + sign * flips

        sign = 0 - sign

        # Generate next permutation
        # Rotate perm1
        tmp: int = perm1[1]
        perm1[1] = perm1[0]
        perm1[0] = tmp

        i = 1
        count[i] = count[i] + 1
        while count[i] > i:
            count[i] = 0
            i = i + 1
            if i >= n:
                print(checksum)
                print("Pfannkuchen(" + str(n) + ") =", max_flips)
                return

            # Rotate perm1[0:i+1]
            tmp = perm1[0]
            j: i32 = 0
            while j < i:
                perm1[j] = perm1[j + 1]
                j = j + 1
            perm1[i] = tmp

            count[i] = count[i] + 1


def main(n: int) -> None:
    fannkuch(n)


# Default argument for testing
main(7)
