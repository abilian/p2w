"""Test various builtin functions: chr, ord, callable, max, min with multiple args."""

from __future__ import annotations


# chr() - character from code point
print(chr(65))  # A
print(chr(97))  # a
print(chr(48))  # 0
print(chr(8364))  # € (Euro sign)


# ord() - code point from character
print(ord("A"))  # 65
print(ord("a"))  # 97
print(ord("0"))  # 48


# callable() - check if something is callable
def my_func():
    pass


class MyClass:
    pass


print(callable(my_func))  # True
print(callable(MyClass))  # True
print(callable(42))  # False
print(callable("hello"))  # False
print(callable([1, 2, 3]))  # False


# max() with multiple arguments
print(max(1, 2, 3))  # 3
print(max(5, 2, 8, 1))  # 8
print(max(-1, -5, -2))  # -1


# min() with multiple arguments
print(min(1, 2, 3))  # 1
print(min(5, 2, 8, 1))  # 1
print(min(-1, -5, -2))  # -5


# max/min with iterable (already covered, but include for completeness)
print(max([4, 2, 7]))  # 7
print(min([4, 2, 7]))  # 2


print("builtin_functions tests done")
