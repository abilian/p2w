# Test Ellipsis literal: ... and Ellipsis

# Basic ellipsis literal
x = ...
print(x is ...)  # True

# Ellipsis is a singleton
y = ...
print(x is y)  # True

# Ellipsis name
z = Ellipsis
print(z is ...)  # True

# Ellipsis in tuple
t = (1, ..., 3)
print(len(t))  # 3
print(t[1] is ...)  # True

# Ellipsis in list
lst = [1, 2, ...]
print(len(lst))  # 3
print(lst[2] is ...)  # True


# Ellipsis as placeholder in function
def not_implemented_yet(): ...


# Call it - should not error
not_implemented_yet()
print("function with ... body works")


# Ellipsis in class body
class Placeholder: ...


p = Placeholder()
print("class with ... body works")


# Ellipsis as default value
def func_with_sentinel(value=...):
    if value is ...:
        return "no value provided"
    return value


print(func_with_sentinel())  # "no value provided"
print(func_with_sentinel("hello"))  # "hello"


# Ellipsis in conditional
def check_ellipsis(x):
    if x is ...:
        return "ellipsis"
    return "other"


print(check_ellipsis(...))  # "ellipsis"
print(check_ellipsis(None))  # "other"
print(check_ellipsis(0))  # "other"


# Ellipsis is truthy
if ...:
    print("ellipsis is truthy")


# Ellipsis as dict value
d = {"placeholder": ...}
print(d["placeholder"] is ...)  # True


print("ellipsis tests done")
