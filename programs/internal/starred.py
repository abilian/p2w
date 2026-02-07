"""Test starred expressions in list literals."""

from __future__ import annotations

# Starred in list literals
a = [1, 2]
b = [3, 4]
c = [*a, *b]
print(c)

# Mixed with regular elements
d = [0, *a, 5, *b, 9]
print(d)

# Starred unpacking - simple cases
first, *rest = [1, 2, 3, 4, 5]
print(first)
print(rest)

# Empty rest
x, *empty = [10]
print(x)
print(empty)

# Single starred
(*all_items,) = [1, 2, 3]
print(all_items)
