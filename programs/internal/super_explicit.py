"""Test super() with explicit arguments: super(Class, self)."""

from __future__ import annotations


class Base:
    def __init__(self, value):
        self.value = value

    def get_value(self):
        return self.value

    def describe(self):
        return "Base"


class Child(Base):
    def __init__(self, value, extra):
        # Use explicit super(Class, self) form
        super(Child, self).__init__(value)
        self.extra = extra

    def get_value(self):
        # Call parent method explicitly
        base_value = super(Child, self).get_value()
        return base_value + self.extra

    def describe(self):
        parent_desc = super(Child, self).describe()
        return parent_desc + " -> Child"


class GrandChild(Child):
    def __init__(self, value, extra, bonus):
        super(GrandChild, self).__init__(value, extra)
        self.bonus = bonus

    def get_value(self):
        child_value = super(GrandChild, self).get_value()
        return child_value + self.bonus

    def describe(self):
        parent_desc = super(GrandChild, self).describe()
        return parent_desc + " -> GrandChild"


# Test the classes
b = Base(10)
print(b.get_value())  # 10
print(b.describe())  # Base

c = Child(10, 5)
print(c.get_value())  # 15
print(c.describe())  # Base -> Child

gc = GrandChild(10, 5, 2)
print(gc.get_value())  # 17
print(gc.describe())  # Base -> Child -> GrandChild


print("super_explicit tests done")
