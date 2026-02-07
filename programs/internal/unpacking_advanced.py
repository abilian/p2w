"""Test advanced unpacking with starred expressions."""

from __future__ import annotations


# Basic starred unpacking
a, *rest = [1, 2, 3, 4, 5]
print(a)  # 1
print(rest)  # [2, 3, 4, 5]


# Star at the end
*start, last = [1, 2, 3, 4, 5]
print(start)  # [1, 2, 3, 4]
print(last)  # 5


# Star in the middle
first, *middle, last = [1, 2, 3, 4, 5]
print(first)  # 1
print(middle)  # [2, 3, 4]
print(last)  # 5


# With just enough elements
a, *rest = [1, 2]
print(a)  # 1
print(rest)  # [2]


# Multiple targets with star
first, second, *rest = [1, 2, 3, 4, 5, 6]
print(first)  # 1
print(second)  # 2
print(rest)  # [3, 4, 5, 6]


# With tuples
a, *rest, z = (10, 20, 30, 40, 50)
print(a)  # 10
print(rest)  # [20, 30, 40]
print(z)  # 50


# Swapping with unpacking
x, y = 10, 20
x, y = y, x
print(x, y)  # 20 10


# Unpacking in function call
def add(a, b, c):
    return a + b + c


args = [1, 2, 3]
print(add(*args))  # 6


# Unpacking dict in function call (using explicit args instead of **kwargs)
def greet(name, greeting="Hello"):
    return f"{greeting}, {name}!"


# Note: **kwargs unpacking in calls not fully supported
# Using explicit arguments instead
print(greet("World", "Hi"))  # Hi, World!


# Unpacking in list literals
list1 = [1, 2, 3]
list2 = [4, 5, 6]
combined = [*list1, *list2]
print(combined)  # [1, 2, 3, 4, 5, 6]


# Dict merging with update (workaround for {**d1, **d2})
dict1 = {"a": 1, "b": 2}
dict2 = {"c": 3, "d": 4}
merged = dict1.copy()
merged.update(dict2)
print(len(merged))  # 4


# Unpacking with range
a, b, c, d, e = range(5)
print(a, b, c, d, e)  # 0 1 2 3 4


# Unpacking return values
def get_stats(numbers):
    return min(numbers), max(numbers), sum(numbers)


mn, mx, total = get_stats([1, 2, 3, 4, 5])
print(mn, mx, total)  # 1 5 15


# Ignore values with underscore
a, _, c = [1, 2, 3]
print(a, c)  # 1 3


print("unpacking_advanced tests done")
