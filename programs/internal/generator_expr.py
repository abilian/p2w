"""Test generator expressions."""

from __future__ import annotations

# Basic generator expression with list()
squares = list(x * x for x in range(5))
print(squares)

# With condition
evens = list(x for x in range(10) if x % 2 == 0)
print(evens)

# Nested generators - check length and access individual items
pairs = list((x, y) for x in range(3) for y in range(2))
print(len(pairs))
first = pairs[0]
print(first[0], first[1])
last = pairs[5]
print(last[0], last[1])

# With tuple unpacking - print individual values
items = [(1, "a"), (2, "b"), (3, "c")]
values = list(v for k, v in items)
for v in values:
    print(v)

# In sum()
total = sum(x for x in range(5))
print(total)

# In any()/all() - compare with explicit True/False
has_positive = any(x > 0 for x in [-1, 0, 1, 2])
if has_positive:
    print("has positive")
else:
    print("no positive")

all_positive = all(x > 0 for x in [1, 2, 3])
if all_positive:
    print("all positive")
else:
    print("not all positive")

# In join()
result = ",".join(str(x) for x in range(5))
print(result)

# Generator with complex expression
doubled = list(x * 2 for x in range(3))
print(doubled)
