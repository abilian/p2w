"""Test context managers (with statements).

Note: Prescrypt uses a simplified 'with' implementation that calls .close()
in a finally block. This test uses proper Python context managers that also
have a close() method to work in both environments.
"""

from __future__ import annotations


class SimpleContext:
    """Context manager with both __enter__/__exit__ (for Python) and close() (for Prescrypt)."""

    def __init__(self, name):
        self.name = name

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        print(f"closing {self.name}")


# Basic with statement
with SimpleContext("resource1") as ctx:
    print(f"using {ctx.name}")


# With statement without as
with SimpleContext("resource2"):
    print("inside with block")


# Nested with statements
with SimpleContext("outer") as o:
    print(f"in outer: {o.name}")
    with SimpleContext("inner") as i:
        print(f"in inner: {i.name}")


# Context manager with return value
class ValueContext:
    def __init__(self, value):
        self.value = value

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        pass


with ValueContext(42) as v:
    print(v.value)


# Multiple operations in with block
with SimpleContext("multi") as m:
    print("step 1")
    print("step 2")
    print("step 3")


print("all contexts closed")
