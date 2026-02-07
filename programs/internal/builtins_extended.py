"""Test extended builtin functions: abs, round, map, filter."""

from __future__ import annotations


# abs() - absolute value
print(abs(5))      # 5
print(abs(-5))     # 5
print(abs(0))      # 0
print(abs(-3.14))  # 3.14

# round() - rounding
print(round(3.14159))      # 3
print(round(3.7))          # 4
print(round(2.5))          # 2 (banker's rounding)
print(round(3.5))          # 4
print(round(-2.5))         # -2

# sum() basic
print(sum([1, 2, 3]))         # 6
print(sum([10, 20, 30]))      # 60

# len() on various types
print(len([1, 2, 3, 4, 5]))   # 5
print(len("hello"))            # 5
print(len({1, 2, 3}))          # 3
print(len({"a": 1, "b": 2}))   # 2
print(len([]))                 # 0

# sorted() basic
print(sorted([3, 1, 4, 1, 5, 9, 2, 6]))  # [1, 1, 2, 3, 4, 5, 6, 9]
print(sorted([5, 2, 8, 1, 9]))           # [1, 2, 5, 8, 9]
print(sorted([]))                         # []

# sorted() with reverse
print(sorted([3, 1, 4, 1, 5], reverse=True))  # [5, 4, 3, 1, 1]

# any() and all()
print(any([True, False, False]))   # True
print(any([False, False, False]))  # False
print(any([]))                      # False

print(all([True, True, True]))     # True
print(all([True, False, True]))    # False
print(all([]))                      # True

# any/all with expressions
nums = [2, 4, 6, 8]
print(all(n % 2 == 0 for n in nums))  # True (all even)
print(any(n > 7 for n in nums))       # True (8 > 7)

# map() - apply function to iterable
def double(x):
    return x * 2

result = list(map(double, [1, 2, 3, 4]))
print(result)  # [2, 4, 6, 8]

# map() with lambda
result = list(map(lambda x: x ** 2, [1, 2, 3, 4, 5]))
print(result)  # [1, 4, 9, 16, 25]

# filter() - filter items
def is_even(x):
    return x % 2 == 0

result = list(filter(is_even, [1, 2, 3, 4, 5, 6]))
print(result)  # [2, 4, 6]

# filter() with lambda
result = list(filter(lambda x: x > 3, [1, 2, 3, 4, 5]))
print(result)  # [4, 5]

# Combining map and filter
result = list(map(lambda x: x * 2, filter(is_even, [1, 2, 3, 4, 5, 6])))
print(result)  # [4, 8, 12]

# int() with base
print(int("ff", 16))    # 255
print(int("1010", 2))   # 10
print(int("777", 8))    # 511

# repr() for debugging
print(repr("hello"))     # 'hello'
print(repr([1, 2, 3]))   # [1, 2, 3]
print(repr(None))        # None

# Nested function with builtins
def process(nums):
    doubled = list(map(lambda x: x * 2, nums))
    evens = list(filter(lambda x: x % 4 == 0, doubled))
    return sum(evens)

print(process([1, 2, 3, 4, 5]))  # 12 (4 + 8)


print("builtins_extended tests done")
