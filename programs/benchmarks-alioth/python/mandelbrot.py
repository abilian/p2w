# The Computer Language Benchmarks Game
# http://benchmarksgame.alioth.debian.org/
#
# contributed by Tupteq
# modified for single-threaded p2w
#
# This version outputs to stdout but doesn't produce actual PBM image
# It focuses on the computation for benchmarking purposes


def main(size: int) -> None:
    fsize: float = float(size)

    # Just count iterations (for benchmarking without I/O)
    total_in_set: int = 0

    y: i32 = 0
    while y < size:
        fy: float = 2.0 * y / fsize - 1.0

        x: i32 = 0
        while x < size:
            # Complex number c = (cr, ci)
            cr: float = 2.0 * x / fsize - 1.5
            ci: float = fy

            # z = 0
            zr: float = 0.0
            zi: float = 0.0

            # Iterate z = z*z + c
            iter: i32 = 0
            in_set: int = 1
            while iter < 50:
                # z*z = (zr + zi*i)^2 = zr^2 - zi^2 + 2*zr*zi*i
                zr2: float = zr * zr
                zi2: float = zi * zi

                # Check if |z|^2 > 4
                if zr2 + zi2 > 4.0:
                    in_set = 0
                    iter = 50  # break

                # z = z*z + c
                zi = 2.0 * zr * zi + ci
                zr = zr2 - zi2 + cr

                iter = iter + 1

            total_in_set = total_in_set + in_set
            x = x + 1

        y = y + 1

    # Output total count for verification
    print("size:", size, "in_set:", total_in_set)


# Default argument for testing
main(200)
