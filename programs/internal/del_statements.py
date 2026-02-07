"""Test del statement for various targets."""

from __future__ import annotations


# del from list by index
lst = [1, 2, 3, 4, 5]
del lst[0]
print(lst)  # [2, 3, 4, 5]

del lst[2]
print(lst)  # [2, 3, 5]


# del from list by negative index
lst2 = [10, 20, 30, 40]
del lst2[-1]
print(lst2)  # [10, 20, 30]


# del slice from list
lst3 = [1, 2, 3, 4, 5, 6]
del lst3[1:3]
print(lst3)  # [1, 4, 5, 6]


# del slice from start
lst4 = [1, 2, 3, 4, 5]
del lst4[:2]
print(lst4)  # [3, 4, 5]


# del slice to end
lst5 = [1, 2, 3, 4, 5]
del lst5[3:]
print(lst5)  # [1, 2, 3]


# del entire slice (clear list)
lst6 = [1, 2, 3]
del lst6[:]
print(lst6)  # []


# del from dict
d = {"a": 1, "b": 2, "c": 3}
del d["b"]
print(d["a"])  # 1
print(len(d))  # 2


# Delete variable (local scope)
def test_del_var():
    x = 10
    y = x
    del x
    return y


print(test_del_var())  # 10


# Multiple deletions
items = [1, 2, 3, 4, 5, 6, 7, 8]
del items[0]
del items[0]
print(items)  # [3, 4, 5, 6, 7, 8]


print("del_statements tests done")
