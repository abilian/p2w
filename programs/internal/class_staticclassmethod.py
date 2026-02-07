"""Test @staticmethod and @classmethod decorators."""

from __future__ import annotations


class Calculator:
    value = 100

    @staticmethod
    def add(a, b):
        return a + b

    @staticmethod
    def multiply(a, b):
        return a * b

    @classmethod
    def get_value(cls):
        return cls.value

    @classmethod
    def create_with_value(cls, val):
        cls.value = val
        return cls()

    # Test with 'self' as first param (MicroPython style)
    @classmethod
    def get_value_self(self):
        return self.value


# Test staticmethod from class
print(Calculator.add(1, 2))
print(Calculator.multiply(3, 4))

# Test staticmethod from instance
calc = Calculator()
print(calc.add(5, 6))
print(calc.multiply(7, 8))

# Test classmethod from class
print(Calculator.get_value())

# Test classmethod from instance
print(calc.get_value())

# Test classmethod with 'self' param name
print(calc.get_value_self())


# Test that staticmethod doesn't bind 'this'
class Counter:
    count = 0

    @staticmethod
    def increment():
        Counter.count += 1
        return Counter.count


print(Counter.increment())
print(Counter.increment())
c = Counter()
print(c.increment())


# Test classmethod returning instance
class Factory:
    @classmethod
    def create(cls):
        return cls()

    def describe(self):
        return "Factory instance"


f = Factory.create()
print(f.describe())


print("class_staticclassmethod tests done")
