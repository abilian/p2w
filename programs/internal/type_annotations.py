"""Test type annotations and type-informed code generation."""

from __future__ import annotations


# Annotated variables - enable optimized output
def add_ints(a: int, b: int) -> int:
    return a + b


print(add_ints(3, 4))  # 7


def concat_strings(a: str, b: str) -> str:
    return a + b


print(concat_strings("hello", " world"))  # "hello world"


# F-string optimization with typed variables
def greet(name: str) -> str:
    return f"Hello, {name}!"


print(greet("Alice"))  # "Hello, Alice!"


# Type annotations on variables
x: int = 10
y: int = 20
print(x + y)  # 30

s1: str = "foo"
s2: str = "bar"
print(s1 + s2)  # "foobar"


# Function with float annotation
def circle_area(radius: float) -> float:
    return 3.14159 * radius * radius


print(circle_area(2.0))  # ~12.566


# Boolean operations with annotations
def is_valid(value: int) -> bool:
    return value > 0


print(is_valid(5))  # True
print(is_valid(-3))  # False


# String repetition with type info
def repeat_str(s: str, n: int) -> str:
    return s * n


print(repeat_str("ab", 3))  # "ababab"


# Comparison with typed values
def compare_ints(a: int, b: int) -> bool:
    return a == b


print(compare_ints(5, 5))  # True
print(compare_ints(5, 6))  # False


# Mixed expressions with type annotations
def calculate(x: int, y: int, z: int) -> int:
    return x + y * z


print(calculate(1, 2, 3))  # 7


# len() returns int
def get_length(items: list) -> int:
    return len(items)


print(get_length([1, 2, 3, 4, 5]))  # 5


# String methods return strings
def process_text(text: str) -> str:
    result = text.upper()
    return result.strip()


print(process_text("  hello  "))  # "HELLO"


# str() with type annotation
def stringify(value: int) -> str:
    return str(value)


print(stringify(42))  # "42"


# int() with type annotation
def parse_int(s: str) -> int:
    return int(s)


print(parse_int("123"))  # 123


# List annotation
numbers: list = [1, 2, 3]
print(len(numbers))  # 3


# Dict annotation
data: dict = {"a": 1, "b": 2}
print(len(data))  # 2


# Optional-style annotation (using None default)
def greet_optional(name: str = "World") -> str:
    return f"Hello, {name}!"


print(greet_optional())  # "Hello, World!"
print(greet_optional("Bob"))  # "Hello, Bob!"


# Class with annotated methods
class Calculator:
    def add(self, a: int, b: int) -> int:
        return a + b

    def multiply(self, a: float, b: float) -> float:
        return a * b


calc = Calculator()
print(calc.add(3, 4))  # 7
print(calc.multiply(2.5, 3.0))  # 7.5 (use non-whole result to avoid JS integer display)


print("type_annotations tests done")
