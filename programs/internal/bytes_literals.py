"""Test bytes literals."""

from __future__ import annotations

# Basic bytes literal
b = b"hello"
print(len(b))

# Access individual bytes
print(b[0])  # 'h' = 104
print(b[1])  # 'e' = 101
print(b[4])  # 'o' = 111

# Empty bytes
empty = b""
print(len(empty))

# Bytes with escape sequences
esc = b"\x00\x01\x02"
print(len(esc))
print(esc[0])
print(esc[1])
print(esc[2])

# Single char bytes
single = b"A"
print(len(single))
print(single[0])
