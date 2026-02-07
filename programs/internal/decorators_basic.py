"""Test basic decorator syntax."""

from __future__ import annotations


# Basic decorator with no arguments
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


# Decorator that modifies function with arguments
def log_call(func):
    def wrapper(a, b):
        print("calling")
        result = func(a, b)
        print("done")
        return result

    return wrapper


@log_call
def add(x, y):
    return x + y


print(add(3, 4))


# Multiple decorators (stacked)
def add_exclaim(func):
    def wrapper(s):
        return func(s) + "!"

    return wrapper


def add_greeting(func):
    def wrapper(s):
        return "Hello, " + func(s)

    return wrapper


@add_exclaim
@add_greeting
def get_name(name):
    return name


print(get_name("World"))


# Decorator with closure state (using workaround for subscript augassign)
def counter_decorator(func):
    count = [0]

    def wrapper():
        count[0] = count[0] + 1
        print(count[0])
        return func()

    return wrapper


@counter_decorator
def do_nothing():
    pass


do_nothing()
do_nothing()
do_nothing()


print("decorators done")
