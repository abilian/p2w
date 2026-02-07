"""Test type conversion functions: bool(), float(), str() with various inputs."""

from __future__ import annotations


# bool() with arguments
print(bool(1))  # True
print(bool(0))  # False
print(bool("hello"))  # True
print(bool(""))  # False
print(bool([1, 2]))  # True
print(bool([]))  # False
print(bool(None))  # False


# float() with string argument
# Note: whole number floats display without .0 in JS (known limitation)
print(float("3.14"))  # 3.14
print(float("-2.5"))  # -2.5
print(float("42.5"))  # 42.5
print(float("0.001"))  # 0.001


# str() called on a string (identity)
s = "hello"
print(str(s))  # hello
print(str("world"))  # world


# str() with various types (some already covered, included for completeness)
print(str(123))  # 123
print(str(True))  # True
print(str(False))  # False
print(str(None))  # None


# int() with different bases (exercise the code path more explicitly)
x = "ff"
base = 16
print(int(x, base))  # 255

y = "1010"
print(int(y, 2))  # 10

z = "777"
print(int(z, 8))  # 511


print("type_conversions tests done")
