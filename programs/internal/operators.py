"""Test operators."""

from __future__ import annotations


# Comparison operators - use conditional to print string
def bool_str(b):
    if b:
        return "yes"
    return "no"


print(bool_str(5 > 3))
print(bool_str(5 < 3))
print(bool_str(5 >= 5))
print(bool_str(5 <= 4))
print(bool_str(5 == 5))
print(bool_str(5 != 4))

# Chained comparisons
x = 5
print(bool_str(1 < x < 10))
print(bool_str(1 < x < 3))
print(bool_str(1 <= x <= 5))

# Logical operators
print(bool_str(1 and 1))
print(bool_str(1 and 0))
print(bool_str(0 or 1))
print(bool_str(0 or 0))
print(bool_str(not 1))
print(bool_str(not 0))

# Short-circuit evaluation
a = 0
b = 5
result = a or b
print(result)

result = b and a
print(result)

# In operator
items = [1, 2, 3, 4, 5]
print(bool_str(3 in items))
print(bool_str(10 in items))
print(bool_str(10 not in items))

# In with strings
s = "hello"
print(bool_str("ell" in s))
print(bool_str("xyz" in s))

# In with dict
d = {"a": 1, "b": 2}
print(bool_str("a" in d))
print(bool_str("c" in d))

# Bitwise operators
print(5 & 3)  # 0101 & 0011 = 0001
print(5 | 3)  # 0101 | 0011 = 0111
print(5 ^ 3)  # 0101 ^ 0011 = 0110
print(~5)  # bitwise not
print(2 << 3)  # left shift
print(16 >> 2)  # right shift

# Arithmetic operators
print(10 + 3)
print(10 - 3)
print(10 * 3)
print(10 // 3)
print(10 % 3)
print(2**3)

# Unary operators
x = 5
print(-x)
print(+x)

# Identity operators (is/is not)
a = None
print(bool_str(a is None))
print(bool_str(a is not None))

b = [1, 2, 3]
c = b
d = [1, 2, 3]
print(bool_str(b is c))
print(bool_str(b is d))
