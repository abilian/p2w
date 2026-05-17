"""Mandelbrot set benchmark - native f64 version.

Counts points in the Mandelbrot set.
Uses f64/i32 annotations for native WASM performance (no boxing).
Mirrors mandelbrot.py exactly; only the types differ.
"""

from __future__ import annotations


def mandelbrot() -> i32:
    count: i32 = 0

    h: f64 = 150.0
    K: f64 = 1.5
    k: f64 = 1.0

    y: f64 = 0.0
    while y < 150.0:
        y = y + 1.0

        x: f64 = 0.0
        while x < 150.0:
            x = x + 1.0
            Z: f64 = 0.0
            z: f64 = 0.0
            T: f64 = 0.0
            t: f64 = 0.0

            C: f64 = (x * 2.0) / h - K
            c: f64 = (y * 2.0) / h - k

            i: f64 = 0.0
            while i < 50.0:
                i = i + 1.0
                if T + t <= 4.0:
                    z = (Z * z) * 2.0 + c
                    Z = T - t + C
                    T = Z * Z
                    t = z * z

            if T + t <= 4.0:
                count = count + 1

    return count


# Run benchmark 10 iterations
ITERATIONS: i32 = 10
EXPECTED: i32 = 8939

for _ in range(ITERATIONS):
    result: i32 = mandelbrot()
    if result != EXPECTED:
        print("ERROR: expected", EXPECTED, "got", result)

print("Mandelbrot:", result)
