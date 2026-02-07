"""Test match statements (structural pattern matching)."""

from __future__ import annotations


# Basic literal matching
def describe_number(n):
    match n:
        case 0:
            return "zero"
        case 1:
            return "one"
        case 2:
            return "two"
        case _:
            return "many"


print(describe_number(0))
print(describe_number(1))
print(describe_number(2))
print(describe_number(99))


# Match with multiple patterns (OR)
def is_weekend(day):
    match day:
        case "Saturday" | "Sunday":
            return True
        case _:
            return False


print(is_weekend("Saturday"))
print(is_weekend("Monday"))


# Match with capture
def process(value):
    match value:
        case 0:
            return "zero"
        case n:
            return f"got {n}"


print(process(0))
print(process(42))


# Match with guard
def classify(n):
    match n:
        case x if x < 0:
            return "negative"
        case x if x == 0:
            return "zero"
        case x if x > 0:
            return "positive"


print(classify(-5))
print(classify(0))
print(classify(10))


# Match on type/structure (list patterns)
def handle_list(lst):
    match lst:
        case []:
            return "empty"
        case [x]:
            return f"single: {x}"
        case [x, y]:
            return f"pair: {x}, {y}"
        case [x, y, *rest]:
            return f"first two: {x}, {y}, rest: {rest}"


print(handle_list([]))
print(handle_list([1]))
print(handle_list([1, 2]))
print(handle_list([1, 2, 3, 4, 5]))


# Match with nested patterns
def analyze_point(point):
    match point:
        case (0, 0):
            return "origin"
        case (0, y):
            return f"on y-axis at {y}"
        case (x, 0):
            return f"on x-axis at {x}"
        case (x, y):
            return f"point at ({x}, {y})"


print(analyze_point((0, 0)))
print(analyze_point((0, 5)))
print(analyze_point((3, 0)))
print(analyze_point((3, 4)))


# Match with dict patterns
def handle_command(cmd):
    match cmd:
        case {"action": "quit"}:
            return "quitting"
        case {"action": "move", "x": x, "y": y}:
            return f"moving to ({x}, {y})"
        case {"action": action}:
            return f"unknown action: {action}"
        case _:
            return "invalid command"


print(handle_command({"action": "quit"}))
print(handle_command({"action": "move", "x": 10, "y": 20}))
print(handle_command({"action": "jump"}))
print(handle_command("invalid"))


# String matching
def parse_color(color):
    match color:
        case "red":
            return (255, 0, 0)
        case "green":
            return (0, 255, 0)
        case "blue":
            return (0, 0, 255)
        case _:
            return (0, 0, 0)


print(parse_color("red"))
print(parse_color("green"))
print(parse_color("unknown"))


print("match tests done")
