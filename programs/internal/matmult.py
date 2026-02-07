"""Test matrix multiplication operator: @."""

from __future__ import annotations


# Class implementing __matmul__
class Matrix:
    def __init__(self, data):
        self.data = data
        self.rows = len(data)
        self.cols = len(data[0]) if data else 0

    def __matmul__(self, other):
        # Simple matrix multiplication
        if self.cols != other.rows:
            raise ValueError("Incompatible dimensions")
        result = []
        for i in range(self.rows):
            row = []
            for j in range(other.cols):
                total = 0
                for k in range(self.cols):
                    total += self.data[i][k] * other.data[k][j]
                row.append(total)
            result.append(row)
        return Matrix(result)

    def __str__(self):
        return str(self.data)


# 2x2 matrix multiplication
a = Matrix([[1, 2], [3, 4]])
b = Matrix([[5, 6], [7, 8]])
c = a @ b
print(c.data[0])  # [19, 22]
print(c.data[1])  # [43, 50]


# 2x3 @ 3x2 = 2x2
m1 = Matrix([[1, 2, 3], [4, 5, 6]])
m2 = Matrix([[7, 8], [9, 10], [11, 12]])
m3 = m1 @ m2
print(m3.data[0])  # [58, 64]
print(m3.data[1])  # [139, 154]


# Vector class with dot product via @
class Vector:
    def __init__(self, values):
        self.values = values

    def __matmul__(self, other):
        # Dot product
        if len(self.values) != len(other.values):
            raise ValueError("Vectors must have same length")
        total = 0
        for i in range(len(self.values)):
            total += self.values[i] * other.values[i]
        return total


v1 = Vector([1, 2, 3])
v2 = Vector([4, 5, 6])
dot = v1 @ v2
print(dot)  # 1*4 + 2*5 + 3*6 = 32


# Identity matrix test
identity = Matrix([[1, 0], [0, 1]])
a = Matrix([[5, 6], [7, 8]])
result = a @ identity
print(result.data[0])  # [5, 6]
print(result.data[1])  # [7, 8]


print("matmult tests done")
