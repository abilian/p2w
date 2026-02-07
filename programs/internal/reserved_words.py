"""Test JavaScript reserved word auto-renaming.

Python allows variable names like 'default', 'switch', 'case' which are
reserved keywords in JavaScript. Prescrypt now auto-renames these by
appending an underscore.
"""

# Variables with reserved names
default = 42
switch = "hello"
case = [1, 2, 3]
interface = {"a": 1}
export = True
package = "test"

# Use them in expressions
print(default + 10)  # 52
print(switch.upper())  # HELLO
print(len(case))  # 3
print(interface.get("a"))  # 1
print(str(export))  # True
print(package)  # test


# Functions with reserved parameter names
def process(default, export):
    return default + len(export)


result = process(100, [1, 2, 3, 4, 5])
print(result)  # 105


# Nested usage
def outer(switch):
    def inner(case):
        return switch + case

    return inner(10)


print(outer(5))  # 15


# Tuple unpacking with reserved names (use different names to avoid redeclaration)
static, volatile = 1, 2
print(static + volatile)  # 3
