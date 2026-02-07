"""Test comparison operators with different types.

This tests that comparisons work correctly regardless of how the operands
are obtained (direct values, .length access, function returns, etc.).

The fix: Removed stringly-typed `.endswith(".length")` check in ops.py.
Now comparisons use the type inference system instead of string pattern matching.
"""


def bool_str(b):
    if b:
        return "yes"
    return "no"


# --- Primitive comparisons (should use === optimization) ---

# Integer comparisons
print("=== Integer comparisons ===")
x: int = 42
y: int = 42
z: int = 10
print(bool_str(x == y))  # yes
print(bool_str(x == z))  # no
print(bool_str(x != z))  # yes

# String comparisons
print("=== String comparisons ===")
s1: str = "hello"
s2: str = "hello"
s3: str = "world"
print(bool_str(s1 == s2))  # yes
print(bool_str(s1 == s3))  # no
print(bool_str(s1 != s3))  # yes

# Boolean comparisons
print("=== Boolean comparisons ===")
t: bool = True
f: bool = False
print(bool_str(t == True))  # yes
print(bool_str(f == False))  # yes
print(bool_str(t != f))  # yes


# --- Length comparisons (the specific case that was fixed) ---

print("=== Length comparisons ===")
arr = [1, 2, 3, 4, 5]
print(bool_str(len(arr) == 5))  # yes
print(bool_str(len(arr) == 3))  # no
print(bool_str(len(arr) != 3))  # yes
print(bool_str(len(arr) > 3))  # yes
print(bool_str(len(arr) < 10))  # yes

# String length
text = "hello"
print(bool_str(len(text) == 5))  # yes
print(bool_str(len(text) >= 5))  # yes


# --- Object comparisons (should use op_equals helper) ---

print("=== List comparisons ===")
list1 = [1, 2, 3]
list2 = [1, 2, 3]
list3 = [1, 2, 4]
print(bool_str(list1 == list2))  # yes (deep equality)
print(bool_str(list1 == list3))  # no
print(bool_str(list1 != list3))  # yes

print("=== Dict comparisons ===")
dict1 = {"a": 1, "b": 2}
dict2 = {"a": 1, "b": 2}
dict3 = {"a": 1, "b": 3}
print(bool_str(dict1 == dict2))  # yes (deep equality)
print(bool_str(dict1 == dict3))  # no
print(bool_str(dict1 != dict3))  # yes


# --- Mixed/edge cases ---

print("=== Edge cases ===")

# Comparison with None
val = None
print(bool_str(val == None))  # yes
print(bool_str(val is None))  # yes

# Zero comparisons
print(bool_str(0 == 0))  # yes
print(bool_str(0 == False))  # yes (0 and False are equal in Python)

# Empty collections
empty_list = []
print(bool_str(len(empty_list) == 0))  # yes
print(bool_str(empty_list == []))  # yes


# --- Chained length comparisons ---

print("=== Chained length comparisons ===")
data = [1, 2, 3, 4, 5, 6, 7]
print(bool_str(3 < len(data) < 10))  # yes
print(bool_str(0 <= len(data) <= 7))  # yes
print(bool_str(10 < len(data) < 20))  # no
