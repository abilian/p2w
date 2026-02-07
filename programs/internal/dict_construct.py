"""Test dict() constructor with various arguments."""

from __future__ import annotations

# Empty dict
d1 = dict()
print(len(d1))

# Dict with kwargs only
d2 = dict(a=1, b=2, c=3)
print(d2["a"])
print(d2["b"])
print(d2["c"])
print(len(d2))

# Dict from another dict
d3 = dict({"x": 10, "y": 20})
print(d3["x"])
print(d3["y"])

# Dict from dict with kwargs (merge)
d4 = dict({"x": 1}, y=2, z=3)
print(d4["x"])
print(d4["y"])
print(d4["z"])
print(len(d4))
