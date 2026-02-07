"""Test f-string format specifiers.

This showcases the f-string formatting capabilities including:
- Thousands separator (:,)
- Width and alignment (<, >, ^)
- Custom fill characters
- Zero padding
- Precision for floats
- Combined format specifiers
"""

from __future__ import annotations


# ============================================================================
# Thousands Separator
# ============================================================================

print("=== Thousands Separator ===")

# Basic thousands separator
big_num = 1234567
print(f"1234567 with commas: {big_num:,}")

# Larger number
million = 1000000
print(f"One million: {million:,}")

# Billions
billion = 1234567890
print(f"Billion: {billion:,}")

# Small number (no commas needed)
small = 123
print(f"123 with commas: {small:,}")

# Zero
zero = 0
print(f"Zero with commas: {zero:,}")

# Negative number
negative = -9876543
print(f"Negative: {negative:,}")


# ============================================================================
# Thousands with Float Precision
# ============================================================================

print("\n=== Thousands + Precision ===")

# Float with thousands and precision
price = 1234567.89
print(f"Price: {price:,.2f}")

# Large money amount
salary = 150000.5
print(f"Salary: {salary:,.2f}")

# Percentage (small)
rate = 1234.567
print(f"Rate: {rate:,.1f}")


# ============================================================================
# Width and Alignment
# ============================================================================

print("\n=== Width and Alignment ===")

# Right align (default for numbers)
val = 42
print(f"Right align :>10 : '{val:>10}'")

# Left align
name = "hi"
print(f"Left align  :<10 : '{name:<10}'")

# Center align
mid = "X"
print(f"Center      :^10 : '{mid:^10}'")

# Number alignment
for i in [1, 12, 123, 1234]:
    print(f"  {i:>6}")


# ============================================================================
# Custom Fill Characters
# ============================================================================

print("\n=== Custom Fill Characters ===")

# Star fill
num = 42
print(f"Star fill   :*>8 : '{num:*>8}'")

# Dot fill
text = "hi"
print(f"Dot fill    :.<8 : '{text:.<8}'")

# Dash fill centered
item = "OK"
print(f"Dash center :-^10: '{item:-^10}'")

# Underscore
code = 7
print(f"Underscore  :_>5 : '{code:_>5}'")


# ============================================================================
# Zero Padding
# ============================================================================

print("\n=== Zero Padding ===")

# Basic zero padding
n = 42
print(f"Zero pad :05 : '{n:05}'")

# Larger width
m = 7
print(f"Zero pad :08 : '{m:08}'")

# Time-like formatting
hours = 9
minutes = 5
seconds = 3
print(f"Time: {hours:02}:{minutes:02}:{seconds:02}")


# ============================================================================
# Combined Format Specifiers
# ============================================================================

print("\n=== Combined Formats ===")

# Width with precision
pi = 3.14159
print(f"Pi :10.2f  : '{pi:10.2f}'")

# Right align with precision
value = 123.456
print(f"Value :>12.3f: '{value:>12.3f}'")


# ============================================================================
# Practical Examples
# ============================================================================

print("\n=== Practical Examples ===")

# Financial report
revenue = 1234567.89
expenses = 987654.32
profit = revenue - expenses

print("Financial Summary:")
print(f"  Revenue:  ${revenue:>15,.2f}")
print(f"  Expenses: ${expenses:>15,.2f}")
print(f"  Profit:   ${profit:>15,.2f}")

# Table formatting
print("\nProduct Table:")
print(f"{'Item':<15} {'Price':>10} {'Qty':>5}")
print(f"{'-' * 15} {'-' * 10} {'-' * 5}")
print(f"{'Widget':<15} {'$19.99':>10} {'100':>5}")
print(f"{'Gadget':<15} {'$249.00':>10} {'25':>5}")
print(f"{'Thingamajig':<15} {'$5.50':>10} {'500':>5}")

# ID formatting
print("\nID Numbers:")
for id_num in [1, 42, 999, 10000]:
    print(f"  ID-{id_num:06}")
