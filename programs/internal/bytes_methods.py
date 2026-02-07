"""Test bytes-related methods: int.to_bytes and int.from_bytes."""

from __future__ import annotations


# int.to_bytes - convert integer to bytes
num = 255
b = num.to_bytes(1, "big")
print(len(b))  # 1
print(b[0])  # 255


# Larger number
num2 = 65535
b2 = num2.to_bytes(2, "big")
print(len(b2))  # 2
print(b2[0])  # 255
print(b2[1])  # 255


# Little endian
num3 = 256
b3 = num3.to_bytes(2, "little")
print(b3[0])  # 0
print(b3[1])  # 1


# int.from_bytes - convert bytes back to integer
data = bytes([0, 255])
result = int.from_bytes(data, "big")
print(result)  # 255


# Larger bytes
data2 = bytes([1, 0, 0])
result2 = int.from_bytes(data2, "big")
print(result2)  # 65536


# Little endian from_bytes
data3 = bytes([0, 1])
result3 = int.from_bytes(data3, "little")
print(result3)  # 256


print("bytes_methods tests done")
