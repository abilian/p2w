"""Test advanced comprehension patterns."""

from __future__ import annotations


# Dict comprehension - basic
d = {x: x * x for x in range(5)}
print(d[0])   # 0
print(d[3])   # 9
print(d[4])   # 16

# Dict comprehension with condition
evens = {x: x * 2 for x in range(10) if x % 2 == 0}
print(len(evens))  # 5
print(evens[4])    # 8

# Dict comprehension with expression
cubes = {n: n * n * n for n in range(4)}
print(cubes[2])   # 8
print(cubes[3])   # 27

# List comprehension with string methods
words = ["hello", "WORLD", "Python"]
lower = [w.lower() for w in words]
print(lower)  # ['hello', 'world', 'python']

upper = [w.upper() for w in words]
print(upper)  # ['HELLO', 'WORLD', 'PYTHON']

# List comprehension with len
lengths = [len(w) for w in words]
print(lengths)  # [5, 5, 6]

# List comprehension filtering by length
short = [w for w in words if len(w) <= 5]
print(short)  # ['hello', 'WORLD']

# Nested loops in comprehension
products = [x * y for x in [1, 2, 3] for y in [10, 20]]
print(products)  # [10, 20, 20, 40, 30, 60]

# Comprehension with conditional expression (ternary)
classified = ["even" if x % 2 == 0 else "odd" for x in range(5)]
print(classified)  # ['even', 'odd', 'even', 'odd', 'even']

# Comprehension building tuples
coords = [(x, x * x) for x in range(4)]
print(coords)  # [(0, 0), (1, 1), (2, 4), (3, 9)]

# Comprehension with negative numbers
negatives = [-x for x in range(5)]
print(negatives)  # [0, -1, -2, -3, -4]

# Comprehension with abs
absolutes = [abs(x) for x in [-3, -1, 0, 1, 3]]
print(absolutes)  # [3, 1, 0, 1, 3]

# Nested comprehension creating 2D grid
grid = [[i * j for j in range(1, 4)] for i in range(1, 4)]
print(grid[0])  # [1, 2, 3]
print(grid[1])  # [2, 4, 6]
print(grid[2])  # [3, 6, 9]

# Flattening nested list with comprehension
nested = [[1, 2], [3, 4, 5], [6]]
flat = [x for sublist in nested for x in sublist]
print(flat)  # [1, 2, 3, 4, 5, 6]

# Comprehension collecting results from function
def square(x):
    return x * x

squares = [square(x) for x in range(6)]
print(squares)  # [0, 1, 4, 9, 16, 25]

# Comprehension with multiple filters combined
result = [x for x in range(30) if x % 2 == 0 if x % 5 == 0]
print(result)  # [0, 10, 20]

# List comprehension with nested function call
def increment(x):
    return x + 1

def double(x):
    return x * 2

processed = [double(increment(x)) for x in range(4)]
print(processed)  # [2, 4, 6, 8]

# Set comprehension with condition
even_squares = {x * x for x in range(10) if x % 2 == 0}
print(sorted(list(even_squares)))  # [0, 4, 16, 36, 64]

# Comprehension with modulo grouping
mod3 = {x % 3 for x in range(20)}
print(sorted(list(mod3)))  # [0, 1, 2]

# List comprehension with boolean
bools = [x > 5 for x in range(10)]
print(bools)  # [False, False, False, False, False, False, True, True, True, True]

# Comprehension with str conversion
strs = [str(x) for x in [1, 2, 3]]
print(strs)  # ['1', '2', '3']

# Comprehension with int conversion
nums = [int(s) for s in ["1", "2", "3"]]
print(nums)  # [1, 2, 3]


print("comprehensions_advanced tests done")
