"""Test function arguments and calling patterns."""

from __future__ import annotations


# Default arguments
def greet(name, greeting="Hello"):
    return greeting + ", " + name

print(greet("Alice"))              # Hello, Alice
print(greet("Bob", "Hi"))          # Hi, Bob


# Multiple default arguments
def power(base, exp=2):
    return base ** exp

print(power(3))      # 9
print(power(3, 3))   # 27
print(power(2, 10))  # 1024


# Unpacking in call
def add(a, b, c):
    return a + b + c

nums = [1, 2, 3]
print(add(*nums))  # 6


# Dict unpacking in call
def person(name, age, city):
    return name + " " + str(age) + " " + city

info = {"name": "Dan", "age": 40, "city": "Boston"}
print(person(**info))


# Recursive with default
def factorial(n, acc=1):
    if n <= 1:
        return acc
    return factorial(n - 1, acc * n)

print(factorial(5))   # 120
print(factorial(10))  # 3628800


# Function returning function
def make_multiplier(n):
    def multiplier(x):
        return x * n
    return multiplier

double = make_multiplier(2)
triple = make_multiplier(3)
print(double(5))  # 10
print(triple(5))  # 15


# Higher-order function
def apply_twice(f, x):
    return f(f(x))

def add_one(n):
    return n + 1

print(apply_twice(add_one, 5))  # 7


# Default with mutable - avoid the trap
def append_to(item, target=None):
    if target is None:
        target = []
    target.append(item)
    return target

print(append_to(1))  # [1]
print(append_to(2))  # [2] (not [1, 2])


# Multiple positional with defaults
def create_point(x=0, y=0, z=0):
    return [x, y, z]

print(create_point())           # [0, 0, 0]
print(create_point(1))          # [1, 0, 0]
print(create_point(1, 2))       # [1, 2, 0]
print(create_point(1, 2, 3))    # [1, 2, 3]


# Function with many args
def many_args(a, b, c, d, e):
    return a + b + c + d + e

print(many_args(1, 2, 3, 4, 5))  # 15


# Closure capturing multiple variables
def make_linear(a, b):
    def linear(x):
        return a * x + b
    return linear

f = make_linear(2, 3)  # 2x + 3
print(f(0))   # 3
print(f(1))   # 5
print(f(5))   # 13


# Nested function calls
def outer(x):
    def middle(y):
        def inner(z):
            return x + y + z
        return inner
    return middle

print(outer(1)(2)(3))  # 6


# Recursive Fibonacci
def fib(n):
    if n <= 1:
        return n
    return fib(n - 1) + fib(n - 2)

print(fib(0))   # 0
print(fib(1))   # 1
print(fib(10))  # 55


# Mutually recursive
def is_even(n):
    if n == 0:
        return True
    return is_odd(n - 1)

def is_odd(n):
    if n == 0:
        return False
    return is_even(n - 1)

print(is_even(4))  # True
print(is_even(5))  # False
print(is_odd(4))   # False
print(is_odd(5))   # True


print("function_args tests done")
