"""Test string methods."""

from __future__ import annotations


# Case conversion
s = "Hello World"
print(s.upper())  # HELLO WORLD
print(s.lower())  # hello world
print(s.capitalize())  # Hello world
print(s.title())  # Hello World


# Stripping whitespace
padded = "  hello  "
print(padded.strip())  # hello
print(padded.lstrip())  # 'hello  '
print(padded.rstrip())  # '  hello'

# Strip specific characters
print("xxxhelloxxx".strip("x"))  # hello


# Splitting
text = "one,two,three,four"
parts = text.split(",")
print(len(parts))  # 4
print(parts[0])  # one

parts2 = text.split(",", 2)
print(len(parts2))  # 3
print(parts2[2])  # three,four


# Joining
parts = ["a", "b", "c"]
print("-".join(parts))  # a-b-c
print("".join(parts))  # abc


# Finding and searching
haystack = "hello world hello"
print(haystack.find("world"))  # 6
print(haystack.find("xyz"))  # -1
print(haystack.find("l"))  # 2
print(haystack.rfind("l"))  # 15

print(haystack.count("l"))  # 4
print(haystack.count("hello"))  # 2


# Starts/ends with
filename = "document.txt"
print(filename.startswith("doc"))  # True
print(filename.startswith("txt"))  # False
print(filename.endswith(".txt"))  # True
print(filename.endswith(".pdf"))  # False


# Replacement
original = "hello world"
print(original.replace("world", "python"))  # hello python
print(original.replace("l", "L"))  # heLLo worLd
print(original.replace("l", "L", 1))  # heLlo world


# Character classification
print("hello".isalpha())  # True
print("hello123".isalpha())  # False
print("123".isdigit())  # True
print("12.3".isdigit())  # False
print("hello123".isalnum())  # True
print("   ".isspace())  # True
print("hello".islower())  # True
print("HELLO".isupper())  # True


# Alignment
word = "hi"
print(word.center(10))  # '    hi    '
print(word.ljust(10))  # 'hi        '
print(word.rjust(10))  # '        hi'
print("42".zfill(5))  # 00042


# Format
print("Hello, {}!".format("World"))  # Hello, World!
print("{0} and {1}".format("A", "B"))  # A and B
print("{:.2f}".format(3.14159))  # 3.14


# Operations
print("abc" * 3)  # abcabcabc
print("abc"[1])  # b
print("hello"[1:4])  # ell
print(len("hello"))  # 5
print("l" in "hello")  # True
print("x" in "hello")  # False


print("string_methods tests done")
