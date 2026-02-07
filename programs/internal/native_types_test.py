"""Test native types (i32, i64, f64)."""

from __future__ import annotations


def test_i32_arithmetic() -> None:
    """Test native i32 arithmetic."""
    a: i32 = 10
    b: i32 = 3

    sum_val: i32 = a + b
    diff: i32 = a - b
    prod: i32 = a * b
    quot: i32 = a // b
    rem: i32 = a % b

    print("i32 sum:", sum_val)
    print("i32 diff:", diff)
    print("i32 prod:", prod)
    print("i32 quot:", quot)
    print("i32 rem:", rem)


def test_f64_arithmetic() -> None:
    """Test native f64 arithmetic."""
    x: f64 = 10.5
    y: f64 = 3.0

    sum_val: f64 = x + y
    diff: f64 = x - y
    prod: f64 = x * y
    quot: f64 = x / y

    print("f64 sum:", sum_val)
    print("f64 diff:", diff)
    print("f64 prod:", prod)
    print("f64 quot:", quot)


def test_i32_loop() -> None:
    """Test i32 in a loop - this should be fast."""
    total: i32 = 0
    i: i32 = 0
    while i < 100:
        total = total + i
        i = i + 1
    print("i32 loop sum:", total)


def test_f64_loop() -> None:
    """Test f64 in a loop."""
    total: f64 = 0.0
    i: i32 = 0
    while i < 10:
        total = total + 1.5
        i = i + 1
    print("f64 loop sum:", total)


# Run tests
test_i32_arithmetic()
test_f64_arithmetic()
test_i32_loop()
test_f64_loop()
