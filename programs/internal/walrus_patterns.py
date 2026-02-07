"""Test walrus operator (:=) patterns and use cases."""

from __future__ import annotations


# Basic walrus in print
x = 0
print((x := 42))  # 42
print(x)          # 42

# Walrus in if condition
y = 0
if (y := 10) > 5:
    print("y is greater than 5:", y)  # y is greater than 5: 10

# Walrus in while condition
z = 0
counter = 0
while (z := z + 1) <= 3:
    counter = counter + z
print("counter:", counter)  # counter: 6

# Walrus in list comprehension condition
n = 0
items = [1, 2, 3, 4, 5, 6, 7, 8]
result = [(n := x) for x in items if x % 2 == 0]
print(result)  # [2, 4, 6, 8]
print("last n:", n)  # last n: 8

# Walrus with function call result
def compute(val):
    return val * val

v = 0
if (v := compute(5)) > 20:
    print("computed value:", v)  # computed value: 25

# Walrus in expression
a = 0
total = (a := 5) + (a := a + 3) + a
print("total:", total)  # total: 16 (5 + 8 + 8)
print("a:", a)  # a: 8

# Walrus with comparison chain
b = 0
c = 0
if 0 < (b := 7) < 10:
    c = b * 2
print("c:", c)  # c: 14

# Walrus in nested expression
d = 0
e = 0
d = ((e := 3) + 1) * 2
print("d:", d)  # d: 8
print("e:", e)  # e: 3

# Walrus with boolean and
f = 0
if True and (f := 99):
    print("f assigned:", f)  # f assigned: 99

# Walrus in ternary
g = 0
result = (g := 5) if True else 0
print("result:", result)  # result: 5
print("g:", g)  # g: 5

# Walrus for caching computation
h = 0
def expensive(val):
    return val * 100

data = [1, 2, 3, 4]
results = [(h := expensive(x)) for x in data if h > 150]
# Note: walrus captures expensive(x) for each x
print("last h:", h)  # last h: 400

# Walrus in multiple conditions
i = 0
j = 0
if (i := 3) > 0 and (j := 4) > 0:
    print("both positive:", i, j)  # both positive: 3 4

# Walrus chained assignment
k = 0
l = 0
l = (k := 7) + 3
print("k:", k, "l:", l)  # k: 7 l: 10


print("walrus_patterns tests done")
