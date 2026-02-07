"""Test slice expressions."""

from __future__ import annotations

# Basic slices
a = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
print(a[2:5])
print(a[:3])
print(a[7:])
print(a[:])

# Negative indices
print(a[-3:])
print(a[:-2])
print(a[-5:-2])

# Step slices
print(a[::2])
print(a[1::2])
print(a[::-1])  # Reverse
print(a[8:2:-1])

# String slices
s = "hello world"
print(s[0:5])
print(s[6:])
print(s[::-1])

# Slice assignment
b = [0, 1, 2, 3, 4]
b[1:3] = [10, 20]
print(b)

b[2:] = [100]
print(b)
