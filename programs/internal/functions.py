from __future__ import annotations


def f():
    return 1


def g(x):
    return x + 1


def h(x):
    def inner(y):
        return x + y

    return inner(1)


print(f())
print(g(1))
print(h(1))
