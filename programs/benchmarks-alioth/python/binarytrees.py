# The Computer Language Benchmarks Game
# http://benchmarksgame.alioth.debian.org/
#
# contributed by Antoine Pitrou
# modified by Dominique Wahli
# modified by Heinrich Acker
# adapted for p2w
#
# Single-threaded version optimized for p2w


def make_tree(depth: int):
    if depth == 0:
        return (None, None)
    depth = depth - 1
    return (make_tree(depth), make_tree(depth))


def check_tree(node) -> int:
    left = node[0]
    right = node[1]
    if left is None:
        return 1
    return 1 + check_tree(left) + check_tree(right)


def main(n: int) -> None:
    min_depth: int = 4
    max_depth: int = 0
    if min_depth + 2 > n:
        max_depth = min_depth + 2
    else:
        max_depth = n

    stretch_depth: int = max_depth + 1

    stretch_tree = make_tree(stretch_depth)
    stretch_check: int = check_tree(stretch_tree)
    print("stretch tree of depth", stretch_depth, "check:", stretch_check)

    long_lived_tree = make_tree(max_depth)

    iterations: int = 1
    i: int = 0
    while i < max_depth:
        iterations = iterations * 2
        i = i + 1

    depth: int = min_depth
    while depth < stretch_depth:
        check: int = 0
        i = 1
        while i <= iterations:
            check = check + check_tree(make_tree(depth))
            i = i + 1

        print(iterations, "trees of depth", depth, "check:", check)
        iterations = iterations // 4
        depth = depth + 2

    print("long lived tree of depth", max_depth, "check:", check_tree(long_lived_tree))


# Default argument for testing
main(10)
