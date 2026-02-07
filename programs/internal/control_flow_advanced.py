"""Test advanced control flow patterns."""

from __future__ import annotations


# Break from nested loop (inner only)
found = False
for i in range(3):
    for j in range(3):
        if j == 1:
            found = True
            break
        print(i, j)
print("found:", found)


# Continue with multiple conditions
for i in range(10):
    if i % 2 == 0:
        continue
    if i > 7:
        continue
    print(i)  # 1, 3, 5, 7


# While with complex condition
x = 0
y = 0
while x < 3 and y < 3:
    print(x, y)
    x = x + 1
    if x == 3:
        x = 0
        y = y + 1


# Deeply nested if
a = 1
b = 2
c = 3
if a > 0:
    if b > 0:
        if c > 0:
            print("all positive")
        else:
            print("c not positive")
    else:
        print("b not positive")
else:
    print("a not positive")


# Loop with accumulator
total = 0
for i in range(1, 6):
    total = total + i
print(total)  # 15


# Early return from function
def find_first_even(nums):
    for n in nums:
        if n % 2 == 0:
            return n
    return -1

print(find_first_even([1, 3, 4, 5]))  # 4
print(find_first_even([1, 3, 5]))     # -1


# Multiple breaks with flag
def find_pair(target):
    for i in range(10):
        for j in range(10):
            if i + j == target:
                return (i, j)
    return None

result = find_pair(5)
print(result)  # (0, 5)


# Chained elif with fallthrough logic
def classify(n):
    if n < 0:
        return "negative"
    elif n == 0:
        return "zero"
    elif n < 10:
        return "small"
    elif n < 100:
        return "medium"
    else:
        return "large"

print(classify(-5))   # negative
print(classify(0))    # zero
print(classify(5))    # small
print(classify(50))   # medium
print(classify(500))  # large


# Loop with early exit condition
def sum_until_limit(nums, limit):
    total = 0
    for n in nums:
        if total + n > limit:
            break
        total = total + n
    return total

print(sum_until_limit([1, 2, 3, 4, 5], 6))  # 6 (1+2+3)


# Loop with index tracking
items = ["a", "b", "c", "d", "e"]
idx = 0
for item in items:
    if item == "c":
        print("found at", idx)
        break
    idx = idx + 1


# Conditional in loop body
results = []
for i in range(10):
    if i % 3 == 0:
        results.append("fizz")
    elif i % 2 == 0:
        results.append("buzz")
    else:
        results.append(str(i))
print(results)


print("control_flow_advanced tests done")
