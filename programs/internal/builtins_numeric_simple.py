"""Test numeric builtins: divmod, pow with modulo, round with ndigits (simplified)."""

from __future__ import annotations


# =============================================================================
# divmod() - quotient and remainder
# =============================================================================

print("divmod basic:")
print(divmod(17, 5))   # (3, 2)
print(divmod(10, 3))   # (3, 1)
print(divmod(20, 4))   # (5, 0)

print("divmod larger numbers:")
print(divmod(100, 7))  # (14, 2)
print(divmod(1000, 13))  # (76, 12)

print("divmod exact division:")
print(divmod(15, 5))   # (3, 0)
print(divmod(100, 10)) # (10, 0)

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
print(pow(2, 10, 1000))   # 24 (1024 % 1000)
print(pow(3, 5, 100))     # 43 (243 % 100)
print(pow(7, 3, 10))      # 3 (343 % 10)

print("pow modular arithmetic:")
print(pow(2, 8, 255))     # 1 (256 % 255)
print(pow(5, 3, 7))       # 6 (125 % 7)
print(pow(10, 4, 17))     # 4 (10000 % 17)

print("pow with mod=1:")
print(pow(100, 50, 1))    # 0
print(pow(999, 999, 1))   # 0

print("pow edge cases:")
print(pow(0, 5))          # 0
print(pow(1, 1000))       # 1
print(pow(2, 0, 5))       # 1


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

print("round with ndigits=3:")
print(round(3.14159, 3))  # 3.142
print(round(2.71828, 3))  # 2.718

print("round with ndigits=0:")
print(round(3.7, 0))      # 4.0
print(round(3.2, 0))      # 3.0

print("round with negative ndigits:")
print(round(1234, -1))    # 1230
print(round(1234, -2))    # 1200
print(round(1234, -3))    # 1000
print(round(5678, -1))    # 5680
print(round(5678, -2))    # 5700

print("round negative numbers:")
print(round(-3.14159, 2)) # -3.14


print("builtins_numeric_simple tests done")
