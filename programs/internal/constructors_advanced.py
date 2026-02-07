"""Test advanced constructor usage."""

from __future__ import annotations


# int() with base
print(int("ff", 16))  # 255
print(int("1010", 2))  # 10
print(int("777", 8))  # 511
print(int("42", 10))  # 42


# int() with no args
print(int())  # 0


# float() with no args (JS displays 0 not 0.0 - known limitation)
print(float() == 0)  # True


# float() with string
print(float("3.14"))  # 3.14


# bool() with no args
print(bool())  # False


# str() with no args
print(repr(str()))  # ''


# dict() with keyword arguments
d = dict(a=1, b=2, c=3)
print(d["a"])  # 1
print(d["b"])  # 2


# dict() with no args
d2 = dict()
print(len(d2))  # 0


# list() with no args
lst = list()
print(len(lst))  # 0


# list() with iterable
lst2 = list([1, 2, 3])
print(lst2)  # [1, 2, 3]


# set() with no args
s = set()
print(len(s))  # 0


# set() with iterable
s2 = set([1, 2, 2, 3])
print(len(s2))  # 3


# tuple() with iterable
t = tuple([1, 2, 3])
print(len(t))  # 3


# bytes() with no args
b = bytes()
print(len(b))  # 0


# bytes() with integer (creates zero-filled bytes)
b2 = bytes(5)
print(len(b2))  # 5


print("constructors_advanced tests done")
