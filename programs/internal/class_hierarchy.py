"""Test complex class hierarchies and inheritance patterns."""

from __future__ import annotations


# Three-level inheritance chain
class Animal:
    def __init__(self, name):
        self.name = name

    def speak(self):
        return "..."


class Mammal(Animal):
    def __init__(self, name, warm_blooded):
        super().__init__(name)
        self.warm_blooded = warm_blooded

    def speak(self):
        return "mammal sound"


class Dog(Mammal):
    def __init__(self, name, breed):
        super().__init__(name, True)
        self.breed = breed

    def speak(self):
        return "woof"


# Test the chain
d = Dog("Buddy", "Labrador")
print(d.name)        # Buddy
print(d.warm_blooded) # True
print(d.breed)       # Labrador
print(d.speak())     # woof

# isinstance checks up the chain
print(isinstance(d, Dog))     # True
print(isinstance(d, Mammal))  # True
print(isinstance(d, Animal))  # True

# Create Mammal directly
m = Mammal("Cat", True)
print(m.name)        # Cat
print(m.speak())     # mammal sound
print(isinstance(m, Dog))     # False
print(isinstance(m, Mammal))  # True


# Sibling classes
class Bird(Animal):
    def __init__(self, name, can_fly):
        super().__init__(name)
        self.can_fly = can_fly

    def speak(self):
        return "chirp"


b = Bird("Sparrow", True)
print(b.name)        # Sparrow
print(b.can_fly)     # True
print(b.speak())     # chirp

# Cross-check
print(isinstance(b, Bird))    # True
print(isinstance(b, Animal))  # True
print(isinstance(b, Mammal))  # False
print(isinstance(b, Dog))     # False


# Method overriding with super calls
class Counter:
    def __init__(self):
        self.count = 0

    def increment(self):
        self.count = self.count + 1
        return self.count


class DoubleCounter(Counter):
    def increment(self):
        super().increment()
        super().increment()
        return self.count


dc = DoubleCounter()
print(dc.increment())  # 2
print(dc.increment())  # 4
print(dc.count)        # 4


# Abstract-like base class (no direct instantiation needed)
class Shape:
    def area(self):
        return 0

    def describe(self):
        return "I am a shape with area " + str(self.area())


class Rectangle(Shape):
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def area(self):
        return self.width * self.height


class Square(Rectangle):
    def __init__(self, side):
        super().__init__(side, side)
        self.side = side


r = Rectangle(3, 4)
print(r.area())      # 12
print(r.describe())  # I am a shape with area 12

s = Square(5)
print(s.area())      # 25
print(s.side)        # 5
print(s.width)       # 5
print(isinstance(s, Square))     # True
print(isinstance(s, Rectangle))  # True
print(isinstance(s, Shape))      # True


# Class attributes vs instance attributes
class Config:
    default_value = 100

    def __init__(self, value):
        self.value = value


class CustomConfig(Config):
    default_value = 200


c1 = Config(10)
c2 = CustomConfig(20)
print(c1.value)           # 10
print(c2.value)           # 20
print(Config.default_value)       # 100
print(CustomConfig.default_value) # 200


print("class_hierarchy tests done")
