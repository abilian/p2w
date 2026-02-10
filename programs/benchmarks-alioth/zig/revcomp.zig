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

fn writeBytes(bytes: []const u8) void {
    _ = posix.write(posix.STDOUT_FILENO, bytes) catch {};
}

fn complement(c: u8) u8 {
    return switch (c) {
        'A', 'a' => 'T',
        'T', 't' => 'A',
        'C', 'c' => 'G',
        'G', 'g' => 'C',
        'B', 'b' => 'V',
        'V', 'v' => 'B',
        'D', 'd' => 'H',
        'H', 'h' => 'D',
        'K', 'k' => 'M',
        'M', 'm' => 'K',
        'N', 'n' => 'N',
        'R', 'r' => 'Y',
        'Y', 'y' => 'R',
        'S', 's' => 'S',
        'W', 'w' => 'W',
        'U', 'u' => 'A',
        else => c,
    };
}

fn reverseComplement(seq: []const u8, allocator: std.mem.Allocator) ![]u8 {
    const result = try allocator.alloc(u8, seq.len);
    for (0..seq.len) |i| {
        result[i] = complement(seq[seq.len - 1 - i]);
    }
    return result;
}

fn printFormatted(seq: []const u8, width: usize) void {
    var i: usize = 0;
    var line: [61]u8 = undefined;

    while (i < seq.len) {
        const line_len = if (i + width <= seq.len) width else seq.len - i;
        for (0..line_len) |j| {
            line[j] = seq[i + j];
        }
        line[line_len] = '\n';
        writeBytes(line[0 .. line_len + 1]);
        i += width;
    }
}

fn processEntry(header: []const u8, sequence: []const u8, allocator: std.mem.Allocator) !void {
    const rc = try reverseComplement(sequence, allocator);
    defer allocator.free(rc);

    writeBytes(header);
    writeBytes("\n");
    printFormatted(rc, 60);
}

pub fn main() !void {
    var gpa = std.heap.GeneralPurposeAllocator(.{}){};
    defer _ = gpa.deinit();
    const allocator = gpa.allocator();

    // Same test data as Python/C versions - repeated 10 times
    const entries = [_]struct { header: []const u8, sequence: []const u8 }{
        .{
            .header = ">ONE Homo sapiens alu",
            .sequence = "GGCCGGGCGCGGTGGCTCACGCCTGTAATCCCAGCACTTTGGGAGGCCGAGGCGGGCGGATCACCTGAGGTCAGGAGTTCGAGACCAGCCTGGCCAACATGGTGAAACCCCGTCTCTACTAAAAATACAAAAATTAGCCGGGCGTGGTGGCGCGCGCCTGTAATCCCAGCTACTCGGGAGGCTGAGGCAGGAGAATCGCTTGAACCCGGGAGGCGGAGGTTGCAGTGAGCCGAGATCGCGCCACTGCACTCCAGCCTGGGCGACAGAGCGAGACTCCGTCTCAAAAA",
        },
        .{
            .header = ">TWO IUB ambiguity codes",
            .sequence = "TAGGDHACHATCRYGMKWSYYBVNN",
        },
        .{
            .header = ">THREE Homo sapiens frequency",
            .sequence = "ATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGC",
        },
    };

    // Process 10 times
    for (0..10) |_| {
        for (entries) |entry| {
            try processEntry(entry.header, entry.sequence, allocator);
        }
    }
}
