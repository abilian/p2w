"""Test special method dispatch for classes."""

from __future__ import annotations


# Test comparison operators
class MyNumber:
    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        print("eq")
        return self.value == other.value

    def __lt__(self, other):
        print("lt")
        return self.value < other.value

    def __gt__(self, other):
        print("gt")
        return self.value > other.value

    def __le__(self, other):
        print("le")
        return self.value <= other.value

    def __ge__(self, other):
        print("ge")
        return self.value >= other.value


n1 = MyNumber(5)
n2 = MyNumber(10)
n3 = MyNumber(5)

print(n1 == n2)
print(n1 == n3)
print(n1 < n2)
print(n1 > n2)
print(n1 <= n3)
print(n1 >= n3)


# Test container special methods
class Container:
    def __init__(self):
        self._data = {}

    def __getitem__(self, key):
        print(f"getitem {key}")
        return self._data.get(key, None)

    def __setitem__(self, key, value):
        print(f"setitem {key}={value}")
        self._data[key] = value

    def __delitem__(self, key):
        print(f"delitem {key}")
        if key in self._data:
            del self._data[key]


c = Container()
c["a"] = 1
c["b"] = 2
print(c["a"])
print(c["b"])
del c["a"]
print(c["a"])


print("special_methods tests done")
