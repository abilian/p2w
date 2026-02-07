"""Test control flow statements."""

from __future__ import annotations


# Basic if/else
x = 10
if x > 5:
    print("greater")
else:
    print("smaller")

# elif chain
y = 50
if y < 25:
    print("low")
elif y < 75:
    print("medium")
else:
    print("high")

# Nested if
a = 3
b = 7
if a > 0:
    if b > 5:
        print("both positive and b large")

# While loop
count = 0
while count < 3:
    print(count)
    count += 1

# For loop with range
for i in range(4):
    print(i)

# For loop with list
items = ["a", "b", "c"]
for item in items:
    print(item)

# Break in loop
for i in range(10):
    if i == 3:
        break
    print(i)
print("after break")

# Continue in loop
for i in range(5):
    if i == 2:
        continue
    print(i)
print("after continue")

# Nested loops
for i in range(2):
    for j in range(2):
        print(i * 10 + j)

# While with break
n = 0
while True:
    n += 1
    if n >= 3:
        break
print(n)

# For-else (no break)
for i in range(3):
    pass
else:
    print("loop completed")

# For-else (with break)
for i in range(5):
    if i == 2:
        break
else:
    print("should not print")
print("done")
