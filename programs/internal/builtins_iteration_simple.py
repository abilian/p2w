"""Test iteration tools: enumerate, zip, reversed (simplified - no tuple unpacking in for)."""

from __future__ import annotations


# =============================================================================
# enumerate() - iterate with index
# =============================================================================

print("enumerate to list:")
result = list(enumerate(["a", "b", "c"]))
print(result)  # [(0, 'a'), (1, 'b'), (2, 'c')]

print("enumerate with start=1:")
result = list(enumerate(["x", "y", "z"], 1))
print(result)  # [(1, 'x'), (2, 'y'), (3, 'z')]

print("enumerate with start=10:")
result = list(enumerate([100, 200], 10))
print(result)  # [(10, 100), (11, 200)]

print("enumerate empty list:")
result = list(enumerate([]))
print(result)  # []

print("enumerate single element:")
result = list(enumerate(["only"]))
print(result)  # [(0, 'only')]

print("enumerate string:")
result = list(enumerate("abc"))
print(result)  # [(0, 'a'), (1, 'b'), (2, 'c')]


# =============================================================================
# zip() - combine iterables
# =============================================================================

print("zip basic:")
result = list(zip([1, 2, 3], ["a", "b", "c"]))
print(result)  # [(1, 'a'), (2, 'b'), (3, 'c')]

print("zip different lengths:")
result = list(zip([1, 2, 3, 4, 5], ["x", "y"]))
print(result)  # [(1, 'x'), (2, 'y')]

print("zip three lists:")
result = list(zip([1, 2], ["a", "b"], [True, False]))
print(result)  # [(1, 'a', True), (2, 'b', False)]

print("zip empty lists:")
result = list(zip([], []))
print(result)  # []

print("zip single elements:")
result = list(zip([1], ["a"]))
print(result)  # [(1, 'a')]

print("zip strings:")
pairs = list(zip("abc", "123"))
print(pairs)  # [('a', '1'), ('b', '2'), ('c', '3')]

print("zip to dict:")
keys = ["a", "b", "c"]
values = [1, 2, 3]
d = dict(zip(keys, values))
print(d)  # {'a': 1, 'b': 2, 'c': 3}


# =============================================================================
# reversed() - reverse iteration
# =============================================================================

print("reversed to list:")
result = list(reversed([1, 2, 3, 4, 5]))
print(result)  # [5, 4, 3, 2, 1]

print("reversed another:")
result = list(reversed([10, 20, 30]))
print(result)  # [30, 20, 10]

print("reversed string:")
result = "".join(reversed("hello"))
print(result)  # olleh

print("reversed tuple:")
result = list(reversed((1, 2, 3)))
print(result)  # [3, 2, 1]

print("reversed empty:")
result = list(reversed([]))
print(result)  # []

print("reversed single element:")
result = list(reversed([42]))
print(result)  # [42]

print("nested reversed:")
result = list(reversed(list(reversed([1, 2, 3]))))
print(result)  # [1, 2, 3]


# =============================================================================
# Using results in comprehensions (single variable)
# =============================================================================

print("enumerate in comprehension:")
# Get just the indices
indices = [pair[0] for pair in enumerate(["a", "b", "c"])]
print(indices)  # [0, 1, 2]

print("zip in comprehension:")
sums = [pair[0] + pair[1] for pair in zip([1, 2, 3], [10, 20, 30])]
print(sums)  # [11, 22, 33]

print("reversed in comprehension:")
doubled = [x * 2 for x in reversed([1, 2, 3])]
print(doubled)  # [6, 4, 2]


print("builtins_iteration_simple tests done")
