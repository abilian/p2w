# Test large integers (exceeding i31 range)
# i31 range: -1073741824 to 1073741823

# Large positive integer
big = 2000000000
print(big)

# Large negative integer
neg_big = -2000000000
print(neg_big)

# Just outside i31 max
just_over = 1073741824
print(just_over)

# Just outside i31 min
just_under = -1073741825
print(just_under)

# Arithmetic with large numbers
a = 1000000000
b = 1000000000
print(a + b)  # 2000000000 (overflows i31, should use INT64)

# Multiplication that overflows
x = 50000
y = 50000
print(x * y)  # 2500000000 (overflows i31)

# Subtraction with large negative result
c = -1000000000
d = 1500000000
print(c - d)  # -2500000000

# Division with large numbers
print(big // 2)  # 1000000000

# Modulo with large numbers
print(big % 3)  # 2000000000 % 3 = 2

# Negation
print(-big)  # -2000000000

# Comparison
print(big == 2000000000)
print(big > 1000000000)
print(big < 3000000000)

# Large integer in list
lst = [big, neg_big]
print(lst[0])
print(lst[1])

# Large integer with float comparison
print(big == 2000000000.0)

# Large integer to string (via f-string)
print(f"big = {big}")
