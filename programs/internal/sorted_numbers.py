"""Test sorted() with numbers and various types."""

from __future__ import annotations


# sorted() with integers
nums = [3, 1, 4, 1, 5, 9, 2, 6]
print(sorted(nums))  # [1, 1, 2, 3, 4, 5, 6, 9]

# sorted() with floats
floats = [3.14, 2.71, 1.41, 1.73]
print(sorted(floats))  # [1.41, 1.73, 2.71, 3.14]

# sorted() with negative numbers
negatives = [-5, 3, -1, 7, -3, 0]
print(sorted(negatives))  # [-5, -3, -1, 0, 3, 7]

# sorted() with mixed int and float
mixed = [1, 2.5, 3, 0.5, 2]
print(sorted(mixed))  # [0.5, 1, 2, 2.5, 3]

# sorted() with large numbers
large = [1000000, 100, 10000, 10, 100000, 1]
print(sorted(large))  # [1, 10, 100, 1000, 10000, 100000, 1000000]

# sorted() reverse=True
nums2 = [5, 2, 8, 1, 9]
print(sorted(nums2, reverse=True))  # [9, 8, 5, 2, 1]

# sorted() preserves input
original = [3, 1, 2]
result = sorted(original)
print(original)  # [3, 1, 2] (unchanged)
print(result)  # [1, 2, 3]

# sorted() with generator
gen = (x * 2 for x in range(5))
print(sorted(gen, reverse=True))  # [8, 6, 4, 2, 0]

# sorted() empty list
print(sorted([]))  # []

# sorted() single element
print(sorted([42]))  # [42]

# sorted() already sorted
print(sorted([1, 2, 3, 4, 5]))  # [1, 2, 3, 4, 5]

# sorted() reverse sorted input
print(sorted([5, 4, 3, 2, 1]))  # [1, 2, 3, 4, 5]

# min() and max() with integers
nums3 = [7, 2, 9, 4, 5]
print(min(nums3))  # 2
print(max(nums3))  # 9

# min/max with negative integers
nums4 = [-3, 5, -7, 2]
print(min(nums4))  # -7
print(max(nums4))  # 5

# Note: min/max with floats requires float comparison support
# which is not yet implemented


print("sorted_numbers tests done")
