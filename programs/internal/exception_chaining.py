"""Test exception chaining: raise X from Y."""

from __future__ import annotations


# Basic exception chaining
# Note: JS doesn't raise on division by zero (returns Infinity), so we use explicit check
def process_value(value):
    try:
        if value == 0:
            raise ValueError("Cannot divide by zero")
        return 100 / value
    except ValueError as e:
        raise RuntimeError("Processing failed") from e


try:
    process_value(0)
except RuntimeError as e:
    print("caught RuntimeError with cause")
    if hasattr(e, "__cause__"):
        print("has cause")


# Chain with new exception type
def load_config(path):
    try:
        # Simulating file not found
        if path == "missing":
            raise KeyError("file not found")
        return {"data": "ok"}
    except KeyError as e:
        raise RuntimeError("Config load failed") from e


try:
    load_config("missing")
except RuntimeError as e:
    print("caught RuntimeError")


# Explicit None cause (suppress context)
def clean_raise():
    try:
        raise ValueError("original")
    except ValueError:
        raise TypeError("new error") from None


try:
    clean_raise()
except TypeError as e:
    print("caught TypeError")
    # __cause__ should be None when using "from None"


# Chaining in nested try blocks
def outer():
    try:
        inner()
    except ValueError as e:
        raise RuntimeError("outer failed") from e


def inner():
    raise ValueError("inner failed")


try:
    outer()
except RuntimeError as e:
    print("caught outer RuntimeError")


# Multiple levels of chaining
def level1():
    raise KeyError("level 1")


def level2():
    try:
        level1()
    except KeyError as e:
        raise ValueError("level 2") from e


def level3():
    try:
        level2()
    except ValueError as e:
        raise RuntimeError("level 3") from e


try:
    level3()
except RuntimeError as e:
    print("caught at level 3")


# Exception chaining with custom exception
class CustomError(Exception):
    pass


def custom_chain():
    try:
        raise ValueError("base error")
    except ValueError as e:
        raise CustomError("custom error") from e


try:
    custom_chain()
except CustomError as e:
    print("caught CustomError")


print("exception chaining tests done")
