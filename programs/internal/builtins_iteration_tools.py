"""Test iteration tools: enumerate, zip, reversed."""

from __future__ import annotations


# =============================================================================
# enumerate() - iterate with index
# =============================================================================

# Basic enumerate
print("enumerate basic:")
for i, val in enumerate(["a", "b", "c"]):
    print(i, val)
# 0 a
# 1 b
# 2 c

# enumerate with start parameter
print("enumerate with start=1:")
for i, val in enumerate(["x", "y", "z"], start=1):
    print(i, val)
# 1 x
# 2 y
# 3 z

# enumerate with start=10
print("enumerate with start=10:")
for i, val in enumerate([100, 200], start=10):
    print(i, val)
# 10 100
# 11 200

# enumerate empty list
print("enumerate empty:")
result = list(enumerate([]))
print(result)  # []

# enumerate single element
print("enumerate single:")
result = list(enumerate(["only"]))
print(result)  # [(0, 'only')]

# enumerate with tuple unpacking in list comprehension
print("enumerate in comprehension:")
pairs = [(i, x * 2) for i, x in enumerate([1, 2, 3])]
print(pairs)  # [(0, 2), (1, 4), (2, 6)]

# enumerate string
print("enumerate string:")
for i, ch in enumerate("abc"):
    print(i, ch)
# 0 a
# 1 b
# 2 c


# =============================================================================
# zip() - combine iterables
# =============================================================================

# Basic zip
print("zip basic:")
for a, b in zip([1, 2, 3], ["a", "b", "c"]):
    print(a, b)
# 1 a
# 2 b
# 3 c

# zip with different lengths (stops at shortest)
print("zip different lengths:")
result = list(zip([1, 2, 3, 4, 5], ["x", "y"]))
print(result)  # [(1, 'x'), (2, 'y')]

# zip three iterables
print("zip three lists:")
for a, b, c in zip([1, 2], ["a", "b"], [True, False]):
    print(a, b, c)
# 1 a True
# 2 b False

# zip empty lists
print("zip empty:")
result = list(zip([], []))
print(result)  # []

# zip single elements
print("zip single elements:")
result = list(zip([1], ["a"]))
print(result)  # [(1, 'a')]

# zip in list comprehension
print("zip in comprehension:")
sums = [a + b for a, b in zip([1, 2, 3], [10, 20, 30])]
print(sums)  # [11, 22, 33]

# zip with strings
print("zip strings:")
pairs = list(zip("abc", "123"))
print(pairs)  # [('a', '1'), ('b', '2'), ('c', '3')]

# Using zip to create dict
print("zip to dict:")
keys = ["a", "b", "c"]
values = [1, 2, 3]
d = dict(zip(keys, values))
print(d)  # {'a': 1, 'b': 2, 'c': 3}


# =============================================================================
# reversed() - reverse iteration
# =============================================================================

# reversed on list
print("reversed list:")
for x in reversed([1, 2, 3, 4, 5]):
    print(x)
# 5
# 4
# 3
# 2
# 1

# reversed to list
print("reversed to list:")
result = list(reversed([10, 20, 30]))
print(result)  # [30, 20, 10]

# reversed on string
print("reversed string:")
result = "".join(reversed("hello"))
print(result)  # olleh

# reversed on tuple
print("reversed tuple:")
result = list(reversed((1, 2, 3)))
print(result)  # [3, 2, 1]

# reversed empty
print("reversed empty:")
result = list(reversed([]))
print(result)  # []

# reversed single element
print("reversed single:")
result = list(reversed([42]))
print(result)  # [42]

# reversed in comprehension
print("reversed in comprehension:")
doubled = [x * 2 for x in reversed([1, 2, 3])]
print(doubled)  # [6, 4, 2]

# Nested reversed
print("nested reversed:")
result = list(reversed(list(reversed([1, 2, 3]))))
print(result)  # [1, 2, 3]


# =============================================================================
# Combining iteration tools
# =============================================================================

# enumerate + reversed
print("enumerate reversed:")
for i, val in enumerate(reversed([10, 20, 30])):
    print(i, val)
# 0 30
# 1 20
# 2 10

# zip + enumerate
print("zip enumerate:")
for i, (a, b) in enumerate(zip([1, 2], ["x", "y"])):
    print(i, a, b)
# 0 1 x
# 1 2 y

# reversed + zip
print("reversed zip:")
result = list(zip(reversed([1, 2, 3]), ["a", "b", "c"]))
print(result)  # [(3, 'a'), (2, 'b'), (1, 'c')]


print("builtins_iteration_tools tests done")
