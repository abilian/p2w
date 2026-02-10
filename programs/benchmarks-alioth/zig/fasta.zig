// The Computer Language Benchmarks Game
// http://benchmarksgame.alioth.debian.org/
//
// Zig port (Zig 0.15+)

const std = @import("std");
const posix = std.posix;

const IM: u32 = 139968;
const IA: u32 = 3877;
const IC: u32 = 29573;
const LINE_LENGTH: usize = 60;

var last_random: u32 = 42;

fn print(comptime fmt: []const u8, args: anytype) void {
    var buf: [256]u8 = undefined;
    const msg = std.fmt.bufPrint(&buf, fmt, args) catch unreachable;
    _ = posix.write(posix.STDOUT_FILENO, msg) catch {};
}

fn writeBytes(bytes: []const u8) void {
    _ = posix.write(posix.STDOUT_FILENO, bytes) catch {};
}

fn genRandom(max: f64) f64 {
    last_random = (last_random * IA + IC) % IM;
    return max * @as(f64, @floatFromInt(last_random)) / @as(f64, @floatFromInt(IM));
}

const AminoAcid = struct {
    c: u8,
    p: f64,
};

fn makeCumulative(genelist: []AminoAcid) void {
    var cp: f64 = 0.0;
    for (genelist) |*g| {
        cp += g.p;
        g.p = cp;
    }
}

fn selectRandom(genelist: []const AminoAcid) u8 {
    const r = genRandom(1.0);

    if (r < genelist[0].p) return genelist[0].c;

    var lo: usize = 0;
    var hi: usize = genelist.len - 1;

    while (hi > lo + 1) {
        const i = (hi + lo) / 2;
        if (r < genelist[i].p) {
            hi = i;
        } else {
            lo = i;
        }
    }
    return genelist[hi].c;
}

fn makeRandomFasta(id: []const u8, desc: []const u8, genelist: []const AminoAcid, n: usize) void {
    print(">{s} {s}\n", .{ id, desc });

    var pick: [LINE_LENGTH + 1]u8 = undefined;
    var todo = n;

    while (todo > 0) {
        const m = if (todo < LINE_LENGTH) todo else LINE_LENGTH;

        for (0..m) |i| {
            pick[i] = selectRandom(genelist);
        }
        pick[m] = '\n';
        writeBytes(pick[0 .. m + 1]);

        todo -= m;
    }
}

fn makeRepeatFasta(id: []const u8, desc: []const u8, s: []const u8, n: usize) void {
    print(">{s} {s}\n", .{ id, desc });

    const kn = s.len;
    var line: [LINE_LENGTH + 1]u8 = undefined;
    var k: usize = 0;
    var todo = n;

    while (todo > 0) {
        var m = if (todo < LINE_LENGTH) todo else LINE_LENGTH;
        var pos: usize = 0;

        while (m > 0) {
            const chunk = if (kn - k < m) kn - k else m;
            for (0..chunk) |i| {
                line[pos + i] = s[k + i];
            }
            pos += chunk;
            m -= chunk;
            k += chunk;
            if (k >= kn) k = 0;
        }

        line[pos] = '\n';
        writeBytes(line[0 .. pos + 1]);
        todo -= if (todo < LINE_LENGTH) todo else LINE_LENGTH;
    }
}

pub fn main() !void {
    var args = std.process.args();
    _ = args.skip();

    const n_str = args.next() orelse "1000";
    const n = std.fmt.parseInt(usize, n_str, 10) catch 1000;

    var iub = [_]AminoAcid{
        .{ .c = 'a', .p = 0.27 },
        .{ .c = 'c', .p = 0.12 },
        .{ .c = 'g', .p = 0.12 },
        .{ .c = 't', .p = 0.27 },
        .{ .c = 'B', .p = 0.02 },
        .{ .c = 'D', .p = 0.02 },
        .{ .c = 'H', .p = 0.02 },
        .{ .c = 'K', .p = 0.02 },
        .{ .c = 'M', .p = 0.02 },
        .{ .c = 'N', .p = 0.02 },
        .{ .c = 'R', .p = 0.02 },
        .{ .c = 'S', .p = 0.02 },
        .{ .c = 'V', .p = 0.02 },
        .{ .c = 'W', .p = 0.02 },
        .{ .c = 'Y', .p = 0.02 },
    };

    var homosapiens = [_]AminoAcid{
        .{ .c = 'a', .p = 0.3029549426680 },
        .{ .c = 'c', .p = 0.1979883004921 },
        .{ .c = 'g', .p = 0.1975473066391 },
        .{ .c = 't', .p = 0.3015094502008 },
    };

    const alu =
        "GGCCGGGCGCGGTGGCTCACGCCTGTAATCCCAGCACTTTGG" ++
        "GAGGCCGAGGCGGGCGGATCACCTGAGGTCAGGAGTTCGAGA" ++
        "CCAGCCTGGCCAACATGGTGAAACCCCGTCTCTACTAAAAAT" ++
        "ACAAAAATTAGCCGGGCGTGGTGGCGCGCGCCTGTAATCCCA" ++
        "GCTACTCGGGAGGCTGAGGCAGGAGAATCGCTTGAACCCGGG" ++
        "AGGCGGAGGTTGCAGTGAGCCGAGATCGCGCCACTGCACTCC" ++
        "AGCCTGGGCGACAGAGCGAGACTCCGTCTCAAAAA";

    makeCumulative(&iub);
    makeCumulative(&homosapiens);

    makeRepeatFasta("ONE", "Homo sapiens alu", alu, n * 2);
    makeRandomFasta("TWO", "IUB ambiguity codes", &iub, n * 3);
    makeRandomFasta("THREE", "Homo sapiens frequency", &homosapiens, n * 5);
}
