"""Test bytes encoding and decoding: str(bytes, encoding), bytes(str, encoding)."""

from __future__ import annotations


# bytes() with string and encoding
b1 = bytes("hello", "utf-8")
print(len(b1))  # 5
print(b1[0])  # 104 (h)
print(b1[1])  # 101 (e)


# str() with bytes and encoding (decode)
b2 = bytes([104, 101, 108, 108, 111])  # "hello" in bytes
s = str(b2, "utf-8")
print(s)  # hello


# int.to_bytes with signed parameter
# Positive number, signed
n1 = 127
b3 = n1.to_bytes(1, "big", signed=True)
print(b3[0])  # 127

# Negative number needs signed=True
n2 = -1
b4 = n2.to_bytes(1, "big", signed=True)
print(b4[0])  # 255 (two's complement)

n3 = -128
b5 = n3.to_bytes(1, "big", signed=True)
print(b5[0])  # 128


# int.from_bytes with signed parameter
# Unsigned interpretation
data1 = bytes([255])
print(int.from_bytes(data1, "big"))  # 255

# Signed interpretation
print(int.from_bytes(data1, "big", signed=True))  # -1

data2 = bytes([128])
print(int.from_bytes(data2, "big", signed=True))  # -128


print("bytes_encoding tests done")
