"""Test isinstance() with user-defined classes."""

from __future__ import annotations


class Animal:
    def speak(self):
        return "..."


class Dog(Animal):
    def speak(self):
        return "Woof"


class Cat(Animal):
    def speak(self):
        return "Meow"


class Robot:
    def speak(self):
        return "Beep"


# Create instances
dog = Dog()
cat = Cat()
robot = Robot()


# isinstance with user-defined classes
print(isinstance(dog, Dog))  # True
print(isinstance(dog, Animal))  # True
print(isinstance(dog, Cat))  # False
print(isinstance(dog, Robot))  # False

print(isinstance(cat, Cat))  # True
print(isinstance(cat, Animal))  # True
print(isinstance(cat, Dog))  # False

print(isinstance(robot, Robot))  # True
print(isinstance(robot, Animal))  # False


# isinstance with built-in types (already covered, but for completeness)
print(isinstance(42, int))  # True
print(isinstance("hello", str))  # True
print(isinstance([1, 2], list))  # True


print("isinstance_classes tests done")
