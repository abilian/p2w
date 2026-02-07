"""Test tuples."""

from __future__ import annotations


# Basic tuple creation and access
t = (1, 2, 3)
print(t[0])
print(t[1])
print(t[2])

# Single element tuple (needs comma)
single = (42,)
print(single[0])

# Tuple without parentheses
implicit = 1, 2, 3
print(implicit[0])

# Empty tuple
empty = ()
print(len(empty))

# Tuple indexing - including negative indices (now fixed!)
t = (10, 20, 30, 40, 50)
print(t[0])
print(t[2])
print(t[-1])  # Negative indexing now works
print(t[-2])

# Tuple slicing - print elements
sliced = t[1:4]
print(sliced[0])
print(sliced[1])

# Tuple unpacking
a, b, c = (1, 2, 3)
print(a)
print(b)
print(c)

# Tuple unpacking with starred
first, *rest = (1, 2, 3, 4, 5)
print(first)
print(len(rest))

*init, last = (1, 2, 3, 4, 5)
print(len(init))
print(last)

# Swap using tuples
x, y = 10, 20
x, y = y, x
print(x)
print(y)

# Nested tuples
nested = ((1, 2), (3, 4), (5, 6))
print(nested[1][0])
print(nested[1][1])
print(nested[-1][0])  # Negative index in nested

# Tuple concatenation
t1 = (1, 2)
t2 = (3, 4)
t3 = t1 + t2
print(len(t3))
print(t3[2])

# Tuple repetition
repeated = (1, 2) * 3
print(len(repeated))

# Tuple length
print(len((1, 2, 3, 4)))

# Membership test
t = (1, 2, 3, 4, 5)
if 3 in t:
    print("found 3")
if 10 not in t:
    print("10 not found")

# Tuple in for loop
for item in (10, 20, 30):
    print(item)

# Nested unpacking
pairs = [(1, 2), (3, 4), (5, 6)]
for a, b in pairs:
    print(a + b)


# Tuple as function return
def get_coords():
    return (10, 20)


x, y = get_coords()
print(x)
print(y)

# Mixed types in tuple - access elements
mixed = (1, "hello", 3.14)
print(mixed[1])
