"""Test dict unpacking with ** operator."""

from __future__ import annotations


# Basic dict unpacking
d1 = {"a": 1, "b": 2}
d2 = {"c": 3, "d": 4}
merged = {**d1, **d2}
print(merged["a"])  # 1
print(merged["c"])  # 3
print(len(merged))  # 4


# Unpacking with additional keys
base = {"x": 10, "y": 20}
extended = {**base, "z": 30}
print(extended["x"])  # 10
print(extended["z"])  # 30
print(len(extended))  # 3


# Later values override earlier ones
first = {"a": 1, "b": 2}
second = {"b": 100, "c": 3}
combined = {**first, **second}
print(combined["a"])  # 1
print(combined["b"])  # 100 (overridden)
print(combined["c"])  # 3


# Mixed unpacking and explicit keys
d = {"k1": "v1"}
result = {"k0": "v0", **d, "k2": "v2"}
print(result["k0"])  # v0
print(result["k1"])  # v1
print(result["k2"])  # v2


# Empty dict unpacking
empty = {}
with_empty = {**empty, "a": 1}
print(with_empty["a"])  # 1
print(len(with_empty))  # 1


# Multiple unpacks with override in middle
a = {"x": 1}
b = {"x": 2, "y": 3}
c = {"z": 4}
result2 = {**a, **b, **c}
print(result2["x"])  # 2 (from b, overrides a)
print(result2["y"])  # 3
print(result2["z"])  # 4


# Unpacking in function call context (indirect test)
def greet(name, greeting):
    return greeting + " " + name


kwargs = {"name": "World", "greeting": "Hello"}
# Note: **kwargs in function calls may have separate handling
# This test focuses on dict literal unpacking


print("dict_unpacking tests done")
