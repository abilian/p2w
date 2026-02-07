"""Test Set literals."""

from __future__ import annotations

# Basic set literal
s = {1, 2, 3}
print(len(s))

# Set with duplicates (should dedupe)
s2 = {1, 1, 2, 2, 3}
print(len(s2))

# Set operations - add
s3 = {1, 2, 3}
s3.add(4)
print(len(s3))
s3.add(4)  # Adding duplicate
print(len(s3))  # Should still be 4

# Variables in set literal
x = 10
y = 20
s4 = {x, y, 30}
print(len(s4))

# Empty set created via set()
s5 = set()
print(len(s5))
s5.add(1)
print(len(s5))
