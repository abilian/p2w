"""Test global and nonlocal declarations."""

from __future__ import annotations


# Basic global
counter = 0


def increment():
    global counter
    counter += 1


increment()
increment()
print(counter)  # 2


# Global in nested function
total = 0


def outer():
    def inner():
        global total
        total += 10

    inner()
    inner()


outer()
print(total)  # 20


# Multiple globals
x = 1
y = 2


def modify_both():
    global x, y
    x = 10
    y = 20


modify_both()
print(x, y)  # 10 20


# Nonlocal basic
def make_counter():
    count = 0

    def inc():
        nonlocal count
        count += 1
        return count

    return inc


counter_fn = make_counter()
print(counter_fn())  # 1
print(counter_fn())  # 2
print(counter_fn())  # 3


# Nonlocal with multiple levels
def level1():
    value = "L1"

    def level2():
        def level3():
            nonlocal value
            value = "L3"

        level3()
        return value

    return level2()


print(level1())  # L3


# Nonlocal vs local shadowing
def test_shadowing():
    x = "outer"

    def inner():
        nonlocal x
        x = "modified"

    inner()
    return x


print(test_shadowing())  # modified


# Multiple nonlocals
def multi_nonlocal():
    a = 1
    b = 2

    def modify():
        nonlocal a, b
        a = 10
        b = 20

    modify()
    return a + b


print(multi_nonlocal())  # 30


# Closure without nonlocal (read-only)
def closure_readonly():
    data = [1, 2, 3]

    def get_sum():
        return sum(data)

    return get_sum


print(closure_readonly()())  # 6


# Global assignment creates new local without declaration
value = "global"


def shadow_test():
    value = "local"
    return value


print(shadow_test())  # local
print(value)  # global (unchanged)


print("global_nonlocal tests done")
