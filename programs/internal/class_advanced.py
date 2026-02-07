"""Test advanced class features: @staticmethod, @classmethod, @property, super()."""

from __future__ import annotations


# @staticmethod - no self/cls parameter
class MathUtils:
    @staticmethod
    def add(a, b):
        return a + b

    @staticmethod
    def multiply(a, b):
        return a * b


# Call static methods on class
print(MathUtils.add(3, 4))  # 7
print(MathUtils.multiply(3, 4))  # 12

# Can also call on instance
utils = MathUtils()
print(utils.add(5, 6))  # 11


# @classmethod - receives class as first argument
class Greeter:
    prefix = "Hello"

    @classmethod
    def greet(cls, name):
        return cls.prefix + ", " + name + "!"

    @classmethod
    def set_prefix(cls, new_prefix):
        cls.prefix = new_prefix


print(Greeter.greet("World"))  # "Hello, World!"
Greeter.set_prefix("Hi")
print(Greeter.greet("Alice"))  # "Hi, Alice!"


# @property - getter and setter
class Circle:
    def __init__(self, radius):
        self._radius = radius

    @property
    def radius(self):
        return self._radius

    @radius.setter
    def radius(self, value):
        if value < 0:
            self._radius = 0
        else:
            self._radius = value

    @property
    def diameter(self):
        return self._radius * 2


circle = Circle(5)
print(circle.radius)  # 5
print(circle.diameter)  # 10
circle.radius = 10
print(circle.radius)  # 10
print(circle.diameter)  # 20
circle.radius = -5  # Should clamp to 0
print(circle.radius)  # 0


# super() - single inheritance
class Animal:
    def __init__(self, name):
        self.name = name

    def speak(self):
        return "..."


class Dog(Animal):
    def __init__(self, name, breed):
        super().__init__(name)
        self.breed = breed

    def speak(self):
        return "Woof!"


dog = Dog("Rex", "German Shepherd")
print(dog.name)  # "Rex"
print(dog.breed)  # "German Shepherd"
print(dog.speak())  # "Woof!"


# super() with method override
class Base:
    def greet(self):
        return "Hello"


class Derived(Base):
    def greet(self):
        return super().greet() + " World"


d = Derived()
print(d.greet())  # "Hello World"


# Multi-level inheritance with super()
class A:
    def __init__(self):
        self.a = "A"

    def value(self):
        return self.a


class B(A):
    def __init__(self):
        super().__init__()
        self.b = "B"

    def value(self):
        return super().value() + self.b


class C(B):
    def __init__(self):
        super().__init__()
        self.c = "C"

    def value(self):
        return super().value() + self.c


obj = C()
print(obj.a)  # "A"
print(obj.b)  # "B"
print(obj.c)  # "C"
print(obj.value())  # "ABC"


# Combined example
class Rectangle:
    def __init__(self, width, height):
        self._width = width
        self._height = height

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @property
    def area(self):
        return self._width * self._height

    @staticmethod
    def is_valid(width, height):
        return width > 0 and height > 0

    @classmethod
    def square(cls, size):
        return cls(size, size)


rect = Rectangle(4, 5)
print(rect.area)  # 20
print(Rectangle.is_valid(4, 5))  # True
print(Rectangle.is_valid(-1, 5))  # False

sq = Rectangle.square(3)
print(sq.area)  # 9


print("advanced class tests done")
