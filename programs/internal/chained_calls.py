"""Test chained calls and callable expressions."""

from __future__ import annotations


# Chained function calls (closures)
def make_adder(x):
    def add(y):
        return x + y

    return add


add5 = make_adder(5)
print(add5(3))
print(add5(10))

# Direct chained call
print(make_adder(10)(7))


# Triple chain
def make_multiplier(x):
    def mult(y):
        def inner(z):
            return x * y * z

        return inner

    return mult


print(make_multiplier(2)(3)(4))

# List function call
ops = [lambda x: x + 1, lambda x: x * 2]
print(ops[0](10))
print(ops[1](10))
