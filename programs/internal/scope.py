"""Test scope: global and nonlocal."""

from __future__ import annotations


# Global variable
counter = 0


def increment():
    global counter
    counter += 1


increment()
increment()
increment()
print(counter)


# Global read without declaration
message = "hello"


def print_message():
    print(message)


print_message()


# Global vs local
value = 100


def local_value():
    value = 200  # Local variable
    print(value)


local_value()
print(value)  # Global unchanged


# Multiple globals
x = 1
y = 2


def modify_both():
    global x, y
    x = 10
    y = 20


modify_both()
print(x)
print(y)


# Nonlocal in nested function
def outer():
    count = 0

    def inner():
        nonlocal count
        count += 1
        return count

    print(inner())
    print(inner())
    print(inner())


outer()


# Nonlocal vs local
def outer2():
    x = "outer"

    def inner_local():
        x = "inner"  # Local to inner_local
        return x

    def inner_nonlocal():
        nonlocal x
        x = "modified"
        return x

    print(inner_local())
    print(x)  # Still "outer"
    print(inner_nonlocal())
    print(x)  # Now "modified"


outer2()


# Closure without nonlocal (read-only)
def make_counter(start):
    def get_start():
        return start  # Read outer variable

    return get_start


counter_fn = make_counter(10)
print(counter_fn())


# Multiple levels of nesting
def level1():
    a = 1

    def level2():
        nonlocal a
        a = 2

        def level3():
            nonlocal a
            a = 3

        level3()
        return a

    result = level2()
    print(result)
    print(a)


level1()


# Global in nested function
total = 0


def accumulate(n):
    def add():
        global total
        total += n

    add()


accumulate(5)
accumulate(10)
accumulate(15)
print(total)


# Shadowing without global/nonlocal
name = "global"


def shadow():
    name = "local"
    print(name)


shadow()
print(name)


print("scope tests done")
