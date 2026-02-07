"""Test map and filter (simplified - no try/except)."""

from __future__ import annotations


# =============================================================================
# map() edge cases
# =============================================================================

print("map with empty list:")
result = list(map(lambda x: x * 2, []))
print(result)  # []

print("map with single element:")
result = list(map(lambda x: x * 2, [5]))
print(result)  # [10]

print("map with type conversion:")
result = list(map(str, [1, 2, 3]))
print(result)  # ['1', '2', '3']

result = list(map(int, ["1", "2", "3"]))
print(result)  # [1, 2, 3]

result = list(map(float, [1, 2, 3]))
print(result)  # [1.0, 2.0, 3.0]

print("map with len:")
result = list(map(len, ["a", "bb", "ccc"]))
print(result)  # [1, 2, 3]

print("map with abs:")
result = list(map(abs, [-1, 2, -3, 4, -5]))
print(result)  # [1, 2, 3, 4, 5]

print("map with complex lambda:")
result = list(map(lambda x: x ** 2 + 1, [1, 2, 3, 4]))
print(result)  # [2, 5, 10, 17]

print("map on string:")
result = list(map(lambda c: c.upper(), "hello"))
print(result)  # ['H', 'E', 'L', 'L', 'O']

print("map on tuple:")
result = list(map(lambda x: x + 1, (1, 2, 3)))
print(result)  # [2, 3, 4]


# =============================================================================
# filter() edge cases
# =============================================================================

print("filter with empty list:")
result = list(filter(lambda x: x > 0, []))
print(result)  # []

print("filter with single element (passes):")
result = list(filter(lambda x: x > 0, [5]))
print(result)  # [5]

print("filter with single element (fails):")
result = list(filter(lambda x: x > 0, [-5]))
print(result)  # []

print("filter all pass:")
result = list(filter(lambda x: x > 0, [1, 2, 3, 4, 5]))
print(result)  # [1, 2, 3, 4, 5]

print("filter none pass:")
result = list(filter(lambda x: x > 10, [1, 2, 3, 4, 5]))
print(result)  # []

print("filter with None (truthy filter):")
result = list(filter(None, [0, 1, 2, 0, 3, 0, 4]))
print(result)  # [1, 2, 3, 4]

print("filter None on strings:")
result = list(filter(None, ["", "a", "", "b", "c", ""]))
print(result)  # ['a', 'b', 'c']

print("filter on tuple:")
result = list(filter(lambda x: x % 2 == 0, (1, 2, 3, 4, 5, 6)))
print(result)  # [2, 4, 6]


# =============================================================================
# Chaining map and filter
# =============================================================================

print("filter then map:")
nums = [-3, -1, 0, 2, 4]
result = list(map(lambda x: x ** 2, filter(lambda x: x > 0, nums)))
print(result)  # [4, 16]

print("map then filter:")
nums = [1, 2, 3, 4, 5]
result = list(filter(lambda x: x > 5, map(lambda x: x * 2, nums)))
print(result)  # [6, 8, 10]


# =============================================================================
# map/filter with named functions
# =============================================================================

def square(x):
    return x * x

def is_positive(x):
    return x > 0

def is_even(x):
    return x % 2 == 0

print("map with named function:")
result = list(map(square, [1, 2, 3, 4, 5]))
print(result)  # [1, 4, 9, 16, 25]

print("filter with named function:")
result = list(filter(is_positive, [-2, -1, 0, 1, 2]))
print(result)  # [1, 2]

print("combined named functions:")
nums = [-3, -2, -1, 0, 1, 2, 3]
result = list(map(square, filter(is_positive, nums)))
print(result)  # [1, 4, 9]


# =============================================================================
# Practical examples
# =============================================================================

print("practical: transform strings:")
words = ["hello", "WORLD", "Python"]
result = list(map(lambda s: s.lower(), words))
print(result)  # ['hello', 'world', 'python']

print("practical: filter and sum:")
nums = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
even_sum = sum(filter(is_even, nums))
print(even_sum)  # 30 (2+4+6+8+10)

print("practical: length filtering:")
words = ["a", "bb", "ccc", "dddd", "eeeee"]
long_words = list(filter(lambda w: len(w) > 2, words))
print(long_words)  # ['ccc', 'dddd', 'eeeee']


print("builtins_map_filter_simple tests done")
