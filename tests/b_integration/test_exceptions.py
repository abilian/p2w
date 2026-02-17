"""Integration tests for exception handling."""

from __future__ import annotations

import pytest

from p2w.testing import compare_outputs


class TestBasicExceptions:
    """Test basic try/except functionality."""

    def test_simple_try_except(self):
        source = """
try:
    x = 1
except:
    x = 2
print(x)
"""
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"

    def test_exception_raised(self):
        source = """
try:
    raise ValueError("test")
except ValueError:
    print("caught")
"""
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"

    def test_exception_with_message(self):
        source = """
try:
    raise ValueError("error message")
except ValueError as e:
    print("caught")
"""
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"


class TestExceptionTypes:
    """Test catching specific exception types."""

    def test_catch_value_error(self):
        source = """
try:
    raise ValueError()
except ValueError:
    print("ValueError")
except TypeError:
    print("TypeError")
"""
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"

    def test_catch_type_error(self):
        source = """
try:
    raise TypeError()
except ValueError:
    print("ValueError")
except TypeError:
    print("TypeError")
"""
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"

    @pytest.mark.skip(reason="Exception hierarchy not yet implemented in p2w")
    def test_catch_exception_base(self):
        source = """
try:
    raise ValueError()
except Exception:
    print("caught")
"""
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"


class TestTryFinally:
    """Test try/finally blocks."""

    def test_finally_runs_no_exception(self):
        source = """
try:
    print("try")
finally:
    print("finally")
"""
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"

    def test_finally_runs_with_exception(self):
        source = """
try:
    try:
        raise ValueError()
    finally:
        print("finally")
except ValueError:
    print("caught")
"""
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"

    @pytest.mark.skip(reason="return inside try/finally not yet implemented")
    def test_finally_with_return(self):
        source = """
def foo():
    try:
        return 1
    finally:
        print("finally")
    return 2

result = foo()
print(result)
"""
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"


class TestTryExceptFinally:
    """Test combined try/except/finally."""

    def test_full_try_block(self):
        source = """
try:
    print("try")
except:
    print("except")
finally:
    print("finally")
"""
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"

    def test_exception_caught_with_finally(self):
        source = """
try:
    raise ValueError()
except ValueError:
    print("caught")
finally:
    print("finally")
"""
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"


class TestTryElse:
    """Test try/except/else blocks."""

    def test_else_no_exception(self):
        source = """
try:
    x = 1
except:
    print("except")
else:
    print("else")
"""
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"

    def test_else_not_run_on_exception(self):
        source = """
try:
    raise ValueError()
except ValueError:
    print("except")
else:
    print("else")
"""
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"


class TestNestedExceptions:
    """Test nested exception handling."""

    def test_nested_try_blocks(self):
        source = """
try:
    try:
        raise ValueError()
    except ValueError:
        print("inner")
        raise TypeError()
except TypeError:
    print("outer")
"""
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"

    def test_exception_in_except_handler(self):
        source = """
try:
    try:
        raise ValueError()
    except ValueError:
        raise TypeError()
except TypeError:
    print("caught TypeError")
"""
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"


class TestReraiseException:
    """Test re-raising exceptions."""

    @pytest.mark.skip(reason="Bare raise not yet implemented")
    def test_bare_raise(self):
        source = """
try:
    try:
        raise ValueError()
    except ValueError:
        print("caught inner")
        raise
except ValueError:
    print("caught outer")
"""
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"


class TestExceptionInLoop:
    """Test exceptions within loops."""

    def test_exception_breaks_loop(self):
        source = """
try:
    for i in range(5):
        print(i)
        if i == 2:
            raise ValueError()
except ValueError:
    print("caught")
"""
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"

    def test_exception_in_loop_body(self):
        source = """
results = []
for i in range(5):
    try:
        if i == 2:
            raise ValueError()
        results.append(i)
    except ValueError:
        results.append(-1)
print(results)
"""
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"


class TestExceptionInFunction:
    """Test exceptions in function contexts."""

    def test_exception_from_function(self):
        source = """
def fail():
    raise ValueError()

try:
    fail()
except ValueError:
    print("caught")
"""
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"

    def test_exception_propagates(self):
        source = """
def inner():
    raise ValueError()

def outer():
    inner()

try:
    outer()
except ValueError:
    print("caught")
"""
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"


class TestBuiltinExceptions:
    """Test built-in exceptions."""

    @pytest.mark.skip(reason="IndexError on out-of-bounds not yet implemented")
    def test_index_error(self):
        source = """
try:
    lst = [1, 2, 3]
    x = lst[10]
except IndexError:
    print("caught IndexError")
"""
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"

    @pytest.mark.skip(reason="KeyError on missing key not yet implemented")
    def test_key_error(self):
        source = """
try:
    d = {"a": 1}
    x = d["missing"]
except KeyError:
    print("caught KeyError")
"""
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"

    @pytest.mark.skip(reason="ZeroDivisionError not yet implemented")
    def test_zero_division_error(self):
        source = """
try:
    x = 1 // 0
except ZeroDivisionError:
    print("caught ZeroDivisionError")
"""
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"
