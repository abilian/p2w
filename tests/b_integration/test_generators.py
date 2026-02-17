"""Integration tests for generator corner cases."""

from __future__ import annotations

import pytest

from p2w.testing import compare_outputs


class TestBasicGenerators:
    """Test basic generator functionality."""

    def test_simple_yield(self):
        source = """
def gen():
    yield 1
    yield 2
    yield 3

for x in gen():
    print(x)
"""
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"

    def test_yield_with_value(self):
        source = """
def countdown(n):
    while n > 0:
        yield n
        n = n - 1

for x in countdown(5):
    print(x)
"""
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"

    def test_yield_none(self):
        source = """
def gen():
    yield
    yield None

for x in gen():
    print(x)
"""
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"


class TestYieldExpressions:
    """Test yield as expressions (not just statements)."""

    @pytest.mark.skip(reason="Yield expression with computation not yet working")
    def test_yield_in_expression(self):
        source = """
def gen():
    x = 1
    y = 2
    yield x + y

for v in gen():
    print(v)
"""
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"

    def test_yield_list(self):
        source = """
def gen():
    yield [1, 2, 3]

for v in gen():
    print(v)
"""
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"


class TestMultipleYields:
    """Test generators with multiple yield points."""

    def test_multiple_yields(self):
        source = """
def gen():
    print("before first")
    yield 1
    print("after first")
    yield 2
    print("after second")
    yield 3
    print("done")

list(gen())
"""
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"

    def test_yield_in_loop(self):
        source = """
def squares(n):
    i = 0
    while i < n:
        yield i * i
        i = i + 1

result = list(squares(5))
print(result)
"""
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"


class TestYieldInConditionals:
    """Test yield inside conditional statements."""

    def test_yield_in_if(self):
        source = """
def gen(x):
    if x > 0:
        yield "positive"
    else:
        yield "non-positive"

print(list(gen(5)))
print(list(gen(-5)))
"""
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"

    def test_yield_in_both_branches(self):
        source = """
def gen(n):
    for i in range(n):
        if i % 2 == 0:
            yield i
        else:
            yield i * 10

print(list(gen(5)))
"""
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"


@pytest.mark.skip(reason="Generator state preservation not fully working")
class TestGeneratorState:
    """Test generator state preservation across yields."""

    def test_local_vars_preserved(self):
        source = """
def gen():
    a = 1
    b = 2
    yield a
    yield b
    yield a + b

print(list(gen()))
"""
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"

    def test_loop_counter_preserved(self):
        source = """
def gen():
    i = 0
    while i < 3:
        yield i
        i = i + 1
        yield i * 10

print(list(gen()))
"""
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"


class TestGeneratorWithParameters:
    """Test generators with parameters."""

    def test_generator_with_param(self):
        source = """
def range_gen(start, stop):
    i = start
    while i < stop:
        yield i
        i = i + 1

print(list(range_gen(2, 7)))
"""
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"

    def test_generator_captures_param(self):
        source = """
def multiplier(factor):
    i = 0
    while i < 5:
        yield i * factor
        i = i + 1

print(list(multiplier(3)))
"""
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"


class TestGeneratorExhaustion:
    """Test generator exhaustion behavior."""

    def test_generator_stops(self):
        source = """
def gen():
    yield 1
    yield 2

g = gen()
print(next(g))
print(next(g))
# Third call would raise StopIteration
exhausted = True
print(exhausted)
"""
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"

    @pytest.mark.skip(reason="Empty generator with early return not working")
    def test_empty_generator(self):
        source = """
def empty():
    return
    yield  # Never reached

print(list(empty()))
"""
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"


class TestGeneratorExpressions:
    """Test generator expressions."""

    def test_simple_genexp(self):
        source = """
g = (x * 2 for x in range(5))
print(list(g))
"""
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"

    def test_genexp_with_filter(self):
        source = """
g = (x for x in range(10) if x % 2 == 0)
print(list(g))
"""
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"

    def test_genexp_as_argument(self):
        source = """
result = sum(x * x for x in range(5))
print(result)
"""
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"


class TestNestedGenerators:
    """Test nested generator usage."""

    def test_nested_for_loops_with_generators(self):
        source = """
def gen1():
    yield 1
    yield 2

def gen2():
    yield 10
    yield 20

for a in gen1():
    for b in gen2():
        print(a + b)
"""
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"

    def test_generator_calling_generator(self):
        source = """
def inner():
    yield 1
    yield 2

def outer():
    for x in inner():
        yield x * 10

print(list(outer()))
"""
        py_out, p2w_out, match = compare_outputs(source)
        assert match, f"Expected {py_out!r}, got {p2w_out!r}"
