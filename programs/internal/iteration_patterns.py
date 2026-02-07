"""Test iteration patterns with range, enumerate, zip."""

from __future__ import annotations


# Basic range
for i in range(5):
    print(i)

# Range with start
for i in range(2, 6):
    print(i)

# Range with step
for i in range(0, 10, 2):
    print(i)

# Range to list
r = list(range(5))
print(r)  # [0, 1, 2, 3, 4]

# Enumerate basic
for i, val in enumerate(["a", "b", "c"]):
    print(i, val)

# Enumerate with start
for i, val in enumerate(["x", "y", "z"], 1):
    print(i, val)

# Enumerate collecting results
indexed = list(enumerate(["apple", "banana", "cherry"]))
print(len(indexed))  # 3
print(indexed[0])    # (0, 'apple')

# Zip basic
for a, b in zip([1, 2, 3], ["a", "b", "c"]):
    print(a, b)

# Zip with different lengths (stops at shortest)
for x, y in zip([1, 2, 3, 4], [10, 20]):
    print(x, y)

# Zip to list
zipped = list(zip([1, 2, 3], [4, 5, 6]))
print(zipped)  # [(1, 4), (2, 5), (3, 6)]

# Range in comprehension
squares = [x * x for x in range(6)]
print(squares)  # [0, 1, 4, 9, 16, 25]

# Enumerate in comprehension
indexed_squares = [(i, x * x) for i, x in enumerate(range(5))]
print(indexed_squares)

# Zip in comprehension
sums = [a + b for a, b in zip([1, 2, 3], [10, 20, 30])]
print(sums)  # [11, 22, 33]

# Range with sum
total = sum(range(1, 6))
print(total)  # 15

# Enumerate for searching
items = ["apple", "banana", "cherry", "date"]
for i, item in enumerate(items):
    if item == "cherry":
        print("found at", i)
        break

# Zip for parallel processing
names = ["Alice", "Bob", "Charlie"]
scores = [85, 92, 78]
for name, score in zip(names, scores):
    print(name + ":", score)

# Empty range
empty = list(range(5, 5))
print(len(empty))  # 0

# Range in function
def sum_range(start, end):
    total = 0
    for i in range(start, end):
        total = total + i
    return total

print(sum_range(1, 11))  # 55

# Nested range
grid = []
for i in range(3):
    row = []
    for j in range(3):
        row.append(i * 3 + j)
    grid.append(row)
print(grid)

# Enumerate with index math
words = ["hello", "world", "python"]
for i, word in enumerate(words):
    if i > 0:
        print(i, ":", word)


print("iteration_patterns tests done")
