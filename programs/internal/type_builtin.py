"""Test type() builtin with various types."""

from __future__ import annotations


# Basic types
print(type(42))           # <class 'int'>
print(type(3.14))         # <class 'float'>
print(type("hello"))      # <class 'str'>
print(type(True))         # <class 'bool'>
print(type(False))        # <class 'bool'>

# Collections
print(type([1, 2, 3]))    # <class 'list'>
print(type((1, 2, 3)))    # <class 'tuple'>
print(type({"a": 1}))     # <class 'dict'>
print(type([]))           # <class 'list'>
print(type(()))           # <class 'tuple'>
print(type({}))           # <class 'dict'>

# Bytes
print(type(b"hello"))     # <class 'bytes'>
print(type(b""))          # <class 'bytes'>

# Large integers
print(type(10**20))       # <class 'int'>
print(type(-10**20))      # <class 'int'>


# User-defined classes
class Empty:
    pass


class Animal:
    def __init__(self, name: str):
        self.name = name


class Dog(Animal):
    def bark(self):
        return "Woof!"


e = Empty()
a = Animal("Generic")
d = Dog("Rex")

# Type names only (not full module path)
t_e = str(type(e))
t_a = str(type(a))
t_d = str(type(d))

print("Empty" in t_e)    # True
print("Animal" in t_a)   # True
print("Dog" in t_d)      # True

# Nested structures
nested = [[1, 2], [3, 4]]
print(type(nested))          # <class 'list'>
print(type(nested[0]))       # <class 'list'>

mixed = [1, "two", 3.0]
print(type(mixed))           # <class 'list'>


print("type_builtin tests done")
