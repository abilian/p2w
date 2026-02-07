"""Test list.sort() with key and reverse arguments."""

from __future__ import annotations


# Basic sort with reverse
nums = [3, 1, 4, 1, 5, 9, 2, 6]
nums.sort(reverse=True)
print(nums)  # [9, 6, 5, 4, 3, 2, 1, 1]


# Sort with key function
words = ["banana", "apple", "cherry", "date"]
words.sort(key=len)
print(words)  # ['date', 'apple', 'banana', 'cherry']


# Sort with key and reverse
items = ["a", "bbb", "cc"]
items.sort(key=len, reverse=True)
print(items)  # ['bbb', 'cc', 'a']


# Sort with lambda key
pairs = [[1, "one"], [3, "three"], [2, "two"]]
pairs.sort(key=lambda x: x[0])
print(pairs[0][1])  # one
print(pairs[1][1])  # two
print(pairs[2][1])  # three


# sorted() with key
unsorted = [5, 2, 8, 1]
result = sorted(unsorted, key=lambda x: -x)
print(result)  # [8, 5, 2, 1]


# sorted() with reverse
result2 = sorted([3, 1, 2], reverse=True)
print(result2)  # [3, 2, 1]


# sorted() with both key and reverse
result3 = sorted(["a", "bbb", "cc"], key=len, reverse=True)
print(result3)  # ['bbb', 'cc', 'a']


print("sort_advanced tests done")
