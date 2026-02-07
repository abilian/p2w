"""Test lambda functions."""

from __future__ import annotations


# Basic lambda
add = lambda x, y: x + y
print(add(3, 4))

# Lambda with no args
get_five = lambda: 5
print(get_five())

# Lambda with single arg
double = lambda x: x * 2
print(double(7))

# Lambda in map-like usage
numbers = [1, 2, 3, 4, 5]
squared = list(map(lambda x: x * x, numbers))
print(squared)

# Lambda in filter-like usage
evens = list(filter(lambda x: x % 2 == 0, numbers))
print(evens)

# Lambda with conditional expression
sign = lambda x: "positive" if x > 0 else "non-positive"
print(sign(5))
print(sign(-3))

# Lambda returning lambda (currying)
make_adder = lambda n: lambda x: x + n
add_ten = make_adder(10)
print(add_ten(5))

# Lambda in list
ops = [lambda x: x + 1, lambda x: x * 2, lambda x: x**2]
print(ops[0](5))
print(ops[1](5))
print(ops[2](5))

# Immediately invoked lambda
result = (lambda x, y: x * y)(6, 7)
print(result)

# Lambda capturing closure variable
multiplier = 3
times_three = lambda x: x * multiplier
print(times_three(4))

# Lambda with multiple values via list (not tuple to avoid repr difference)
multi = lambda x: [x, x * 2, x * 3]
print(multi(5))

# Nested lambdas
compose = lambda f, g: lambda x: f(g(x))
inc = lambda x: x + 1
dbl = lambda x: x * 2
inc_then_dbl = compose(dbl, inc)
print(inc_then_dbl(5))  # (5 + 1) * 2 = 12

# Lambda with string operations
upper = lambda s: s.upper()
print(upper("hello"))
