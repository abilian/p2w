"""Test boolean logic and comparison operations."""

from __future__ import annotations


# Basic boolean values
print(True)
print(False)

# Boolean negation
print(not True)   # False
print(not False)  # True

# And operations
print(True and True)    # True
print(True and False)   # False
print(False and True)   # False
print(False and False)  # False

# Or operations
print(True or True)    # True
print(True or False)   # True
print(False or True)   # True
print(False or False)  # False

# Combined operations
print(True and True or False)    # True
print(False or True and True)    # True
print(not True or False)         # False
print(not False and True)        # True

# Short-circuit evaluation
def returns_true():
    print("called_true")
    return True

def returns_false():
    print("called_false")
    return False

# Short-circuit and (second not called when first is False)
print(False and returns_true())

# Short-circuit or (second not called when first is True)
print(True or returns_false())

# All three called
print(returns_true() and returns_true() and returns_true())

# Comparison operators
print(5 == 5)   # True
print(5 == 6)   # False
print(5 != 6)   # True
print(5 != 5)   # False

print(5 < 6)    # True
print(5 < 5)    # False
print(5 <= 5)   # True
print(5 <= 4)   # False

print(6 > 5)    # True
print(5 > 5)    # False
print(5 >= 5)   # True
print(4 >= 5)   # False

# String equality (but not ordering)
print("abc" == "abc")  # True
print("abc" != "def")  # True

# Chained comparisons
x = 5
print(1 < x < 10)      # True
print(1 < x < 4)       # False
print(0 < x < 10 < 20) # True

# Comparison with boolean result in expression
y = 3 if 5 > 3 else 7
print(y)  # 3

# Boolean in condition
if True:
    print("true branch")

if not False:
    print("not false branch")

# Multiple conditions
a = 5
b = 10
c = 15

if a < b and b < c:
    print("all in order")

if a > b or b < c:
    print("at least one true")

# is and is not with None
print(None is None)      # True
print(None is not True)  # True

# Boolean conversion
print(bool(1))    # True
print(bool(0))    # False
print(bool(-1))   # True
print(bool(""))   # False
print(bool("a"))  # True
print(bool([]))   # False
print(bool([1]))  # True

# in operator
print(1 in [1, 2, 3])       # True
print(4 in [1, 2, 3])       # False
print("a" in "abc")         # True
print("z" in "abc")         # False
print("key" in {"key": 1})  # True
print("x" in {"key": 1})    # False

# not in operator
print(1 not in [1, 2, 3])   # False
print(4 not in [1, 2, 3])   # True

# Complex boolean expressions
def is_valid(n):
    return n > 0 and n < 100 and n % 2 == 0

print(is_valid(50))   # True
print(is_valid(-5))   # False
print(is_valid(101))  # False
print(is_valid(51))   # False

# any/all with boolean lists
print(any([True, False, False]))   # True
print(any([False, False, False]))  # False
print(all([True, True, True]))     # True
print(all([True, False, True]))    # False

# Comparison returning value for and/or
print(5 and 10)       # 10 (last truthy)
print(0 and 10)       # 0 (first falsy)
print(5 or 10)        # 5 (first truthy)
print(0 or 10)        # 10 (first truthy)
print(0 or "" or [])  # [] (last value)

# None comparisons
print(None == None)   # True
print(None != 0)      # True

# Filter-like with booleans
nums = [1, 2, 3, 4, 5, 6]
evens = [n for n in nums if n % 2 == 0]
print(evens)  # [2, 4, 6]


print("boolean_logic tests done")
