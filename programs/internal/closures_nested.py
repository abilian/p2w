"""Test closures and nested functions."""

from __future__ import annotations


# Basic closure - captures outer variable
def make_adder(x):
    def adder(y):
        return x + y
    return adder


add5 = make_adder(5)
add10 = make_adder(10)
print(add5(3))   # 8
print(add10(3))  # 13
print(add5(7))   # 12


# Multiple nested levels
def outer(x):
    def middle(y):
        def inner(z):
            return x + y + z
        return inner
    return middle


f = outer(1)(2)
print(f(3))  # 6
print(f(10))  # 13


# Closure captures multiple variables
def make_linear(a, b):
    def f(x):
        return a * x + b
    return f


f1 = make_linear(2, 3)  # 2x + 3
f2 = make_linear(1, -1)  # x - 1
print(f1(5))  # 13
print(f2(5))  # 4


# Lambda closures
def make_multiplier(n):
    return lambda x: x * n


double = make_multiplier(2)
triple = make_multiplier(3)
print(double(7))  # 14
print(triple(7))  # 21


# Closure with conditional
def make_filter(threshold):
    def f(x):
        if x > threshold:
            return True
        return False
    return f


above5 = make_filter(5)
above10 = make_filter(10)
print(above5(7))   # True
print(above5(3))   # False
print(above10(7))  # False
print(above10(15)) # True


# Closure with string operations
def make_greeter(greeting):
    def greet(name):
        return greeting + ", " + name + "!"
    return greet


hello = make_greeter("Hello")
hi = make_greeter("Hi")
print(hello("Alice"))  # Hello, Alice!
print(hi("Bob"))       # Hi, Bob!


# Closure that returns another closure
def compose(f, g):
    def composed(x):
        return f(g(x))
    return composed


def add1(x):
    return x + 1


def mul2(x):
    return x * 2


h = compose(add1, mul2)  # add1(mul2(x)) = 2x + 1
print(h(5))  # 11


print("closures_nested tests done")
