"""Test generator functions."""

from __future__ import annotations


# Basic generator
def count(n):
    i = 0
    while i < n:
        yield i
        i += 1


# Use list() to convert to array
result = list(count(5))
print(result)

# Use in for loop
total = 0
for x in count(3):
    total += x
print(total)


# Generator with yield from
def gen1():
    yield 1
    yield 2


def gen2():
    yield from gen1()
    yield 3


result2 = list(gen2())
print(result2)


# Generator in sum()
total2 = sum(count(5))
print(total2)


# Generator that filters
def evens(n):
    for i in range(n):
        if i % 2 == 0:
            yield i


result3 = list(evens(10))
print(result3)


# Generator with multiple yields
def multi():
    yield "a"
    yield "b"
    yield "c"


for letter in multi():
    print(letter)


# Nested yield from
def chain(a, b):
    yield from a
    yield from b


chained = list(chain([1, 2], [3, 4]))
print(chained)


# Test any() with list (generator expression over generator not yet supported)
has_even = any([x % 2 == 0 for x in [0, 1, 2, 3, 4]])
if has_even:
    print("has even")
