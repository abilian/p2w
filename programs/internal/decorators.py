"""Test decorator syntax.

Now with @decorator syntax support!
"""

from __future__ import annotations


# Basic decorator
def simple_decorator(func):
    def wrapper():
        print("before")
        func()
        print("after")

    return wrapper


@simple_decorator
def say_hello():
    print("hello")


say_hello()


# Decorator with arguments passthrough
def passthrough(func):
    def wrapper(*args):
        return func(*args)

    return wrapper


@passthrough
def add(a, b):
    return a + b


print(add(3, 4))


# Decorator that modifies return value
def double_result(func):
    def wrapper(*args):
        result = func(*args)
        return result * 2

    return wrapper


@double_result
def get_value(x):
    return x + 10


print(get_value(5))


# Multiple decorators (stacked)
def add_exclaim(func):
    def wrapper(*args):
        return func(*args) + "!"

    return wrapper


def add_greeting(func):
    def wrapper(*args):
        return "Hello, " + func(*args)

    return wrapper


@add_exclaim
@add_greeting
def get_name(name):
    return name


print(get_name("World"))


# Closure with state
def make_counter():
    count = [0]

    def counter():
        count[0] = count[0] + 1
        return count[0]

    return counter


c = make_counter()
print(c())
print(c())
print(c())


# Simple class
class Counter:
    def __init__(self):
        self.value = 0

    def increment(self):
        self.value += 1
        return self.value


obj = Counter()
print(obj.increment())
print(obj.increment())


# Function with *args (now working!)
def sum_all(*args):
    total = 0
    for x in args:
        total += x
    return total


print(sum_all(1, 2, 3))
print(sum_all(1, 2, 3, 4, 5))
