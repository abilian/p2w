"""Test list methods."""

from __future__ import annotations


# append()
lst = [1, 2, 3]
lst.append(4)
print(lst)  # [1, 2, 3, 4]


# extend()
lst = [1, 2, 3]
lst.extend([4, 5, 6])
print(lst)  # [1, 2, 3, 4, 5, 6]


# insert()
lst = [1, 2, 4, 5]
lst.insert(2, 3)  # Insert 3 at index 2
print(lst)  # [1, 2, 3, 4, 5]

lst.insert(0, 0)  # Insert at beginning
print(lst)  # [0, 1, 2, 3, 4, 5]


# remove()
lst = [1, 2, 3, 2, 4]
lst.remove(2)  # Removes first occurrence
print(lst)  # [1, 3, 2, 4]


# pop()
lst = [1, 2, 3, 4, 5]
print(lst.pop())  # 5 (removes and returns last)
print(lst)  # [1, 2, 3, 4]

print(lst.pop(0))  # 1 (removes and returns first)
print(lst)  # [2, 3, 4]


# clear()
lst = [1, 2, 3]
lst.clear()
print(lst)  # []


# index()
lst = [10, 20, 30, 20, 40]
print(lst.index(20))  # 1 (first occurrence)
print(lst.index(20, 2))  # 3 (search from index 2)


# count()
lst = [1, 2, 2, 3, 2, 4]
print(lst.count(2))  # 3
print(lst.count(5))  # 0


# sort()
lst = [3, 1, 4, 1, 5, 9, 2, 6]
lst.sort()
print(lst)  # [1, 1, 2, 3, 4, 5, 6, 9]

lst = [3, 1, 4, 1, 5]
lst.sort(reverse=True)
print(lst)  # [5, 4, 3, 1, 1]


# reverse()
lst = [1, 2, 3, 4, 5]
lst.reverse()
print(lst)  # [5, 4, 3, 2, 1]


# copy()
original = [1, 2, 3]
copied = original.copy()
copied.append(4)
print(original)  # [1, 2, 3]
print(copied)  # [1, 2, 3, 4]


# List concatenation and repetition
a = [1, 2]
b = [3, 4]
print(a + b)  # [1, 2, 3, 4]
print(a * 3)  # [1, 2, 1, 2, 1, 2]


# List membership
lst = [1, 2, 3, 4, 5]
print(3 in lst)  # True
print(6 in lst)  # False


# List slicing
lst = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
print(lst[2:5])  # [2, 3, 4]
print(lst[:3])  # [0, 1, 2]
print(lst[7:])  # [7, 8, 9]
print(lst[::2])  # [0, 2, 4, 6, 8]


# Nested lists
matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
print(matrix[1][1])  # 5


print("list_methods tests done")
