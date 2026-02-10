// The Computer Language Benchmarks Game
// http://benchmarksgame.alioth.debian.org/
//
// Zig port (Zig 0.15+)

const std = @import("std");
const posix = std.posix;

fn print(comptime fmt: []const u8, args: anytype) void {
    var buf: [256]u8 = undefined;
    const msg = std.fmt.bufPrint(&buf, fmt, args) catch unreachable;
    _ = posix.write(posix.STDOUT_FILENO, msg) catch {};
}

fn evalA(i: usize, j: usize) f64 {
    const ii: i64 = @intCast(i);
    const jj: i64 = @intCast(j);
    const div = @divFloor((ii + jj) * (ii + jj + 1), 2) + ii + 1;
    return 1.0 / @as(f64, @floatFromInt(div));
}

fn evalATimesU(n: usize, u: []const f64, au: []f64) void {
    for (0..n) |i| {
        au[i] = 0;
        for (0..n) |j| {
            au[i] += evalA(i, j) * u[j];
        }
    }
}

fn evalAtTimesU(n: usize, u: []const f64, au: []f64) void {
    for (0..n) |i| {
        au[i] = 0;
        for (0..n) |j| {
            au[i] += evalA(j, i) * u[j];
        }
    }
}

fn evalAtATimesU(n: usize, u: []const f64, atau: []f64, v: []f64) void {
    evalATimesU(n, u, v);
    evalAtTimesU(n, v, atau);
}

pub fn main() !void {
    var gpa = std.heap.GeneralPurposeAllocator(.{}){};
    defer _ = gpa.deinit();
    const allocator = gpa.allocator();

    var args = std.process.args();
    _ = args.skip();

    const n_str = args.next() orelse "100";
    const n = std.fmt.parseInt(usize, n_str, 10) catch 100;

    const u = try allocator.alloc(f64, n);
    defer allocator.free(u);
    const v = try allocator.alloc(f64, n);
    defer allocator.free(v);
    const tmp = try allocator.alloc(f64, n);
    defer allocator.free(tmp);

    // Initialize u to 1.0
    for (u) |*x| {
        x.* = 1.0;
    }

    // 10 iterations
    for (0..10) |_| {
        evalAtATimesU(n, u, v, tmp);
        evalAtATimesU(n, v, u, tmp);
    }

    var vbv: f64 = 0.0;
    var vv: f64 = 0.0;
    for (0..n) |i| {
        vbv += u[i] * v[i];
        vv += v[i] * v[i];
    }

    print("{d:.9}\n", .{@sqrt(vbv / vv)});
}
