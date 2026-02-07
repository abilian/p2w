"""Test sorted() with various types and edge cases."""

from __future__ import annotations


# Integer sorting
nums = [3, 1, 4, 1, 5, 9, 2, 6]
print(sorted(nums))  # [1, 1, 2, 3, 4, 5, 6, 9]

# Float sorting
floats = [3.14, 2.71, 1.41, 1.73]
print(sorted(floats))  # [1.41, 1.73, 2.71, 3.14]

# Negative numbers
negatives = [-5, 3, -1, 7, -3, 0]
print(sorted(negatives))  # [-5, -3, -1, 0, 3, 7]

# Mixed int and float
mixed = [1, 2.5, 3, 0.5, 2]
print(sorted(mixed))  # [0.5, 1, 2, 2.5, 3]

# String sorting
words = ["banana", "apple", "cherry", "date"]
print(sorted(words))  # ['apple', 'banana', 'cherry', 'date']

# Case sensitive string sorting
mixed_case = ["Banana", "apple", "Cherry"]
print(sorted(mixed_case))  # ['Banana', 'Cherry', 'apple']

# Empty strings
with_empty = ["", "a", "b", ""]
print(sorted(with_empty))  # ['', '', 'a', 'b']

# Single character strings
chars = ["z", "a", "m", "b", "y"]
print(sorted(chars))  # ['a', 'b', 'm', 'y', 'z']

# reverse=True
nums2 = [5, 2, 8, 1, 9]
print(sorted(nums2, reverse=True))  # [9, 8, 5, 2, 1]

words2 = ["cat", "dog", "ant", "bee"]
print(sorted(words2, reverse=True))  # ['dog', 'cat', 'bee', 'ant']

# Preserves original
original = [3, 1, 2]
result = sorted(original)
print(original)  # [3, 1, 2] (unchanged)
print(result)  # [1, 2, 3]

# Empty list
print(sorted([]))  # []

# Single element
print(sorted([42]))  # [42]
print(sorted(["hello"]))  # ['hello']

# Already sorted
print(sorted([1, 2, 3, 4, 5]))  # [1, 2, 3, 4, 5]

# Reverse sorted input
print(sorted([5, 4, 3, 2, 1]))  # [1, 2, 3, 4, 5]

# Duplicates
print(sorted([3, 1, 2, 1, 3, 2]))  # [1, 1, 2, 2, 3, 3]
print(sorted(["a", "b", "a", "c", "b"]))  # ['a', 'a', 'b', 'b', 'c']

# Sorting tuples
t1 = (3, 1, 2)
print(sorted(t1))  # [1, 2, 3]

t2 = ("banana", "apple")
print(sorted(t2))  # ['apple', 'banana']

# Generator expression
gen = (x * 2 for x in range(5))
print(sorted(gen, reverse=True))  # [8, 6, 4, 2, 0]

# Long strings
long_strings = ["abc", "ab", "abcd", "a"]
print(sorted(long_strings))  # ['a', 'ab', 'abc', 'abcd']


print("sorted_comprehensive tests done")
