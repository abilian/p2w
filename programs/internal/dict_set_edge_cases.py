"""Test dict and set edge cases and operations."""

from __future__ import annotations


# === DICT EDGE CASES ===

# Empty dict
d = {}
print(len(d))          # 0
print(bool(d))         # False
d["key"] = "value"
print(len(d))          # 1
print(bool(d))         # True

# String keys
d = {"hello": 1, "world": 2}
print("hello" in d)    # True
print("foo" in d)      # False

# Integer keys
d = {0: "zero", 1: "one", 2: "two"}
print(d[0])            # zero
print(d.get(3))        # None
print(d.get(3, "default"))  # default

# Overwriting values
d = {"a": 1}
d["a"] = 2
print(d["a"])          # 2
d["a"] = d["a"] + 10
print(d["a"])          # 12

# Dict equality
d1 = {"a": 1, "b": 2}
d2 = {"b": 2, "a": 1}  # Same items, different order
d3 = {"a": 1}
print(d1 == d2)        # True
print(d1 == d3)        # False
print(d1 != d3)        # True


# === SET EDGE CASES ===

# Empty set
s = set()
print(len(s))          # 0
print(bool(s))         # False

# Set from list
s = set([1, 2, 2, 3, 3, 3])
print(len(s))          # 3 (duplicates removed)

# Set membership
s = {1, 2, 3, 4, 5}
print(1 in s)          # True
print(10 in s)         # False

# Set add
s = {1, 2}
s.add(3)
print(len(s))          # 3
s.add(2)               # Adding existing element
print(len(s))          # 3 (no change)

# Set discard (no error if missing)
s = {1, 2, 3}
s.discard(2)
print(len(s))          # 2
print(2 in s)          # False
s.discard(99)          # No error
print(len(s))          # 2

# Set remove (test existing element)
s = {1, 2, 3}
s.remove(2)
print(len(s))          # 2

# Set copy
original = {1, 2, 3}
copied = original.copy()
copied.add(4)
print(4 in original)   # False
print(4 in copied)     # True

# Set clear
s = {1, 2, 3}
s.clear()
print(len(s))          # 0

# Iterating over dict keys
d = {"a": 1, "b": 2}
keys = []
for k in d:
    keys.append(k)
print(len(keys))       # 2

# Dict keys as list
d = {"a": 1, "b": 2, "c": 3}
k = list(d.keys())
print(len(k))          # 3

# Dict values as list
v = list(d.values())
print(len(v))          # 3


print("dict_set_edge_cases tests done")
