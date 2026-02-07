"""Test list, dict, and set comprehensions."""

from __future__ import annotations


# Basic list comprehension
squares = [x * x for x in range(5)]
print(squares)

# List comprehension with condition
evens = [x for x in range(10) if x % 2 == 0]
print(evens)

# List comprehension with expression
doubled = [x * 2 for x in [1, 2, 3]]
print(doubled)

# Nested list comprehension
matrix = [[i + j for j in range(3)] for i in range(3)]
print(matrix)

# Flatten with nested comprehension
flat = [x for row in [[1, 2], [3, 4], [5, 6]] for x in row]
print(flat)


# Comprehension with function call
def double(x):
    return x * 2


result = [double(x) for x in range(4)]
print(result)

# Multiple conditions
filtered = [x for x in range(20) if x % 2 == 0 if x % 3 == 0]
print(filtered)

# Comprehension with range step
stepped = [x for x in range(0, 10, 2)]
print(stepped)

# Comprehension with tuple unpacking
pairs = [(1, "a"), (2, "b"), (3, "c")]
nums = [n for n, _ in pairs]
print(nums)

# Nested comprehension producing flat list
coords = [(x, y) for x in range(2) for y in range(2)]
print(len(coords))

# Set comprehension (now implemented!)
unique_mods = {x % 3 for x in range(10)}
print(sorted(list(unique_mods)))

# Set comprehension with condition
even_squares = {x * x for x in range(10) if x % 2 == 0}
print(sorted(list(even_squares)))
