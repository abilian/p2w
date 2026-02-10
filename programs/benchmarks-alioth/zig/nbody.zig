// The Computer Language Benchmarks Game
// http://benchmarksgame.alioth.debian.org/
//
// Zig port (Zig 0.15+)

const std = @import("std");
const posix = std.posix;

const pi = 3.141592653589793;
const solar_mass = 4.0 * pi * pi;
const days_per_year = 365.24;

const Planet = struct {
    x: f64,
    y: f64,
    z: f64,
    vx: f64,
    vy: f64,
    vz: f64,
    mass: f64,
};

fn print(comptime fmt: []const u8, args: anytype) void {
    var buf: [256]u8 = undefined;
    const msg = std.fmt.bufPrint(&buf, fmt, args) catch unreachable;
    _ = posix.write(posix.STDOUT_FILENO, msg) catch {};
}

fn advance(bodies: []Planet, dt: f64) void {
    for (bodies, 0..) |*b, i| {
        for (bodies[i + 1 ..]) |*b2| {
            const dx = b.x - b2.x;
            const dy = b.y - b2.y;
            const dz = b.z - b2.z;
            const dist_sq = dx * dx + dy * dy + dz * dz;
            const distance = @sqrt(dist_sq);
            const mag = dt / (dist_sq * distance);

            b.vx -= dx * b2.mass * mag;
            b.vy -= dy * b2.mass * mag;
            b.vz -= dz * b2.mass * mag;
            b2.vx += dx * b.mass * mag;
            b2.vy += dy * b.mass * mag;
            b2.vz += dz * b.mass * mag;
        }
    }

    for (bodies) |*b| {
        b.x += dt * b.vx;
        b.y += dt * b.vy;
        b.z += dt * b.vz;
    }
}

fn energy(bodies: []const Planet) f64 {
    var e: f64 = 0.0;

    for (bodies, 0..) |b, i| {
        e += 0.5 * b.mass * (b.vx * b.vx + b.vy * b.vy + b.vz * b.vz);

        for (bodies[i + 1 ..]) |b2| {
            const dx = b.x - b2.x;
            const dy = b.y - b2.y;
            const dz = b.z - b2.z;
            const distance = @sqrt(dx * dx + dy * dy + dz * dz);
            e -= (b.mass * b2.mass) / distance;
        }
    }

    return e;
}

fn offsetMomentum(bodies: []Planet) void {
    var px: f64 = 0.0;
    var py: f64 = 0.0;
    var pz: f64 = 0.0;

    for (bodies) |b| {
        px += b.vx * b.mass;
        py += b.vy * b.mass;
        pz += b.vz * b.mass;
    }

    bodies[0].vx = -px / solar_mass;
    bodies[0].vy = -py / solar_mass;
    bodies[0].vz = -pz / solar_mass;
}

pub fn main() !void {
    var args = std.process.args();
    _ = args.skip();

    const n_str = args.next() orelse "1000";
    const n = std.fmt.parseInt(i32, n_str, 10) catch 1000;

    var bodies = [_]Planet{
        // Sun
        .{ .x = 0, .y = 0, .z = 0, .vx = 0, .vy = 0, .vz = 0, .mass = solar_mass },
        // Jupiter
        .{
            .x = 4.84143144246472090e+00,
            .y = -1.16032004402742839e+00,
            .z = -1.03622044471123109e-01,
            .vx = 1.66007664274403694e-03 * days_per_year,
            .vy = 7.69901118419740425e-03 * days_per_year,
            .vz = -6.90460016972063023e-05 * days_per_year,
            .mass = 9.54791938424326609e-04 * solar_mass,
        },
        // Saturn
        .{
            .x = 8.34336671824457987e+00,
            .y = 4.12479856412430479e+00,
            .z = -4.03523417114321381e-01,
            .vx = -2.76742510726862411e-03 * days_per_year,
            .vy = 4.99852801234917238e-03 * days_per_year,
            .vz = 2.30417297573763929e-05 * days_per_year,
            .mass = 2.85885980666130812e-04 * solar_mass,
        },
        // Uranus
        .{
            .x = 1.28943695621391310e+01,
            .y = -1.51111514016986312e+01,
            .z = -2.23307578892655734e-01,
            .vx = 2.96460137564761618e-03 * days_per_year,
            .vy = 2.37847173959480950e-03 * days_per_year,
            .vz = -2.96589568540237556e-05 * days_per_year,
            .mass = 4.36624404335156298e-05 * solar_mass,
        },
        // Neptune
        .{
            .x = 1.53796971148509165e+01,
            .y = -2.59193146099879641e+01,
            .z = 1.79258772950371181e-01,
            .vx = 2.68067772490389322e-03 * days_per_year,
            .vy = 1.62824170038242295e-03 * days_per_year,
            .vz = -9.51592254519715870e-05 * days_per_year,
            .mass = 5.15138902046611451e-05 * solar_mass,
        },
    };

    offsetMomentum(&bodies);

    print("{d:.9}\n", .{energy(&bodies)});

    var i: i32 = 0;
    while (i < n) : (i += 1) {
        advance(&bodies, 0.01);
    }

    print("{d:.9}\n", .{energy(&bodies)});
}
