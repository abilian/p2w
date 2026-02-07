"""Test basic list comprehensions."""

from __future__ import annotations

# Basic list comprehension with range
squares = [x * x for x in range(5)]
print(squares)

# List comprehension with condition
evens = [x for x in range(10) if x % 2 == 0]
print(evens)

# List comprehension over a list
doubled = [x * 2 for x in [1, 2, 3]]
print(doubled)

# List comprehension with expression
result = [x + 10 for x in range(4)]
print(result)

# Empty range
empty = [x for x in range(0)]
print(len(empty))  # 0

# Single element
single = [x for x in range(1)]
print(single)

# With arithmetic in condition
divisible_by_3 = [x for x in range(15) if x % 3 == 0]
print(divisible_by_3)

print("listcomp_basic tests done")
