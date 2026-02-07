"""Test string conversion builtins: bin, hex, oct."""

from __future__ import annotations


# =============================================================================
# bin() - binary representation
# =============================================================================

print("bin basic:")
print(bin(0))       # 0b0
print(bin(1))       # 0b1
print(bin(2))       # 0b10
print(bin(3))       # 0b11
print(bin(4))       # 0b100
print(bin(5))       # 0b101

print("bin powers of 2:")
print(bin(8))       # 0b1000
print(bin(16))      # 0b10000
print(bin(32))      # 0b100000
print(bin(64))      # 0b1000000
print(bin(128))     # 0b10000000
print(bin(256))     # 0b100000000

print("bin various numbers:")
print(bin(10))      # 0b1010
print(bin(15))      # 0b1111
print(bin(100))     # 0b1100100
print(bin(255))     # 0b11111111
print(bin(1000))    # 0b1111101000

print("bin negative numbers:")
print(bin(-1))      # -0b1
print(bin(-2))      # -0b10
print(bin(-10))     # -0b1010
print(bin(-255))    # -0b11111111


# =============================================================================
# hex() - hexadecimal representation
# =============================================================================

print("hex basic:")
print(hex(0))       # 0x0
print(hex(1))       # 0x1
print(hex(9))       # 0x9
print(hex(10))      # 0xa
print(hex(15))      # 0xf
print(hex(16))      # 0x10

print("hex powers of 16:")
print(hex(256))     # 0x100
print(hex(4096))    # 0x1000
print(hex(65536))   # 0x10000

print("hex various numbers:")
print(hex(100))     # 0x64
print(hex(255))     # 0xff
print(hex(1000))    # 0x3e8
print(hex(12345))   # 0x3039
print(hex(65535))   # 0xffff

print("hex colors (common use case):")
print(hex(16711680))  # 0xff0000 (red)
print(hex(65280))     # 0xff00 (green)
print(hex(255))       # 0xff (blue)

print("hex negative numbers:")
print(hex(-1))      # -0x1
print(hex(-16))     # -0x10
print(hex(-255))    # -0xff
print(hex(-256))    # -0x100


# =============================================================================
# oct() - octal representation
# =============================================================================

print("oct basic:")
print(oct(0))       # 0o0
print(oct(1))       # 0o1
print(oct(7))       # 0o7
print(oct(8))       # 0o10
print(oct(9))       # 0o11

print("oct powers of 8:")
print(oct(64))      # 0o100
print(oct(512))     # 0o1000
print(oct(4096))    # 0o10000

print("oct various numbers:")
print(oct(10))      # 0o12
print(oct(100))     # 0o144
print(oct(255))     # 0o377
print(oct(511))     # 0o777
print(oct(1000))    # 0o1750

print("oct file permissions (common use case):")
print(oct(493))     # 0o755 (rwxr-xr-x)
print(oct(420))     # 0o644 (rw-r--r--)
print(oct(511))     # 0o777 (rwxrwxrwx)

print("oct negative numbers:")
print(oct(-1))      # -0o1
print(oct(-8))      # -0o10
print(oct(-64))     # -0o100


# =============================================================================
# Conversions and round-trips
# =============================================================================

print("round-trip bin:")
# Convert to binary string, parse back
val = 42
binary_str = bin(val)
print(binary_str)           # 0b101010
# Parse binary (strip 0b prefix)
parsed = int(binary_str, 2)
print(parsed)               # 42
print(val == parsed)        # True

print("round-trip hex:")
val = 255
hex_str = hex(val)
print(hex_str)              # 0xff
parsed = int(hex_str, 16)
print(parsed)               # 255
print(val == parsed)        # True

print("round-trip oct:")
val = 493
oct_str = oct(val)
print(oct_str)              # 0o755
parsed = int(oct_str, 8)
print(parsed)               # 493
print(val == parsed)        # True


# =============================================================================
# Formatting without prefix
# =============================================================================

print("format without prefix:")
# Using string slicing to remove prefix
print(bin(255)[2:])   # 11111111
print(hex(255)[2:])   # ff
print(oct(255)[2:])   # 377

# Uppercase hex
print(hex(255)[2:].upper())  # FF


# =============================================================================
# Combining with other operations
# =============================================================================

print("combining operations:")

# Binary bit counting (count 1s)
num = 255
binary = bin(num)
ones = binary.count("1")
print(ones)  # 8

# Hex padding
val = 15
h = hex(val)[2:]
print(h.zfill(4))  # 000f

# Format multiple numbers
nums = [10, 20, 30]
for n in nums:
    print(bin(n), hex(n), oct(n))


print("builtins_string_conversions tests done")
