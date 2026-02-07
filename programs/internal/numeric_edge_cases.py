"""Test numeric operations and edge cases."""

from __future__ import annotations


# Integer arithmetic
print(10 + 3)     # 13
print(10 - 3)     # 7
print(10 * 3)     # 30
print(10 // 3)    # 3
print(10 % 3)     # 1
print(10 ** 3)    # 1000

# Division (true division)
print(10 / 4)     # 2.5
print(5 / 2)      # 2.5
print(-5 / 2)     # -2.5

# Float arithmetic
print(1.5 + 2.3)  # 3.8
print(5.5 - 2.2)  # 3.3
print(2.5 * 3.0)  # 7.5
print(7.5 / 3.0)  # 2.5

# Mixed int and float
print(5 + 2.5)    # 7.5
print(5.5 - 2)    # 3.5
print(3 * 1.5)    # 4.5
print(9 / 2.0)    # 4.5

# Negative numbers
print(-5 + 3)     # -2
print(-5 - 3)     # -8
print(-5 * -3)    # 15
print(-5 * 3)     # -15

# Zero handling
print(0 + 5)      # 5
print(0 - 5)      # -5
print(0 * 100)    # 0
print(0 // 5)     # 0
print(0 % 5)      # 0

# Large numbers (still i31)
print(1000000 + 1000000)  # 2000000
print(1000000 * 100)      # 100000000

# Comparison operators
print(5 > 3)      # True
print(5 < 3)      # False
print(5 >= 5)     # True
print(5 <= 4)     # False
print(5 == 5)     # True
print(5 != 3)     # True

# Float comparisons
print(3.14 > 2.71)   # True
print(3.14 < 2.71)   # False
print(1.0 == 1.0)    # True
print(1.5 != 1.5)    # False

# Mixed comparisons
print(5 > 3.5)    # True
print(3.5 < 5)    # True
print(5 == 5.0)   # True

# Chained comparisons
x = 5
print(1 < x < 10)    # True
print(1 < x < 3)     # False
print(1 <= x <= 5)   # True

# abs()
print(abs(5))     # 5
print(abs(-5))    # 5
print(abs(0))     # 0
print(abs(-3.14)) # 3.14
print(abs(3.14))  # 3.14

# Unary minus
print(-5)         # -5
print(-(-5))      # 5
print(-3.14)      # -3.14

# Unary plus
print(+5)         # 5
print(+(-5))      # -5

# Boolean contexts
print(bool(0))    # False
print(bool(1))    # True
print(bool(-1))   # True


print("numeric_edge_cases tests done")
