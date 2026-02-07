"""Test numeric builtins: divmod, pow with modulo, round with ndigits."""

from __future__ import annotations


# =============================================================================
# divmod() - quotient and remainder
# =============================================================================

print("divmod basic:")
# divmod(a, b) returns (a // b, a % b)
print(divmod(17, 5))   # (3, 2)
print(divmod(10, 3))   # (3, 1)
print(divmod(20, 4))   # (5, 0)

print("divmod with larger numbers:")
print(divmod(100, 7))  # (14, 2)
print(divmod(1000, 13))  # (76, 12)

print("divmod exact division:")
print(divmod(15, 5))   # (3, 0)
print(divmod(100, 10)) # (10, 0)

print("divmod with negative:")
print(divmod(-17, 5))  # (-4, 3) in Python (floor division)
print(divmod(17, -5))  # (-4, -3)
print(divmod(-17, -5)) # (3, -2)

print("divmod with floats:")
result = divmod(17.5, 3.0)
print(result[0])  # 5.0
print(result[1])  # 2.5

print("divmod small numbers:")
print(divmod(1, 3))    # (0, 1)
print(divmod(2, 10))   # (0, 2)


# =============================================================================
# pow() - power with optional modulo
# =============================================================================

print("pow basic:")
print(pow(2, 3))       # 8
print(pow(3, 2))       # 9
print(pow(5, 0))       # 1
print(pow(10, 1))      # 10

print("pow larger exponents:")
print(pow(2, 10))      # 1024
print(pow(3, 5))       # 243

print("pow with modulo (3-arg):")
# pow(base, exp, mod) = (base ** exp) % mod, but computed efficiently
print(pow(2, 10, 1000))   # 24 (1024 % 1000)
print(pow(3, 5, 100))     # 43 (243 % 100)
print(pow(7, 3, 10))      # 3 (343 % 10)

print("pow modular arithmetic:")
# Useful for cryptography
print(pow(2, 8, 255))     # 1 (256 % 255)
print(pow(5, 3, 7))       # 6 (125 % 7)
print(pow(10, 4, 17))     # 4 (10000 % 17)

print("pow with mod=1:")
# Any number mod 1 is 0
print(pow(100, 50, 1))    # 0
print(pow(999, 999, 1))   # 0

print("pow edge cases:")
print(pow(0, 5))          # 0
print(pow(1, 1000))       # 1
print(pow(2, 0, 5))       # 1 (any^0 mod anything = 1)

print("pow with floats (2-arg):")
print(pow(2.0, 3.0))      # 8.0
print(pow(4.0, 0.5))      # 2.0 (square root)
print(pow(27.0, 1.0/3.0)) # ~3.0 (cube root)


# =============================================================================
# round() with ndigits parameter
# =============================================================================

print("round basic:")
print(round(3.14159))     # 3
print(round(2.71828))     # 3
print(round(1.5))         # 2 (banker's rounding)
print(round(2.5))         # 2 (banker's rounding)

print("round with ndigits=1:")
print(round(3.14159, 1))  # 3.1
print(round(2.71828, 1))  # 2.7
print(round(9.99, 1))     # 10.0

print("round with ndigits=2:")
print(round(3.14159, 2))  # 3.14
print(round(2.71828, 2))  # 2.72
print(round(1.005, 2))    # 1.0 or 1.01 (float precision issues)

print("round with ndigits=3:")
print(round(3.14159, 3))  # 3.142
print(round(2.71828, 3))  # 2.718

print("round with ndigits=0:")
print(round(3.7, 0))      # 4.0
print(round(3.2, 0))      # 3.0

print("round with negative ndigits:")
# Negative ndigits rounds to tens, hundreds, etc.
print(round(1234, -1))    # 1230
print(round(1234, -2))    # 1200
print(round(1234, -3))    # 1000
print(round(5678, -1))    # 5680
print(round(5678, -2))    # 5700

print("round negative numbers:")
print(round(-3.14159, 2)) # -3.14
print(round(-2.5))        # -2 (banker's rounding)
print(round(-1234, -2))   # -1200

print("round integers with ndigits:")
print(round(42, 2))       # 42
print(round(42, -1))      # 40


# =============================================================================
# Combining numeric operations
# =============================================================================

print("combined operations:")

# Use divmod result
q, r = divmod(47, 5)
print(q, r)  # 9 2
print(q * 5 + r)  # 47 (verify)

# pow with modulo in expression
val = pow(2, 100, 1000000007)  # Common in competitive programming
print(val)

# Chain of operations
x = 123.456789
print(round(x, 2))        # 123.46
print(round(x, 0))        # 123.0
print(round(x, -1))       # 120.0


print("builtins_numeric_extra tests done")
