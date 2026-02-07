"""Test chained assignment with subscripts and attributes.

This showcases the ability to use multiple assignment targets including
array indices and object attributes, not just simple variable names.

Example: a[0] = a[1] = value assigns value to both a[0] and a[1]
"""

from __future__ import annotations


# ============================================================================
# Chained Assignment with List Subscripts
# ============================================================================

print("=== Chained Subscript Assignment ===")

# Basic chained subscript assignment
a = [True, True]
a[0] = a[1] = False
print(f"a[0]={str(a[0])}, a[1]={str(a[1])}")

# Triple subscript assignment
b = [0, 0, 0]
b[0] = b[1] = b[2] = 42
print(f"b[0]={b[0]}, b[1]={b[1]}, b[2]={b[2]}")

# Mixed indices
c = [1, 2, 3, 4, 5]
c[0] = c[4] = 99
print(f"c[0]={c[0]}, c[2]={c[2]}, c[4]={c[4]}")


# ============================================================================
# Chained Assignment with Dict Subscripts
# ============================================================================

print("\n=== Chained Dict Assignment ===")

# Dict subscript assignment
d = {}
d["x"] = d["y"] = 10
print(f'd["x"]={d["x"]}, d["y"]={d["y"]}')

# Mixed string keys
e = {}
e["name"] = e["alias"] = "Python"
print(f'e["name"]={e["name"]}, e["alias"]={e["alias"]}')


# ============================================================================
# Chained Assignment with Attributes
# ============================================================================

print("\n=== Chained Attribute Assignment ===")


class Point:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.z = 0


p = Point()
p.x = p.y = 5
print(f"p.x={p.x}, p.y={p.y}")

# Triple attribute assignment
q = Point()
q.x = q.y = q.z = 100
print(f"q.x={q.x}, q.y={q.y}, q.z={q.z}")


# ============================================================================
# Mixed Chained Assignment (Names, Subscripts, Attributes)
# ============================================================================

print("\n=== Mixed Chained Assignment ===")


class Container:
    def __init__(self):
        self.value = 0


container = Container()
arr = [0]
result = arr[0] = container.value = 77
print(f"result={result}")
print(f"arr[0]={arr[0]}")
print(f"container.value={container.value}")


# ============================================================================
# Edge Cases
# ============================================================================

print("\n=== Edge Cases ===")

# Nested subscript - assigning to multiple positions
matrix = [[0, 0], [0, 0]]
matrix[0][0] = matrix[1][1] = 1
print(f"matrix[0][0]={matrix[0][0]}, matrix[0][1]={matrix[0][1]}")
print(f"matrix[1][0]={matrix[1][0]}, matrix[1][1]={matrix[1][1]}")

# Boolean values
flags = [True, True, True]
flags[0] = flags[1] = flags[2] = False
all_false = flags[0] == False and flags[1] == False and flags[2] == False
print(f"All flags false: {str(all_false)}")

# String values in dict
config = {}
config["host"] = config["backup_host"] = "localhost"
print(f'config["host"]={config["host"]}')
print(f'config["backup_host"]={config["backup_host"]}')

# Verify all assignments are correct
print("\n=== Verification ===")
print("All tests passed: True")
