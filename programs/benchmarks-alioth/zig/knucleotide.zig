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

// Same test sequence as Python/C versions
const BASE_SEQUENCE =
    "GGTATTTTAATTTATAGT" ++
    "CGATCGATCGATCGATCG" ++
    "ATCGATCGATCGATCGAT" ++
    "GGTATTTTAATTTATAGT" ++
    "AAAAAACCCCCCGGGGGG" ++
    "TTTTTTAAAAACCCCCGG" ++
    "GGGGTTTTTAAAACCCCG" ++
    "GGGTTTTAAAACCCGGGT" ++
    "TTTAAAACCGGGTTTTAA" ++
    "AACCCGGGTTTTAAAACG";

const HASH_SIZE = 4096;

const HashEntry = struct {
    key: [20]u8 = [_]u8{0} ** 20,
    key_len: usize = 0,
    count: u32 = 0,
    used: bool = false,
};

var hash_table: [HASH_SIZE]HashEntry = [_]HashEntry{.{}} ** HASH_SIZE;

fn hashFn(s: []const u8) u32 {
    var h: u32 = 0;
    for (s) |c| {
        h = h *% 31 +% c;
    }
    return h % HASH_SIZE;
}

fn clearHash() void {
    for (&hash_table) |*entry| {
        entry.used = false;
        entry.count = 0;
        entry.key_len = 0;
    }
}

fn insertOrIncrement(key: []const u8) void {
    var h = hashFn(key);
    const start = h;

    while (hash_table[h].used) {
        if (hash_table[h].key_len == key.len) {
            var matches = true;
            for (0..key.len) |i| {
                if (hash_table[h].key[i] != key[i]) {
                    matches = false;
                    break;
                }
            }
            if (matches) {
                hash_table[h].count += 1;
                return;
            }
        }
        h = (h + 1) % HASH_SIZE;
        if (h == start) return;
    }

    for (0..key.len) |i| {
        hash_table[h].key[i] = key[i];
    }
    hash_table[h].key_len = key.len;
    hash_table[h].count = 1;
    hash_table[h].used = true;
}

fn getCount(key: []const u8) u32 {
    var h = hashFn(key);
    const start = h;

    while (hash_table[h].used) {
        if (hash_table[h].key_len == key.len) {
            var matches = true;
            for (0..key.len) |i| {
                if (hash_table[h].key[i] != key[i]) {
                    matches = false;
                    break;
                }
            }
            if (matches) {
                return hash_table[h].count;
            }
        }
        h = (h + 1) % HASH_SIZE;
        if (h == start) break;
    }
    return 0;
}

fn countFrequencies(seq: []const u8, frame: usize) void {
    clearHash();
    var i: usize = 0;
    while (i + frame <= seq.len) : (i += 1) {
        insertOrIncrement(seq[i .. i + frame]);
    }
}

fn printFrequencies(total: usize) void {
    // Collect entries
    var entries: [HASH_SIZE]HashEntry = undefined;
    var n: usize = 0;

    for (hash_table) |entry| {
        if (entry.used) {
            entries[n] = entry;
            n += 1;
        }
    }

    // Bubble sort by count descending, then key ascending
    var i: usize = 0;
    while (i < n) : (i += 1) {
        var j: usize = 0;
        while (j + 1 < n - i) : (j += 1) {
            var swap = false;
            if (entries[j].count < entries[j + 1].count) {
                swap = true;
            } else if (entries[j].count == entries[j + 1].count) {
                // Compare keys lexicographically
                const len = @min(entries[j].key_len, entries[j + 1].key_len);
                var k: usize = 0;
                while (k < len) : (k += 1) {
                    if (entries[j].key[k] > entries[j + 1].key[k]) {
                        swap = true;
                        break;
                    } else if (entries[j].key[k] < entries[j + 1].key[k]) {
                        break;
                    }
                }
                if (k == len and entries[j].key_len > entries[j + 1].key_len) {
                    swap = true;
                }
            }

            if (swap) {
                const tmp = entries[j];
                entries[j] = entries[j + 1];
                entries[j + 1] = tmp;
            }
        }
    }

    // Print
    for (0..n) |idx| {
        const freq = 100.0 * @as(f64, @floatFromInt(entries[idx].count)) / @as(f64, @floatFromInt(total));
        writeBytes(entries[idx].key[0..entries[idx].key_len]);
        print(" {d:.3}\n", .{freq});
    }
    writeBytes("\n");
}

fn toUpper(c: u8) u8 {
    if (c >= 'a' and c <= 'z') {
        return c - 32;
    }
    return c;
}

pub fn main() !void {
    var gpa = std.heap.GeneralPurposeAllocator(.{}){};
    defer _ = gpa.deinit();
    const allocator = gpa.allocator();

    // Build repeated sequence (100 times)
    const base_len = BASE_SEQUENCE.len;
    const seq_len = base_len * 100;
    const sequence = try allocator.alloc(u8, seq_len);
    defer allocator.free(sequence);

    for (0..100) |i| {
        for (0..base_len) |j| {
            sequence[i * base_len + j] = toUpper(BASE_SEQUENCE[j]);
        }
    }

    // Output 1-mer frequencies
    countFrequencies(sequence, 1);
    printFrequencies(seq_len);

    // Output 2-mer frequencies
    countFrequencies(sequence, 2);
    printFrequencies(seq_len - 1);

    // Output counts for specific oligos
    const oligos = [_][]const u8{ "GGT", "GGTA", "GGTATT", "GGTATTTTAATT", "GGTATTTTAATTTATAGT" };

    for (oligos) |oligo| {
        countFrequencies(sequence, oligo.len);
        print("{d}\t", .{getCount(oligo)});
        writeBytes(oligo);
        writeBytes("\n");
    }
}
