// The Computer Language Benchmarks Game
// http://benchmarksgame.alioth.debian.org/
//
// Zig port for p2w comparison (Zig 0.15+)

const std = @import("std");
const posix = std.posix;

fn print(comptime fmt: []const u8, args: anytype) void {
    var buf: [256]u8 = undefined;
    const msg = std.fmt.bufPrint(&buf, fmt, args) catch unreachable;
    _ = posix.write(posix.STDOUT_FILENO, msg) catch {};
}

pub fn main() !void {
    var args = std.process.args();
    _ = args.skip();

    const size_str = args.next() orelse "200";
    const size: i32 = std.fmt.parseInt(i32, size_str, 10) catch 200;

    const w = size;
    const h = size;
    const iter: i32 = 50;
    const limit: f64 = 2.0;
    const limit_sq = limit * limit;

    var total_in_set: i32 = 0;

    var y: i32 = 0;
    while (y < h) : (y += 1) {
        var x: i32 = 0;
        while (x < w) : (x += 1) {
            const cr = 2.0 * @as(f64, @floatFromInt(x)) / @as(f64, @floatFromInt(w)) - 1.5;
            const ci = 2.0 * @as(f64, @floatFromInt(y)) / @as(f64, @floatFromInt(h)) - 1.0;

            var zr: f64 = 0.0;
            var zi: f64 = 0.0;
            var tr: f64 = 0.0;
            var ti: f64 = 0.0;

            var i: i32 = 0;
            while (i < iter and (tr + ti <= limit_sq)) : (i += 1) {
                zi = 2.0 * zr * zi + ci;
                zr = tr - ti + cr;
                tr = zr * zr;
                ti = zi * zi;
            }

            if (tr + ti <= limit_sq) {
                total_in_set += 1;
            }
        }
    }

    print("size: {d} in_set: {d}\n", .{ w, total_in_set });
}
