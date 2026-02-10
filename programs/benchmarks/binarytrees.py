"""Binary Trees benchmark.

Creates and traverses binary trees.
Adapted for p2w (uses __slots__ with type narrowing optimization).
"""

from __future__ import annotations


class Tree:
    __slots__ = ('item', 'left', 'right')

    def __init__(self, item: int, left, right) -> None:
        self.item: int = item
        self.left = left
        self.right = right


def make_tree(item: int, depth: int):
    if depth <= 0:
        return item
    item2: int = item + item
    depth = depth - 1
    return Tree(item, make_tree(item2 - 1, depth), make_tree(item2, depth))


def check_tree(tree) -> int:
    if not isinstance(tree, Tree):
        return tree
    return tree.item + check_tree(tree.left) - check_tree(tree.right)


def main(max_depth: int) -> None:
    min_depth: int = 4
    stretch_depth: int = max_depth + 1

    print(
        "stretch tree of depth",
        stretch_depth,
        "check:",
        check_tree(make_tree(0, stretch_depth)),
    )

    long_lived_tree = make_tree(0, max_depth)

    iterations: int = 2**max_depth
    depth: int = min_depth
    while depth < stretch_depth:
        check: int = 0
        for i in range(1, iterations + 1):
            check = (
                check
                + check_tree(make_tree(i, depth))
                + check_tree(make_tree(-i, depth))
            )

        print(iterations * 2, "trees of depth", depth, "check:", check)
        iterations = iterations // 4
        depth = depth + 2

    print("long lived tree of depth", max_depth, "check:", check_tree(long_lived_tree))


# Benchmark with depth 14 (matching alioth)
main(14)
