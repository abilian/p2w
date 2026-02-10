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

fn fannkuchredux(n: usize) !struct { checksum: i32, max_flips: i32 } {
    var gpa = std.heap.GeneralPurposeAllocator(.{}){};
    defer _ = gpa.deinit();
    const allocator = gpa.allocator();

    const perm = try allocator.alloc(i32, n);
    defer allocator.free(perm);
    const perm1 = try allocator.alloc(i32, n);
    defer allocator.free(perm1);
    const count = try allocator.alloc(i32, n);
    defer allocator.free(count);

    var max_flips_count: i32 = 0;
    var perm_count: i32 = 0;
    var checksum: i32 = 0;

    for (0..n) |i| {
        perm1[i] = @intCast(i);
    }

    var r: usize = n;

    outer: while (true) {
        while (r != 1) {
            count[r - 1] = @intCast(r);
            r -= 1;
        }

        for (0..n) |i| {
            perm[i] = perm1[i];
        }

        var flips_count: i32 = 0;

        while (true) {
            const k: usize = @intCast(perm[0]);
            if (k == 0) break;

            const k2 = (k + 1) >> 1;
            for (0..k2) |i| {
                const temp = perm[i];
                perm[i] = perm[k - i];
                perm[k - i] = temp;
            }
            flips_count += 1;
        }

        max_flips_count = @max(max_flips_count, flips_count);
        if (@mod(perm_count, 2) == 0) {
            checksum += flips_count;
        } else {
            checksum -= flips_count;
        }

        while (true) {
            if (r == n) {
                return .{ .checksum = checksum, .max_flips = max_flips_count };
            }

            const perm0 = perm1[0];
            var i: usize = 0;
            while (i < r) {
                const j = i + 1;
                perm1[i] = perm1[j];
                i = j;
            }
            perm1[r] = perm0;
            count[r] -= 1;
            if (count[r] > 0) break;
            r += 1;
        }
        perm_count += 1;
        continue :outer;
    }
}

pub fn main() !void {
    var args = std.process.args();
    _ = args.skip();

    const n_str = args.next() orelse "7";
    const n = std.fmt.parseInt(usize, n_str, 10) catch 7;

    const result = try fannkuchredux(n);

    print("{d}\n", .{result.checksum});
    print("Pfannkuchen({d}) = {d}\n", .{ n, result.max_flips });
}
