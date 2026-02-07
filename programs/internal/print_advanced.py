"""Test print() with sep argument and issubclass()."""

from __future__ import annotations


# Basic print with separator
print(1, 2, 3, sep="-")  # 1-2-3


# Print with custom separator
print("a", "b", "c", sep=", ")  # a, b, c


# Print with empty separator
print("x", "y", "z", sep="")  # xyz


# Note: print with end="" has known limitation with console.log
# console.log always adds newline, but Python print with end="" doesn't
# This is documented in local-notes/issues.md


# issubclass tests
class Animal:
    pass


class Dog(Animal):
    pass


class Cat(Animal):
    pass


print(issubclass(Dog, Animal))  # True
print(issubclass(Cat, Animal))  # True
print(issubclass(Dog, object))  # True


# Multiple values with different types
print(1, "two", 3.5, sep=" | ")  # 1 | two | 3.5


# Boolean values with separator
print(True, False, sep=" and ")  # True and False


print("print_advanced tests done")
