"""Test negative indexing for arrays, tuples, and strings."""

from __future__ import annotations


# List negative indexing
lst = [10, 20, 30, 40, 50]
print(lst[-1])  # 50 (last element)
print(lst[-2])  # 40 (second to last)
print(lst[-5])  # 10 (first element via negative)

# Tuple negative indexing
tup = (1, 2, 3, 4, 5)
print(tup[-1])  # 5
print(tup[-3])  # 3

# String negative indexing
s = "hello"
print(s[-1])  # "o"
print(s[-2])  # "l"
print(s[-5])  # "h"

# Negative index in expressions
lst2 = [1, 2, 3, 4, 5]
print(lst2[-1] + lst2[-2])  # 9 (5 + 4)

# Negative slicing
arr = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
print(arr[-3:])  # [7, 8, 9]
print(arr[:-3])  # [0, 1, 2, 3, 4, 5, 6]
print(arr[-5:-2])  # [5, 6, 7]

# Negative step
print(arr[::-1])  # [9, 8, 7, 6, 5, 4, 3, 2, 1, 0] - reversed
print(arr[-1:-6:-1])  # [9, 8, 7, 6, 5]

# String negative slicing
word = "python"
print(word[-3:])  # "hon"
print(word[:-2])  # "pyth"
print(word[::-1])  # "nohtyp"


# Negative index with range check
def safe_get(lst, idx):
    if idx < -len(lst) or idx >= len(lst):
        return None
    return lst[idx]


data = [1, 2, 3]
print(safe_get(data, -1))  # 3
print(safe_get(data, -3))  # 1
print(safe_get(data, -4))  # None (out of bounds)

# Negative index in loop
items = ["a", "b", "c", "d"]
for i in range(1, len(items) + 1):
    print(items[-i])  # d, c, b, a

# pop with negative index
stack = [1, 2, 3, 4, 5]
print(stack.pop(-2))  # 4 (removes second to last)
print(stack)  # [1, 2, 3, 5]


# Access via negative index in function
def get_last(items):
    return items[-1]


print(get_last([10, 20, 30, 40]))  # 40

# Nested structure negative indexing
matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
print(matrix[-1])  # [7, 8, 9]
print(matrix[-1][-1])  # 9
print(matrix[-2][-2])  # 5


print("negative indexing tests done")
