"""Test introspection builtins: ascii, getattr, setattr, delattr, id."""

from __future__ import annotations


# =============================================================================
# ascii() - Return ASCII representation with escapes for non-ASCII
# Note: Current implementation delegates to repr()
# =============================================================================

print("ascii basic strings:")
print(ascii("hello"))        # 'hello'
print(ascii("world"))        # 'world'
print(ascii(""))             # ''

print("ascii numbers and bool:")
print(ascii(42))             # 42
print(ascii(3.14))           # 3.14
print(ascii(True))           # True

print("ascii lists and dicts:")
print(ascii([1, 2, 3]))      # [1, 2, 3]
print(ascii({"a": 1}))       # {'a': 1}


# =============================================================================
# getattr() - Get attribute by name
# =============================================================================

class Point:
    class_var = "shared"

    def __init__(self, x, y):
        self.x = x
        self.y = y

print("getattr on instance:")
p = Point(10, 20)
print(getattr(p, "x"))           # 10
print(getattr(p, "y"))           # 20
print(getattr(p, "class_var"))   # shared

print("getattr with default:")
print(getattr(p, "z", 0))        # 0
print(getattr(p, "missing", "default"))  # default
print(getattr(p, "x", 999))      # 10 (exists, so no default)


# =============================================================================
# setattr() - Set attribute by name
# =============================================================================

print("setattr on instance:")
p2 = Point(1, 2)
print(p2.x)                      # 1
setattr(p2, "x", 100)
print(p2.x)                      # 100

print("setattr new attribute:")
setattr(p2, "z", 300)
print(p2.z)                      # 300
print(getattr(p2, "z"))          # 300


# =============================================================================
# delattr() - Delete attribute by name
# =============================================================================

print("delattr on instance:")
p3 = Point(5, 6)
setattr(p3, "temp", 999)
print(hasattr(p3, "temp"))       # True
print(getattr(p3, "temp"))       # 999
delattr(p3, "temp")
print(hasattr(p3, "temp"))       # False
print(getattr(p3, "temp", "gone"))  # gone


# =============================================================================
# id() - Return unique identifier for object
# Note: Current implementation returns incrementing integers
# =============================================================================

print("id basic:")
# Verify id returns positive integers
x = 42
y = "hello"
z = [1, 2]
print(id(x) > 0)       # True
print(id(y) > 0)       # True
print(id(z) > 0)       # True

print("id for singletons:")
# True and False have fixed ids
print(id(True) > 0)    # True
print(id(False) >= 0)  # True
print(id(None) >= 0)   # True


# =============================================================================
# Combined usage
# =============================================================================

print("combined getattr/setattr:")
class Config:
    def __init__(self):
        self.debug = False
        self.verbose = False

cfg = Config()
for attr in ["debug", "verbose"]:
    print(getattr(cfg, attr))    # False, False

setattr(cfg, "debug", True)
print(getattr(cfg, "debug"))     # True


print("builtins_introspection tests done")
