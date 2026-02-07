"""Test boolean and None handling."""

from __future__ import annotations


# Helper to print boolean as string
def bool_str(b):
    if b:
        return "yes"
    return "no"


# Boolean from comparison
print(bool_str(5 > 3))
print(bool_str(5 < 3))

# None comparison with is
x = None
print(bool_str(x is None))
print(bool_str(x is not None))

y = 5
print(bool_str(y is None))
print(bool_str(y is not None))

# Truthiness of various types
# Numbers
print(bool_str(0))
print(bool_str(1))
print(bool_str(-1))

# Strings
print(bool_str(""))
print(bool_str("hello"))

# Lists
print(bool_str([]))
print(bool_str([1, 2, 3]))

# Dicts
print(bool_str({}))
print(bool_str({"a": 1}))

# Boolean in if statement
if 1:
    print("true branch")

if 0:
    print("should not print")
else:
    print("false branch")

# Truthiness in if
if [1, 2, 3]:
    print("non-empty list is truthy")

if not []:
    print("empty list is falsy")

if "hello":
    print("non-empty string is truthy")

if not "":
    print("empty string is falsy")


# Default value pattern (now working with None defaults!)
def greet(name=None):
    if name is None:
        name = "World"
    return "Hello, " + name


print(greet())
print(greet("Alice"))

# Or for default
a = None
b = a or "default"
print(b)

c = "value"
d = c or "default"
print(d)

# And short-circuit
result1 = 1 and "yes"
print(result1)
result2 = 0 and "yes"
print(result2)

# Complex boolean expressions
x = 5
y = 10
z = 0

print(x and y)
print(x and z)
print(z or y)
print(z or x or y)

# Boolean conversion with not
print(bool_str(not 0))
print(bool_str(not 1))
print(bool_str(not ""))
print(bool_str(not "text"))
print(bool_str(not []))
print(bool_str(not [1]))
