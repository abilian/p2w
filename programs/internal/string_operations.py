"""Test string operations and edge cases."""

from __future__ import annotations


# Empty string operations
empty = ""
print(len(empty))      # 0
print(empty == "")     # True
print(not empty)       # True (empty string is falsy)
print(bool(empty))     # False

# Single character
c = "x"
print(len(c))          # 1
print(c * 5)           # xxxxx
print(c + c + c)       # xxx

# String concatenation
a = "hello"
b = "world"
print(a + " " + b)     # hello world

# String multiplication
print("-" * 10)        # ----------
print("ab" * 3)        # ababab

# String equality/inequality
print("abc" == "abc")  # True
print("abc" != "xyz")  # True
print("abc" == "ABC")  # False (case sensitive)

# String indexing
s = "python"
print(s[0])            # p
print(s[5])            # n
print(s[-1])           # n
print(s[-2])           # o
print(s[-6])           # p

# String slicing
print(s[0:3])          # pyt
print(s[3:6])          # hon
print(s[:3])           # pyt
print(s[3:])           # hon
print(s[:])            # python
print(s[::2])          # pto
print(s[::-1])         # nohtyp
print(s[1:5:2])        # yh

# Negative slicing
print(s[-3:])          # hon
print(s[:-3])          # pyt
print(s[-4:-1])        # tho

# Membership test
print("th" in "python")   # True
print("x" in "python")    # False
print("" in "python")     # True (empty string is in any string)
print("python" in "python")  # True

# Case operations
mixed = "HeLLo WoRLD"
print(mixed.upper())   # HELLO WORLD
print(mixed.lower())   # hello world
print(mixed.swapcase())  # hEllO wOrld

# Escape sequences
print("line1\nline2")  # line1 (newline) line2
print("col1\tcol2")    # col1 (tab) col2
print("quote: \"hi\"") # quote: "hi"
print("backslash: \\") # backslash: \

# Raw-ish strings (escaped)
path = "C:\\Users\\Name"
print(path)            # C:\Users\Name

# String repetition with zero
print("hello" * 0)     # (empty string)
print("" * 100)        # (empty string)

# String truthiness
print(bool("hello"))   # True
print(bool(""))        # False
print(bool(" "))       # True (whitespace is truthy)

# ord() and chr()
print(ord("A"))        # 65
print(ord("a"))        # 97
print(ord("0"))        # 48
print(chr(65))         # A
print(chr(97))         # a
print(chr(48))         # 0

# String in list operations
words = ["apple", "banana", "cherry"]
print(", ".join(words))  # apple, banana, cherry

# Split edge cases
text = "a,b,c"
print(text.split(","))   # ['a', 'b', 'c']
empty_split = "".split(",")
print(len(empty_split))  # 1
print(empty_split[0])    # '' (empty string)

# Find
s = "hello"
print(s.find("e"))      # 1
print(s.find("z"))      # -1

# Count
print("aaa".count("a"))   # 3
print("aaa".count("aa"))  # 1 (non-overlapping)

# Replace
print("hello".replace("l", "L"))  # heLLo
print("aaa".replace("a", "b"))    # bbb


print("string_operations tests done")
