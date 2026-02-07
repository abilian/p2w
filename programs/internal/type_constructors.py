"""Test type constructors."""

from __future__ import annotations


# int()
print(int())  # 0
print(int(42))  # 42
print(int(3.7))  # 3
print(int(-3.7))  # -3
print(int("123"))  # 123
print(int("-456"))  # -456
print(int(True))  # 1
print(int(False))  # 0


# float()
f1 = float()
print("float() is 0:", f1 == 0)  # float() is 0: True
f2 = float(42)
print("float(42) is 42:", f2 == 42)  # float(42) is 42: True
print(float("3.14"))  # 3.14
print(float("-2.5"))  # -2.5


# str()
print(str())  # '' (empty)
print(str(42))  # '42'
print(str(3.14))  # '3.14'
print(str(None))  # 'None'


# bool() - test values without printing bool directly
print("bool() is falsy:", not bool())  # bool() is falsy: True
print("bool(0) is falsy:", not bool(0))  # bool(0) is falsy: True
print("bool(1) is truthy:", bool(1) == True)  # bool(1) is truthy: True
print("bool(-1) is truthy:", bool(-1) == True)  # bool(-1) is truthy: True
print("bool('') is falsy:", not bool(""))  # bool('') is falsy: True
print("bool('x') is truthy:", bool("x") == True)  # bool('x') is truthy: True
print("bool([]) is falsy:", not bool([]))  # bool([]) is falsy: True
print("bool([1]) is truthy:", bool([1]) == True)  # bool([1]) is truthy: True
print("bool(None) is falsy:", not bool(None))  # bool(None) is falsy: True


# list()
print(list())  # []
lst = list("abc")
print(len(lst))  # 3
print(lst[0])  # a
print(list((1, 2, 3)))  # [1, 2, 3]
print(list(range(5)))  # [0, 1, 2, 3, 4]


# tuple() - test values without printing tuple repr
t1 = tuple()
print(len(t1))  # 0
t2 = tuple("abc")
print(len(t2))  # 3
print(t2[0])  # a
t3 = tuple([1, 2, 3])
print(len(t3))  # 3
print(t3[0])  # 1


# set()
print(len(set()))  # 0
print(len(set([1, 2, 2, 3])))  # 3


# dict()
print(dict())  # {}
d = dict(a=1, b=2)
print(d["a"])  # 1
print(d["b"])  # 2


# range()
print(list(range(5)))  # [0, 1, 2, 3, 4]
print(list(range(2, 8)))  # [2, 3, 4, 5, 6, 7]
print(list(range(0, 10, 2)))  # [0, 2, 4, 6, 8]


# Type conversion chains
print(int(float("3.9")))  # 3
print(list(tuple([1, 2, 3])))  # [1, 2, 3]
print(str(int("42")))  # '42'


print("type_constructors tests done")
