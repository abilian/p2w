"""Test Python dict methods on plain objects.

This tests that .get(), .keys(), .values(), .items() work correctly
on objects that don't have native implementations of these methods.

The fix: Changed method implementations to check if native method exists
before calling it, preventing "can't access property 'apply'" errors.
"""

# Test .get() with default value
obj = {"a": 1, "b": 2, "c": 3}

# Basic get
print(obj.get("a"))  # 1
print(obj.get("b"))  # 2

# Get with default
print(obj.get("x", 99))  # 99 (key doesn't exist)
print(obj.get("a", 99))  # 1 (key exists, default ignored)

# Get missing key without default returns None
result = obj.get("missing")
if result is None:
    print("None")
else:
    print(result)


# Test .keys()
keys = obj.keys()
keys_list = list(keys)
keys_list.sort()
print(keys_list)  # ['a', 'b', 'c']


# Test .values()
vals = obj.values()
vals_list = list(vals)
vals_list.sort()
print(vals_list)  # [1, 2, 3]


# Test .items()
# Note: In JS, items returns arrays not tuples
items = obj.items()
items_list = list(items)
items_list.sort()
# Print individual items to avoid tuple/list difference
for item in items_list:
    print(item[0], item[1])


# Test .setdefault()
obj2 = {"x": 10}
print(obj2.setdefault("x", 20))  # 10 (key exists)
print(obj2.setdefault("y", 30))  # 30 (key doesn't exist, set it)
print(obj2.get("y"))  # 30 (key was set)


# Test .update()
obj3 = {"a": 1}
obj3.update({"b": 2, "c": 3})
keys3 = list(obj3.keys())
keys3.sort()
print(keys3)  # ['a', 'b', 'c']


# Test for-in iteration (already worked, but verify)
result_keys = []
for key in obj:
    result_keys.append(key)
result_keys.sort()
print(result_keys)  # ['a', 'b', 'c']
