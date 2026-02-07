"""Test hash-based collection operations.

This tests the new hash table-based dict and set types
with O(1) average-case operations.
Note: Currently dicts/sets still use PAIR chains by default.
This file will work once we enable hash-based collections.
"""

from __future__ import annotations


# Test basic dict operations
d = {"a": 1, "b": 2, "c": 3}
print(d["a"])  # 1
print(d["b"])  # 2
print(d["c"])  # 3

# Test dict modification
d["d"] = 4
print(d["d"])  # 4

# Test dict length
print(len(d))  # 4

# Test key lookup
print("a" in d)  # True
print("z" in d)  # False
print("z" not in d)  # True

# Test dict with integer keys
nums = {1: "one", 2: "two", 3: "three"}
print(nums[1])  # one
print(nums[2])  # two

# Test set operations
# s = {1, 2, 3}
# print(1 in s)  # True
# print(5 in s)  # False

# Test set with strings
# words = {"hello", "world"}
# print("hello" in words)  # True
# print("foo" in words)  # False

# Test dict iteration
total = 0
for k in d:
    total = total + d[k]
print(total)  # 10

# Test empty dict
empty = {}
print(len(empty))  # 0
if not empty:
    print("empty dict is falsy")

# Test dict with mixed key types
# mixed = {1: "int", "a": "str", True: "bool"}
# print(len(mixed))  # Should be 2 since True == 1

print("hash_collections tests done")
