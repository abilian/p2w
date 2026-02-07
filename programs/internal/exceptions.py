"""Test exception handling."""

from __future__ import annotations


# Raise and catch exception
def check_positive(n):
    if n < 0:
        raise ValueError("must be positive")
    return n


try:
    check_positive(-5)
except ValueError:
    print("caught raised error")

# Try/except/finally
try:
    a = 5
except:
    print("error")
finally:
    print("finally runs")

# Exception variable
try:
    raise RuntimeError("test message")
except RuntimeError as e:
    print("got error")

# Nested try
try:
    try:
        raise ValueError("inner")
    except TypeError:
        print("wrong type")
except ValueError:
    print("caught in outer")


# Exception in function
def might_fail(x):
    if x == 0:
        raise ZeroDivisionError("cannot be zero")
    return 10


try:
    result = might_fail(0)
except ZeroDivisionError:
    print("handled zero")


# Multiple except clauses
def risky(x):
    if x == 1:
        raise ValueError("value")
    elif x == 2:
        raise TypeError("type")
    return x


for i in [1, 2]:
    try:
        risky(i)
    except ValueError:
        print("value error")
    except TypeError:
        print("type error")

print("done")
