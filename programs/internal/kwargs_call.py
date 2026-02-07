"""Test **kwargs in function calls."""

from __future__ import annotations


def greet(name, greeting="Hi", punctuation="!"):
    return greeting + " " + name + punctuation


# Test 1: Full kwargs
kwargs1 = {"name": "World", "greeting": "Hello"}
print(greet(**kwargs1))  # Hello World!


# Test 2: Partial kwargs (use default)
kwargs2 = {"name": "Alice"}
print(greet(**kwargs2))  # Hi Alice!


# Test 3: Mixed positional and kwargs
kwargs3 = {"punctuation": "?"}
print(greet("Bob", "Hello", **kwargs3))  # Hello Bob?


# Test 4: Regular call (no kwargs)
print(greet("Charlie"))  # Hi Charlie!


# Test 5: Single kwarg
kwargs5 = {"greeting": "Yo"}
print(greet("Dave", **kwargs5))  # Yo Dave!


# Test 6: Empty kwargs (should work like regular call)
kwargs6 = {}
print(greet("Eve", "Sup", **kwargs6))  # Sup Eve!


# Test 7: Override with later kwarg
def add(a, b, c=0):
    return a + b + c


kwargs7 = {"b": 10, "c": 5}
print(add(1, **kwargs7))  # 16


# Test 8: All keyword arguments
def info(x, y, z):
    return str(x) + "-" + str(y) + "-" + str(z)


kwargs8 = {"x": 1, "y": 2, "z": 3}
print(info(**kwargs8))  # 1-2-3


print("kwargs_call tests done")
