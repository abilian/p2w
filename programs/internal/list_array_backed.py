"""Test array-backed list operations.

This tests the new $LIST type with O(1) indexed access.
Note: Currently lists still use PAIR chains by default.
This file will work once we enable array-backed lists.
"""

from __future__ import annotations


# Test basic list creation and access
lst = [1, 2, 3, 4, 5]
print(lst[0])  # 1
print(lst[2])  # 3
print(lst[4])  # 5

# Test negative indexing
print(lst[-1])  # 5
print(lst[-3])  # 3

# Test list length
print(len(lst))  # 5

# Test list modification
lst[2] = 99
print(lst[2])  # 99

# Test list in boolean context
if lst:
    print("list is truthy")

empty = []
if not empty:
    print("empty list is falsy")

# Test list append (if implemented)
# lst.append(6)
# print(len(lst))  # 6

# Test nested list access
nested = [[1, 2], [3, 4], [5, 6]]
print(nested[1][0])  # 3
print(nested[2][1])  # 6

# Test list with mixed types
mixed = [1, "hello", 3.14, True]
print(mixed[1])  # hello
print(len(mixed))  # 4

# Test list iteration
total = 0
for x in [10, 20, 30]:
    total = total + x
print(total)  # 60

# Test list comparison (element by element)
a = [1, 2, 3]
b = [1, 2, 3]
c = [1, 2, 4]
print(a == b)  # True
print(a == c)  # False

# Test list multiplication
repeated = [1, 2] * 3
print(len(repeated))  # 6

# Test list concatenation
concat = [1, 2] + [3, 4]
print(len(concat))  # 4
print(concat[2])  # 3

# Test membership
items = [10, 20, 30, 40]
print(20 in items)  # True
print(50 in items)  # False
print(50 not in items)  # True


print("list_array_backed tests done")
