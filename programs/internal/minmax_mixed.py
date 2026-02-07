"""Test min() and max() with mixed numeric types and edge cases."""

from __future__ import annotations


# Basic integer min/max
print(min(1, 2, 3))           # 1
print(max(1, 2, 3))           # 3
print(min([5, 2, 8, 1, 9]))   # 1
print(max([5, 2, 8, 1, 9]))   # 9

# Negative integers
print(min(-5, -2, -8))        # -8
print(max(-5, -2, -8))        # -2
print(min([-10, 0, 10]))      # -10
print(max([-10, 0, 10]))      # 10

# Float min/max
print(min(1.5, 2.5, 0.5))     # 0.5
print(max(1.5, 2.5, 0.5))     # 2.5
print(min([3.14, 2.71, 1.41]))  # 1.41
print(max([3.14, 2.71, 1.41]))  # 3.14

# Mixed int and float
print(min(1, 2.5, 3))         # 1
print(max(1, 2.5, 3))         # 3
print(min([1, 1.5, 2, 2.5]))  # 1
print(max([1, 1.5, 2, 2.5]))  # 2.5

# Edge cases with float
print(min(0.1, 0.2, 0.01))    # 0.01
print(max(0.1, 0.2, 0.01))    # 0.2

# Single element
print(min([42]))              # 42
print(max([42]))              # 42
print(min([3.14]))            # 3.14
print(max([3.14]))            # 3.14

# Two elements
print(min(5, 10))             # 5
print(max(5, 10))             # 10
print(min([5, 10]))           # 5
print(max([5, 10]))           # 10

# Already ordered
print(min([1, 2, 3, 4, 5]))   # 1
print(max([1, 2, 3, 4, 5]))   # 5

# Reverse ordered
print(min([5, 4, 3, 2, 1]))   # 1
print(max([5, 4, 3, 2, 1]))   # 5

# Duplicates
print(min([3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]))  # 1
print(max([3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]))  # 9

# All same value
print(min([7, 7, 7]))         # 7
print(max([7, 7, 7]))         # 7

# Negative floats
print(min(-1.5, -0.5, -2.5))  # -2.5
print(max(-1.5, -0.5, -2.5))  # -0.5

# Mixed negative int and float
print(min(-5, -3.5, -10))     # -10
print(max(-5, -3.5, -10))     # -3.5

# Zero handling
print(min(0, 1, -1))          # -1
print(max(0, 1, -1))          # 1
print(min(0, 0.5, -0.5))      # -0.5
print(max(0, 0.5, -0.5))      # 0.5


print("minmax_mixed tests done")
