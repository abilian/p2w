"""Test constant folding optimizations."""

from __future__ import annotations


# Arithmetic constant folding
print(1 + 2)  # Folds to 3
print(10 - 3)  # Folds to 7
print(4 * 5)  # Folds to 20
print(15 // 3)  # Folds to 5
print(17 % 5)  # Folds to 2
print(2**10)  # Folds to 1024

# Chained arithmetic
print(1 + 2 + 3)  # Folds to 6
print(2 * 3 * 4)  # Folds to 24
print(10 - 5 + 3)  # Folds to 8

# Float arithmetic (use non-whole results to avoid JS integer display)
print(1.5 + 2.3)  # Folds to 3.8
print(2.5 * 2.5)  # Folds to 6.25

# String concatenation folding
print("hello" + " " + "world")  # Folds to "hello world"

# String repetition folding
print("ab" * 3)  # Folds to "ababab"
print("-" * 10)  # Folds to "----------"

# Boolean folding
print(True and True)  # Folds to True
print(True and False)  # Folds to False
print(True or False)  # Folds to True
print(False or False)  # Folds to False
print(not True)  # Folds to False
print(not False)  # Folds to True

# Short-circuit evaluation
x = 5
print(True or x)  # True (short-circuits)
print(False and x)  # False (short-circuits)

# Comparison folding
print(1 < 2)  # Folds to True
print(5 > 10)  # Folds to False
print(3 == 3)  # Folds to True
print(4 != 4)  # Folds to False
print(2 <= 2)  # Folds to True
print(3 >= 5)  # Folds to False

# Subscript folding
print("hello"[0])  # Folds to "h"
print("hello"[4])  # Folds to "o"
print([1, 2, 3][1])  # Folds to 2
print((10, 20, 30)[2])  # Folds to 30

# len() folding
print(len("hello"))  # Folds to 5
print(len([1, 2, 3]))  # Folds to 3
print(len((1, 2, 3, 4)))  # Folds to 4
print(len(""))  # Folds to 0

# min/max folding
print(min(1, 2, 3))  # Folds to 1
print(max(1, 2, 3))  # Folds to 3
print(min(5, 2, 8))  # Folds to 2
print(max(5, 2, 8))  # Folds to 8

# abs() folding
print(abs(-5))  # Folds to 5
print(abs(5))  # Folds to 5
print(abs(-3.14))  # Folds to 3.14

# sum() folding
print(sum([1, 2, 3]))  # Folds to 6
print(sum([1, 2, 3, 4, 5]))  # Folds to 15

# bool() folding
print(bool(0))  # Folds to False
print(bool(1))  # Folds to True
print(bool(""))  # Folds to False
print(bool("x"))  # Folds to True

# int() folding
print(int("123"))  # Folds to 123
print(int(3.7))  # Folds to 3

# chr/ord folding
print(chr(65))  # Folds to "A"
print(chr(97))  # Folds to "a"
print(ord("A"))  # Folds to 65
print(ord("z"))  # Folds to 122

# Conditional expression folding
print(5 if True else 10)  # Folds to 5
print(5 if False else 10)  # Folds to 10

# Complex expressions
print(len("hi") + len("bye"))  # Folds to 5
print(min(1, 2) + max(3, 4))  # Folds to 5
print(abs(-3) * 2)  # Folds to 6


print("constant_folding tests done")
