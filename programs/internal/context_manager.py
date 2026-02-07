"""Test context manager protocol: __enter__ and __exit__."""

from __future__ import annotations


# Simple context manager class
class SimpleContext:
    def __init__(self, name):
        self.name = name
        self.entered = False
        self.exited = False

    def __enter__(self):
        self.entered = True
        print(f"Entering {self.name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.exited = True
        print(f"Exiting {self.name}")
        return False  # Don't suppress exceptions


# Test basic context manager
ctx = SimpleContext("test1")
with ctx as c:
    print(f"Inside with block, c.name = {c.name}")
    print(f"c.entered = {str(c.entered)}")

print(f"After with, ctx.exited = {str(ctx.exited)}")


# Context manager that returns different value from __enter__
class ResourceManager:
    def __init__(self):
        self.resource = None

    def __enter__(self):
        self.resource = "acquired resource"
        return self.resource

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.resource = None
        print("Resource released")
        return False


mgr = ResourceManager()
with mgr as resource:
    print(f"Got resource: {resource}")
print(f"After with, mgr.resource = {str(mgr.resource)}")


# Context manager without 'as' binding
class Counter:
    count = 0

    def __enter__(self):
        Counter.count += 1
        print(f"Counter enter: {Counter.count}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print(f"Counter exit: {Counter.count}")
        return False


# Use without 'as'
with Counter():
    print("Inside counter block")

print(f"Final count: {Counter.count}")


# Nested context managers (using separate with statements)
with SimpleContext("outer") as outer:
    print(f"In outer: {outer.name}")
    with SimpleContext("inner") as inner:
        print(f"In inner: {inner.name}")
    print("After inner")
print("After outer")


print("context_manager tests done")
