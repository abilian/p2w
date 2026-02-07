"""Test f-string formatting."""

from __future__ import annotations


# Basic f-string
name = "Alice"
print(f"Hello, {name}!")

# Multiple expressions
x = 10
y = 20
print(f"x={x}, y={y}")

# Expressions in f-strings
a = 5
b = 3
print(f"Sum: {a + b}")
print(f"Product: {a * b}")

# Method calls in f-strings
s = "hello"
print(f"Upper: {s.upper()}")

# Nested quotes
word = "world"
print(f'Hello, "{word}"')

# Numbers
pi = 3.14159
print(f"Pi is approximately {pi}")

# Integer
count = 42
print(f"Count: {count}")

# Dict value in f-string
data = {"key": "value"}
print(f"Data key: {data['key']}")

# Conditional expression in f-string
score = 85
print(f"Grade: {'pass' if score >= 60 else 'fail'}")


# Function call in f-string
def double(n):
    return n * 2


print(f"Doubled: {double(7)}")

# Multiple f-strings
first = "John"
last = "Doe"
full = f"{first} {last}"
print(f"Full name: {full}")

# Empty f-string part
print(f"Start{''}End")

# F-string with index access
nums = [10, 20, 30]
print(f"First: {nums[0]}")


# Attribute access
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y


p = Point(3, 4)
print(f"Point: ({p.x}, {p.y})")

# Escape braces
print(f"Braces: {{and}}")

# Complex expression
values = [1, 2, 3, 4, 5]
print(f"Sum of values: {sum(values)}")
print(f"Length: {len(values)}")
