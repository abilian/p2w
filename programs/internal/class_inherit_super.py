"""Test basic class inheritance with super()."""

from __future__ import annotations


class Base:
    def __init__(self):
        self.value = 10

    def get_value(self):
        return self.value


class Child(Base):
    def __init__(self):
        super().__init__()
        self.extra = 5

    def get_value(self):
        return super().get_value() + self.extra


# Test basic inheritance
b = Base()
print(b.get_value())

# Test child with super() calls
c = Child()
print(c.value)
print(c.extra)
print(c.get_value())

print("class_inherit_super done")
