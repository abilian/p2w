"""Test special methods: __str__, __repr__, __len__, __eq__, __getitem__, __setitem__."""

from __future__ import annotations


# Class with __str__ and __repr__
class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def __str__(self):
        return self.name

    def __repr__(self):
        return "Person(" + repr(self.name) + ", " + str(self.age) + ")"


p = Person("Alice", 30)
print(str(p))  # "Alice"
print(repr(p))  # "Person('Alice', 30)"


# Class with __len__
class MyList:
    def __init__(self, items):
        self.items = items

    def __len__(self):
        return len(self.items)


ml = MyList([1, 2, 3, 4, 5])
print(len(ml))  # 5


# Class with __eq__
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y


p1 = Point(1, 2)
p2 = Point(1, 2)
p3 = Point(3, 4)
print(p1 == p2)  # True
print(p1 == p3)  # False


# Class with __getitem__
class MyDict:
    def __init__(self):
        self.data = {}

    def __getitem__(self, key):
        return self.data.get(key, "not found")

    def __setitem__(self, key, value):
        self.data[key] = value


d = MyDict()
d["name"] = "Bob"
d["age"] = 25
print(d["name"])  # "Bob"
print(d["age"])  # 25
print(d["missing"])  # "not found"


# Class with numeric index access
class Vector:
    def __init__(self, values):
        self.values = values

    def __getitem__(self, index):
        return self.values[index]

    def __setitem__(self, index, value):
        self.values[index] = value

    def __len__(self):
        return len(self.values)


v = Vector([10, 20, 30])
print(v[0])  # 10
print(v[1])  # 20
print(len(v))  # 3
v[1] = 200
print(v[1])  # 200


# Combining multiple special methods
class Container:
    def __init__(self):
        self.items = []

    def __len__(self):
        return len(self.items)

    def __getitem__(self, index):
        return self.items[index]

    def __setitem__(self, index, value):
        self.items[index] = value

    def __str__(self):
        return "Container(" + str(self.items) + ")"

    def add(self, item):
        self.items.append(item)


c = Container()
c.add(1)
c.add(2)
c.add(3)
print(len(c))  # 3
print(c[0])  # 1
c[0] = 100
print(c[0])  # 100
print(str(c))  # Container([100, 2, 3])


print("special methods tests done")
