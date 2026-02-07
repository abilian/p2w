"""Test list operations edge cases and advanced patterns."""

from __future__ import annotations


# Empty list operations
empty = []
print(len(empty))      # 0
print([] == [])        # True
print([] != [1])       # True

# Single element list
single = [42]
print(single[0])       # 42
print(single[-1])      # 42
print(len(single))     # 1

# List assignment (positive index)
lst = [1, 2, 3, 4, 5]
lst[0] = 10
print(lst)  # [10, 2, 3, 4, 5]

lst[4] = 50
print(lst)  # [10, 2, 3, 4, 50]

# Slice assignment
lst = [1, 2, 3, 4, 5]
lst[1:3] = [20, 30]
print(lst)  # [1, 20, 30, 4, 5]

# Slice assignment with different length
lst = [1, 2, 3, 4, 5]
lst[1:4] = [20]
print(lst)  # [1, 20, 5]

# Deletion from list
lst = [1, 2, 3, 4, 5]
del lst[2]
print(lst)  # [1, 2, 4, 5]

# Negative indexing (read only)
lst = [10, 20, 30, 40, 50]
print(lst[-1])   # 50
print(lst[-2])   # 40
print(lst[-5])   # 10

# Negative slice
print(lst[-3:])     # [30, 40, 50]
print(lst[:-2])     # [10, 20, 30]
print(lst[-4:-1])   # [20, 30, 40]

# Step slicing
lst = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
print(lst[::3])      # [0, 3, 6, 9]
print(lst[1::2])     # [1, 3, 5, 7, 9]
print(lst[::-1])     # [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
print(lst[::-2])     # [9, 7, 5, 3, 1]

# List of mixed types
mixed = [1, "two", 3.0, [4, 5], {"six": 6}]
print(len(mixed))     # 5
print(mixed[1])       # two
print(mixed[3])       # [4, 5]
print(mixed[3][0])    # 4

# List comparison
print([1, 2, 3] == [1, 2, 3])  # True
print([1, 2, 3] == [1, 2, 4])  # False
print([1, 2] != [1, 2, 3])    # True

# List in conditional
if []:
    print("empty is truthy")
else:
    print("empty is falsy")  # This prints

if [1]:
    print("non-empty is truthy")  # This prints

# List with None
with_none = [None, 1, None, 2]
print(None in with_none)      # True

# List multiplication (non-empty)
zeros = [0] * 5
print(zeros)  # [0, 0, 0, 0, 0]

pattern = [1, 2] * 3
print(pattern)  # [1, 2, 1, 2, 1, 2]

# Chained list operations (non-empty)
result = [1, 2, 3] + [4, 5] + [6]
print(result)  # [1, 2, 3, 4, 5, 6]

# List in loop
total = 0
for item in [10, 20, 30]:
    total = total + item
print(total)  # 60

# Enumerate with list
items = ["a", "b", "c"]
for i, item in enumerate(items):
    print(i, item)

# List with boolean operations
bools = [True, False, True, True]
print(any(bools))  # True
print(all(bools))  # False

# Nested list access
matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
print(matrix[0][0])   # 1
print(matrix[2][2])   # 9
print(matrix[1])      # [4, 5, 6]

# Building list incrementally
result = []
for i in range(5):
    result.append(i * i)
print(result)  # [0, 1, 4, 9, 16]

# List from range
from_range = list(range(5))
print(from_range)  # [0, 1, 2, 3, 4]

# Reverse via slicing
original = [1, 2, 3, 4, 5]
reversed_copy = original[::-1]
print(original)       # [1, 2, 3, 4, 5] (unchanged)
print(reversed_copy)  # [5, 4, 3, 2, 1]

# Copy via slicing
original = [1, 2, 3]
copy = original[:]
copy.append(4)
print(original)  # [1, 2, 3]
print(copy)      # [1, 2, 3, 4]


print("list_edge_cases tests done")
