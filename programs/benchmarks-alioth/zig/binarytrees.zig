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

const TreeNode = struct {
    left: ?*TreeNode,
    right: ?*TreeNode,
};

fn bottomUpTree(allocator: std.mem.Allocator, depth: u32) !*TreeNode {
    const node = try allocator.create(TreeNode);
    if (depth > 0) {
        node.left = try bottomUpTree(allocator, depth - 1);
        node.right = try bottomUpTree(allocator, depth - 1);
    } else {
        node.left = null;
        node.right = null;
    }
    return node;
}

fn itemCheck(tree: *const TreeNode) i64 {
    if (tree.left) |left| {
        return 1 + itemCheck(left) + itemCheck(tree.right.?);
    } else {
        return 1;
    }
}

fn deleteTree(allocator: std.mem.Allocator, tree: *TreeNode) void {
    if (tree.left) |left| {
        deleteTree(allocator, left);
        deleteTree(allocator, tree.right.?);
    }
    allocator.destroy(tree);
}

pub fn main() !void {
    var gpa = std.heap.GeneralPurposeAllocator(.{}){};
    defer _ = gpa.deinit();
    const allocator = gpa.allocator();

    var args = std.process.args();
    _ = args.skip();

    const n_str = args.next() orelse "10";
    const n = std.fmt.parseInt(u32, n_str, 10) catch 10;

    const min_depth: u32 = 4;
    const max_depth = if (min_depth + 2 > n) min_depth + 2 else n;
    const stretch_depth = max_depth + 1;

    // Stretch tree
    {
        const stretch_tree = try bottomUpTree(allocator, stretch_depth);
        print("stretch tree of depth {d}\t check: {d}\n", .{ stretch_depth, itemCheck(stretch_tree) });
        deleteTree(allocator, stretch_tree);
    }

    // Long-lived tree
    const long_lived_tree = try bottomUpTree(allocator, max_depth);

    var depth = min_depth;
    while (depth <= max_depth) : (depth += 2) {
        const iterations = @as(i64, 1) << @intCast(max_depth - depth + min_depth);
        var check: i64 = 0;

        var i: i64 = 1;
        while (i <= iterations) : (i += 1) {
            const temp_tree = try bottomUpTree(allocator, depth);
            check += itemCheck(temp_tree);
            deleteTree(allocator, temp_tree);
        }

        print("{d}\t trees of depth {d}\t check: {d}\n", .{ iterations, depth, check });
    }

    print("long lived tree of depth {d}\t check: {d}\n", .{ max_depth, itemCheck(long_lived_tree) });
    deleteTree(allocator, long_lived_tree);
}
