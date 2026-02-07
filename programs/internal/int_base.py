"""Test int() with base parameter."""

from __future__ import annotations

# Base 10 (default)
print(int("42"))
print(int("42", 10))

# Base 16 (hex)
print(int("ff", 16))
print(int("FF", 16))
print(int("10", 16))

# Base 2 (binary)
print(int("1010", 2))
print(int("11111111", 2))

# Base 8 (octal)
print(int("77", 8))
print(int("10", 8))

# Other bases
print(int("z", 36))  # 35
print(int("10", 36))  # 36
