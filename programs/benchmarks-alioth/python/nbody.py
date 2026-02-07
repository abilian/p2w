# The Computer Language Benchmarks Game
# http://benchmarksgame.alioth.debian.org/
#
# originally by Kevin Carson
# modified by Tupteq, Fredrik Johansson, and Daniel Nanz
# modified by Maciej Fijalkowski
# adapted for p2w
#
# Single-threaded version using lists instead of dicts

PI: float = 3.14159265358979323
SOLAR_MASS: float = 4.0 * PI * PI
DAYS_PER_YEAR: float = 365.24


def sqrt(x: float) -> float:
    # Newton's method for square root
    if x <= 0.0:
        return 0.0
    guess: float = x / 2.0
    i: int = 0
    while i < 20:
        guess = (guess + x / guess) / 2.0
        i = i + 1
    return guess


def make_bodies():
    # Returns list of [x, y, z, vx, vy, vz, mass]
    # sun
    sun = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, SOLAR_MASS]

    # jupiter
    jupiter = [
        4.84143144246472090e00,
        -1.16032004402742839e00,
        -1.03622044471123109e-01,
        1.66007664274403694e-03 * DAYS_PER_YEAR,
        7.69901118419740425e-03 * DAYS_PER_YEAR,
        -6.90460016972063023e-05 * DAYS_PER_YEAR,
        9.54791938424326609e-04 * SOLAR_MASS,
    ]

    # saturn
    saturn = [
        8.34336671824457987e00,
        4.12479856412430479e00,
        -4.03523417114321381e-01,
        -2.76742510726862411e-03 * DAYS_PER_YEAR,
        4.99852801234917238e-03 * DAYS_PER_YEAR,
        2.30417297573763929e-05 * DAYS_PER_YEAR,
        2.85885980666130812e-04 * SOLAR_MASS,
    ]

    # uranus
    uranus = [
        1.28943695621391310e01,
        -1.51111514016986312e01,
        -2.23307578892655734e-01,
        2.96460137564761618e-03 * DAYS_PER_YEAR,
        2.37847173959480950e-03 * DAYS_PER_YEAR,
        -2.96589568540237556e-05 * DAYS_PER_YEAR,
        4.36624404335156298e-05 * SOLAR_MASS,
    ]

    # neptune
    neptune = [
        1.53796971148509165e01,
        -2.59193146099879641e01,
        1.79258772950371181e-01,
        2.68067772490389322e-03 * DAYS_PER_YEAR,
        1.62824170038242295e-03 * DAYS_PER_YEAR,
        -9.51592254519715870e-05 * DAYS_PER_YEAR,
        5.15138902046611451e-05 * SOLAR_MASS,
    ]

    return [sun, jupiter, saturn, uranus, neptune]


def make_pairs(bodies):
    # Create all pairs of bodies
    pairs = []
    n: int = len(bodies)
    i: int = 0
    while i < n - 1:
        j: int = i + 1
        while j < n:
            pairs.append((bodies[i], bodies[j]))
            j = j + 1
        i = i + 1
    return pairs


def advance(dt: float, n: int, bodies, pairs) -> None:
    i: int = 0
    while i < n:
        # Update velocities from pairs
        j: int = 0
        while j < len(pairs):
            pair = pairs[j]
            b1 = pair[0]
            b2 = pair[1]

            dx: float = b1[0] - b2[0]
            dy: float = b1[1] - b2[1]
            dz: float = b1[2] - b2[2]

            dist_sq: float = dx * dx + dy * dy + dz * dz
            dist: float = sqrt(dist_sq)
            mag: float = dt / (dist_sq * dist)

            m1: float = b1[6]
            m2: float = b2[6]

            b1[3] = b1[3] - dx * m2 * mag
            b1[4] = b1[4] - dy * m2 * mag
            b1[5] = b1[5] - dz * m2 * mag

            b2[3] = b2[3] + dx * m1 * mag
            b2[4] = b2[4] + dy * m1 * mag
            b2[5] = b2[5] + dz * m1 * mag

            j = j + 1

        # Update positions
        k: int = 0
        while k < len(bodies):
            b = bodies[k]
            b[0] = b[0] + dt * b[3]
            b[1] = b[1] + dt * b[4]
            b[2] = b[2] + dt * b[5]
            k = k + 1

        i = i + 1


def report_energy(bodies, pairs) -> None:
    e: float = 0.0

    # Kinetic energy
    i: int = 0
    while i < len(bodies):
        b = bodies[i]
        vx: float = b[3]
        vy: float = b[4]
        vz: float = b[5]
        m: float = b[6]
        e = e + m * (vx * vx + vy * vy + vz * vz) / 2.0
        i = i + 1

    # Potential energy
    j: int = 0
    while j < len(pairs):
        pair = pairs[j]
        b1 = pair[0]
        b2 = pair[1]

        dx: float = b1[0] - b2[0]
        dy: float = b1[1] - b2[1]
        dz: float = b1[2] - b2[2]

        dist: float = sqrt(dx * dx + dy * dy + dz * dz)
        e = e - (b1[6] * b2[6]) / dist
        j = j + 1

    print(e)


def offset_momentum(bodies) -> None:
    px: float = 0.0
    py: float = 0.0
    pz: float = 0.0

    i: int = 0
    while i < len(bodies):
        b = bodies[i]
        m: float = b[6]
        px = px - b[3] * m
        py = py - b[4] * m
        pz = pz - b[5] * m
        i = i + 1

    sun = bodies[0]
    sun[3] = px / SOLAR_MASS
    sun[4] = py / SOLAR_MASS
    sun[5] = pz / SOLAR_MASS


def main(n: int) -> None:
    bodies = make_bodies()
    pairs = make_pairs(bodies)

    offset_momentum(bodies)
    report_energy(bodies, pairs)
    advance(0.01, n, bodies, pairs)
    report_energy(bodies, pairs)


# Default argument for testing
main(1000)
