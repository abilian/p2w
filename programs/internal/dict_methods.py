"""Test dict methods."""

from __future__ import annotations


# keys(), values(), items()
d = {"a": 1, "b": 2, "c": 3}
keys = sorted(d.keys())
print(len(keys))  # 3
print(keys[0])  # a
print(keys[1])  # b

values = sorted(d.values())
print(values[0])  # 1
print(values[2])  # 3


# Iteration
d = {"x": 10, "y": 20}
for key in sorted(d.keys()):
    print(key + "=" + str(d[key]))


# get()
d = {"name": "Alice", "age": 30}
print(d.get("name"))  # Alice
print(d.get("missing"))  # None
print(d.get("missing", "default"))  # default


# setdefault()
d = {"a": 1}
print(d.setdefault("a", 99))  # 1 (key exists)
print(d.setdefault("b", 2))  # 2 (key missing)
print(d["b"])  # 2


# pop()
d = {"a": 1, "b": 2, "c": 3}
print(d.pop("b"))  # 2
print("b" in d)  # False
print(d.pop("missing", "default"))  # default


# update()
d = {"a": 1, "b": 2}
d.update({"b": 20, "c": 3})
print(d["b"])  # 20
print(d["c"])  # 3


# clear()
d = {"a": 1, "b": 2}
d.clear()
print(len(d))  # 0


# copy()
original = {"a": 1, "b": 2}
copied = original.copy()
copied["c"] = 3
print("c" in original)  # False
print("c" in copied)  # True


# Membership testing
d = {"name": "Bob", "age": 25}
print("name" in d)  # True
print("email" in d)  # False


# Dict comprehension
squares = {x: x * x for x in range(1, 6)}
print(squares[3])  # 9


# Merging dicts
d1 = {"a": 1, "b": 2}
d2 = {"c": 3, "d": 4}
merged = d1.copy()
merged.update(d2)
print(len(merged))  # 4


# Nested dict operations
nested = {"user": {"name": "Alice"}}
print(nested["user"]["name"])  # Alice


# len()
d = {"a": 1, "b": 2}
print(len(d))  # 2


print("dict_methods tests done")
