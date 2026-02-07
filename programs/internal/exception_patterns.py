"""Test exception handling patterns and edge cases."""

from __future__ import annotations


# Basic raise and catch
try:
    raise ValueError("basic error")
except ValueError as e:
    print("caught ValueError")

# Finally always runs - normal case
result = []
try:
    result.append("try")
except:
    result.append("except")
finally:
    result.append("finally")
print(result)  # ['try', 'finally']


# Finally always runs - exception case
result2 = []
try:
    result2.append("try")
    raise ValueError("error")
except ValueError:
    result2.append("except")
finally:
    result2.append("finally")
print(result2)  # ['try', 'except', 'finally']


# Nested exception handling
def inner():
    raise TypeError("inner error")

def outer():
    try:
        inner()
    except TypeError:
        raise ValueError("converted")

try:
    outer()
except ValueError:
    print("caught converted error")


# Exception propagates through multiple levels
def level3():
    raise RuntimeError("from level 3")

def level2():
    level3()

def level1():
    level2()

try:
    level1()
except RuntimeError:
    print("caught at top level")


# Catching different error types
errors = []
for i in range(3):
    try:
        if i == 0:
            raise ValueError("value")
        elif i == 1:
            raise TypeError("type")
        else:
            raise RuntimeError("runtime")
    except ValueError:
        errors.append("V")
    except TypeError:
        errors.append("T")
    except RuntimeError:
        errors.append("R")
print(errors)  # ['V', 'T', 'R']


# Try-except in a loop
caught = 0
for i in range(5):
    try:
        if i % 2 == 0:
            raise ValueError("even")
    except ValueError:
        caught = caught + 1
print(caught)  # 3 (i=0, 2, 4)


# Exception in function with recovery
def maybe_fail(x):
    if x == 2:
        raise ValueError("bad value")
    return x * 2

safe_results = []
for x in range(5):
    try:
        safe_results.append(maybe_fail(x))
    except ValueError:
        safe_results.append(-1)
print(safe_results)  # [0, 2, -1, 6, 8]


# Return from try block
def return_from_try():
    try:
        return "from try"
    except:
        return "from except"
    finally:
        pass  # finally runs but doesn't override return

print(return_from_try())  # from try


# Return from except block
def return_from_except():
    try:
        raise ValueError()
    except ValueError:
        return "from except"
    finally:
        pass

print(return_from_except())  # from except


# Else clause (runs if no exception)
try:
    x = 10
except:
    print("error")
else:
    print("no error")  # prints


# Else not run on exception
try:
    raise ValueError()
except ValueError:
    print("caught")
else:
    print("else runs")  # doesn't print


# Deeply nested try blocks
try:
    try:
        try:
            raise RuntimeError("deep")
        except ValueError:
            print("wrong 1")
    except TypeError:
        print("wrong 2")
except RuntimeError:
    print("caught deep")


# Multiple exceptions in same function
def multi_except(x):
    try:
        if x < 0:
            raise ValueError("negative")
        if x > 10:
            raise TypeError("too big")
        return x * 2
    except ValueError:
        return -1
    except TypeError:
        return -2

print(multi_except(-5))   # -1
print(multi_except(5))    # 10
print(multi_except(15))   # -2


print("exception_patterns tests done")
