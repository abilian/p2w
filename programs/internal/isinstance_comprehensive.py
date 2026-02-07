"""Test isinstance() with various types including tuple of types."""

from __future__ import annotations


# Basic type checks
print(isinstance(42, int))         # True
print(isinstance(42, str))         # False
print(isinstance(3.14, float))     # True
print(isinstance(3.14, int))       # False
print(isinstance("hello", str))    # True
print(isinstance("hello", int))    # False
print(isinstance(True, bool))      # True
print(isinstance(False, bool))     # True

# Collections
print(isinstance([1, 2], list))    # True
print(isinstance([], list))        # True
print(isinstance((1, 2), tuple))   # True
print(isinstance((), tuple))       # True
print(isinstance({"a": 1}, dict))  # True
print(isinstance({}, dict))        # True

# Bytes
print(isinstance(b"hello", bytes))  # True
print(isinstance(b"", bytes))       # True

# Tuple of types
print(isinstance(42, (int, str)))       # True
print(isinstance("hi", (int, str)))     # True
print(isinstance(3.14, (int, str)))     # False
print(isinstance(3.14, (int, float)))   # True
print(isinstance([1], (list, tuple)))   # True
print(isinstance((1,), (list, tuple)))  # True
print(isinstance({}, (list, tuple)))    # False
print(isinstance({}, (list, dict)))     # True

# Multiple types in tuple
print(isinstance("x", (int, float, str, bool)))  # True
print(isinstance(3.14, (int, float, str, bool))) # True
print(isinstance(True, (int, float, str, bool))) # True
print(isinstance(42, (int, float, str, bool)))   # True
print(isinstance([], (int, float, str, bool)))   # False


# User-defined classes
class Animal:
    pass


class Dog(Animal):
    pass


class Cat(Animal):
    pass


class Bird:
    pass


a = Animal()
d = Dog()
c = Cat()
b = Bird()

# isinstance with classes
print(isinstance(d, Dog))       # True
print(isinstance(d, Animal))    # True (inheritance)
print(isinstance(d, Cat))       # False
print(isinstance(a, Animal))    # True
print(isinstance(a, Dog))       # False
print(isinstance(b, Animal))    # False


# isinstance with tuple of classes
print(isinstance(d, (Dog, Cat)))      # True
print(isinstance(c, (Dog, Cat)))      # True
print(isinstance(a, (Dog, Cat)))      # False
print(isinstance(d, (Animal, Bird)))  # True (Dog is Animal)
print(isinstance(b, (Animal, Bird)))  # True


# Mixed builtin and class types
print(isinstance(42, (int, Animal)))  # True
print(isinstance(d, (int, Animal)))   # True
print(isinstance("x", (int, Animal))) # False


# Edge cases: empty collections
print(isinstance([], list))      # True
print(isinstance({}, dict))      # True
print(isinstance((), tuple))     # True


# Large integers
print(isinstance(10**20, int))   # True
print(isinstance(-10**20, int))  # True


print("isinstance_comprehensive tests done")
