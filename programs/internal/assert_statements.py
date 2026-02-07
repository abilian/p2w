"""Test assert statements."""

from __future__ import annotations


# Basic assert (passes)
assert True
print("assert True passed")

assert 1
print("assert 1 passed")

assert "hello"
print("assert 'hello' passed")

assert [1, 2, 3]
print("assert [1, 2, 3] passed")


# Assert with expression
x = 10
assert x > 5
print("assert x > 5 passed")

assert x == 10
print("assert x == 10 passed")


# Assert with message (failing) - just check it raises
try:
    assert False, "This should fail"
except AssertionError:
    print("caught AssertionError with message")


# Assert with message (passing)
assert True, "This message is not shown"
print("assert with unused message passed")


# Assert with complex expression
data = [1, 2, 3, 4, 5]
assert len(data) == 5
print("assert len(data) == 5 passed")

assert sum(data) == 15
print("assert sum(data) == 15 passed")


# Assert with function call
def is_positive(n):
    return n > 0


assert is_positive(42)
print("assert is_positive(42) passed")


# Assert failure without message
try:
    assert 0
except AssertionError:
    print("caught AssertionError (no message)")


# Assert with computed message - just check it raises
value = -5
try:
    assert value > 0, f"Expected positive, got {value}"
except AssertionError:
    print("caught AssertionError with computed message")


# Assert in function - just check it raises on invalid input
def validate(x):
    assert x is not None, "x cannot be None"
    return x * 2


print(validate(5))  # 10

try:
    validate(None)
except AssertionError:
    print("validate(None) raised AssertionError")


# Assert with comparison chain
a, b, c = 1, 2, 3
assert a < b < c
print("assert a < b < c passed")


# Assert with boolean operators
assert True and True
print("assert True and True passed")

assert True or False
print("assert True or False passed")

assert not False
print("assert not False passed")


# Assert with membership
items = [1, 2, 3]
assert 2 in items
print("assert 2 in items passed")

assert 5 not in items
print("assert 5 not in items passed")


# Assert with identity
obj = object()
ref = obj
assert ref is obj
print("assert ref is obj passed")

assert ref is not None
print("assert ref is not None passed")


print("assert_statements tests done")
