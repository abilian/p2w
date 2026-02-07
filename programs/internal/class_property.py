"""Test @property decorator."""

from __future__ import annotations


# Basic property with getter only
class Point:
    def __init__(self, x, y):
        self._x = x
        self._y = y

    @property
    def x(self):
        print("get x")
        return self._x

    @property
    def y(self):
        print("get y")
        return self._y


p = Point(1, 2)
print(p.x)
print(p.y)


# Property with getter and setter
class Temperature:
    def __init__(self, celsius):
        self._celsius = celsius

    @property
    def celsius(self):
        print("get celsius")
        return self._celsius

    @celsius.setter
    def celsius(self, value):
        print("set celsius")
        self._celsius = value

    @property
    def fahrenheit(self):
        return self._celsius * 9 // 5 + 32  # Use integer division


t = Temperature(0)
print(t.celsius)
t.celsius = 100
print(t.celsius)
print(t.fahrenheit)


# Property with getter, setter, and deleter
class Container:
    def __init__(self, value):
        self._value = value

    @property
    def value(self):
        print("get value")
        return self._value

    @value.setter
    def value(self, val):
        print("set value")
        self._value = val

    @value.deleter
    def value(self):
        print("del value")
        self._value = None


c = Container(42)
print(c.value)
c.value = 100
print(c.value)
del c.value
print(c.value)


# Read-only property (no setter) - should raise AttributeError
class ReadOnly:
    def __init__(self):
        self._data = "secret"

    @property
    def data(self):
        return self._data


ro = ReadOnly()
print(ro.data)
try:
    ro.data = "hacked"
except AttributeError:
    print("AttributeError: can't set")


print("class_property tests done")
