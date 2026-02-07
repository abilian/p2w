"""N-body simulation benchmark.

Simulates the gravitational interaction between bodies in the solar system.
Adapted for p2w (no sys.argv, no dict).
"""

from __future__ import annotations


def combinations(l: list) -> list:
    """Generate all unique pairs from a list."""
    result: list = []
    for x in range(len(l) - 1):
        ls: list = l[x + 1 :]
        for y in ls:
            result.append((l[x], y))
    return result


PI: float = 3.14159265358979323
SOLAR_MASS: float = 4 * PI * PI
DAYS_PER_YEAR: float = 365.24

# Bodies as lists: [position, velocity, mass]
# position and velocity are [x, y, z] lists
sun: list = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], SOLAR_MASS]

jupiter: list = [
    [4.84143144246472090, -1.16032004402742839, -0.103622044471123109],
    [
        1.66007664274403694e-03 * DAYS_PER_YEAR,
        7.69901118419740425e-03 * DAYS_PER_YEAR,
        -6.90460016972063023e-05 * DAYS_PER_YEAR,
    ],
    9.54791938424326609e-04 * SOLAR_MASS,
]

saturn: list = [
    [8.34336671824457987, 4.12479856412430479, -0.403523417114321381],
    [
        -2.76742510726862411e-03 * DAYS_PER_YEAR,
        4.99852801234917238e-03 * DAYS_PER_YEAR,
        2.30417297573763929e-05 * DAYS_PER_YEAR,
    ],
    2.85885980666130812e-04 * SOLAR_MASS,
]

uranus: list = [
    [1.28943695621391310e01, -1.51111514016986312e01, -2.23307578892655734e-01],
    [
        2.96460137564761618e-03 * DAYS_PER_YEAR,
        2.37847173959480950e-03 * DAYS_PER_YEAR,
        -2.96589568540237556e-05 * DAYS_PER_YEAR,
    ],
    4.36624404335156298e-05 * SOLAR_MASS,
]

neptune: list = [
    [1.53796971148509165e01, -2.59193146099879641e01, 1.79258772950371181e-01],
    [
        2.68067772490389322e-03 * DAYS_PER_YEAR,
        1.62824170038242295e-03 * DAYS_PER_YEAR,
        -9.51592254519715870e-05 * DAYS_PER_YEAR,
    ],
    5.15138902046611451e-05 * SOLAR_MASS,
]

BODIES: list = [sun, jupiter, saturn, uranus, neptune]
PAIRS: list = combinations(BODIES)


def advance(dt: float, n: int, bodies: list, pairs: list) -> None:
    """Advance the simulation by n steps of size dt."""
    for i in range(n):
        for pair in pairs:
            b1: list = pair[0]
            b2: list = pair[1]
            r1: list = b1[0]
            r2: list = b2[0]
            v1: list = b1[1]
            v2: list = b2[1]
            m1: float = b1[2]
            m2: float = b2[2]
            dx: float = r1[0] - r2[0]
            dy: float = r1[1] - r2[1]
            dz: float = r1[2] - r2[2]
            dist_sq: float = dx * dx + dy * dy + dz * dz
            dist: float = dist_sq**0.5
            mag: float = dt / (dist_sq * dist)
            b1m: float = m1 * mag
            b2m: float = m2 * mag
            v1[0] = v1[0] - dx * b2m
            v1[1] = v1[1] - dy * b2m
            v1[2] = v1[2] - dz * b2m
            v2[0] = v2[0] + dx * b1m
            v2[1] = v2[1] + dy * b1m
            v2[2] = v2[2] + dz * b1m
        for body in bodies:
            r: list = body[0]
            v: list = body[1]
            r[0] = r[0] + dt * v[0]
            r[1] = r[1] + dt * v[1]
            r[2] = r[2] + dt * v[2]


def report_energy(bodies: list, pairs: list) -> float:
    """Calculate the total energy of the system."""
    e: float = 0.0
    for pair in pairs:
        b1: list = pair[0]
        b2: list = pair[1]
        r1: list = b1[0]
        r2: list = b2[0]
        m1: float = b1[2]
        m2: float = b2[2]
        dx: float = r1[0] - r2[0]
        dy: float = r1[1] - r2[1]
        dz: float = r1[2] - r2[2]
        dist: float = (dx * dx + dy * dy + dz * dz) ** 0.5
        e = e - (m1 * m2) / dist
    for body in bodies:
        v: list = body[1]
        m: float = body[2]
        vx: float = v[0]
        vy: float = v[1]
        vz: float = v[2]
        e = e + m * (vx * vx + vy * vy + vz * vz) / 2.0
    return e


def offset_momentum(bodies: list) -> None:
    """Offset momentum so the system's center of mass is at rest."""
    px: float = 0.0
    py: float = 0.0
    pz: float = 0.0
    for body in bodies:
        v: list = body[1]
        m: float = body[2]
        px = px - v[0] * m
        py = py - v[1] * m
        pz = pz - v[2] * m
    ref: list = bodies[0]
    ref_v: list = ref[1]
    ref_m: float = ref[2]
    ref_v[0] = px / ref_m
    ref_v[1] = py / ref_m
    ref_v[2] = pz / ref_m


def main(n: int) -> None:
    """Run the n-body simulation."""
    offset_momentum(BODIES)
    print(f"{report_energy(BODIES, PAIRS):.9f}")
    advance(0.01, n, BODIES, PAIRS)
    print(f"{report_energy(BODIES, PAIRS):.9f}")


# Benchmark: run 1000 steps
main(1000)
