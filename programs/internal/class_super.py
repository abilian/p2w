"""Test super() functionality."""

from __future__ import annotations


# Basic super() call
class Base:
    def __init__(self):
        self.a = 1

    def meth(self):
        print("Base.meth", self.a)
        return self.a


class Sub(Base):
    def meth(self):
        print("Sub.meth")
        return super().meth()


s = Sub()
print(s.meth())


# super() attribute access
class A:
    x = 42


class B(A):
    def get_x(self):
        return super().x


print(B().get_x())


# Method chaining with super()
class C:
    def foo(self):
        return [1, 2, 3]


class D(C):
    def bar(self):
        return super().foo()[1]


print(D().bar())


# super() string representation (starts with "<super:")
# Note: Use a class with explicit parent to test super() repr
class E0:
    pass


class E(E0):
    def p(self):
        # Just check it starts with "<super:" - implementation details may vary
        print(str(super())[:7])


E().p()


# super().__init__() when inheriting from object
class F:
    def __init__(self):
        super().__init__()
        print("F.__init__")


F()


# Set/delete on super raises AttributeError
class G:
    pass


class H(G):
    def test(self):
        try:
            super().x = 1
        except AttributeError:
            print("AttributeError on set")
        try:
            del super().x
        except AttributeError:
            print("AttributeError on del")


H().test()


print("class_super tests done")
