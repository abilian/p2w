"""Mandelbrot set benchmark.

Counts points in the Mandelbrot set.
Adapted for p2w.
"""

from __future__ import annotations


def mandelbrot() -> int:
    count: int = 0

    h: float = 150.0
    K: float = 1.5
    k: float = 1.0

    y: float = 0.0
    while y < 150:
        y = y + 1

        x: float = 0.0
        while x < 150:
            x = x + 1
            Z: float = 0.0
            z: float = 0.0
            T: float = 0.0
            t: float = 0.0

            C: float = (x * 2) / h - K
            c: float = (y * 2) / h - k

            i: float = 0.0
            while i < 50:
                i = i + 1
                if T + t <= 4:
                    z = (Z * z) * 2 + c
                    Z = T - t + C
                    T = Z * Z
                    t = z * z

            if T + t <= 4:
                count = count + 1

    return count


# Run benchmark 10 iterations
ITERATIONS: int = 10
EXPECTED: int = 8939

for i in range(ITERATIONS):
    result: int = mandelbrot()
    if result != EXPECTED:
        print("ERROR: expected", EXPECTED, "got", result)

print("Mandelbrot:", result)
