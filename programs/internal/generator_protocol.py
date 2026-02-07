"""Test generator protocol methods: send(), throw(), close()."""

from __future__ import annotations


# Generator that receives values via send()
def accumulator():
    total = 0
    while True:
        value = yield total
        if value is None:
            break
        total += value


# Test send()
gen = accumulator()
print(next(gen))  # Start generator, prints 0
print(gen.send(10))  # Send 10, prints 10
print(gen.send(5))  # Send 5, prints 15
print(gen.send(3))  # Send 3, prints 18


# Generator that handles thrown exceptions
def resilient():
    while True:
        try:
            yield "ready"
        except ValueError:
            yield "caught ValueError"


gen2 = resilient()
print(next(gen2))  # "ready"
print(gen2.throw(ValueError))  # "caught ValueError"
print(next(gen2))  # "ready" again


# Generator close() - basic
def simple_gen():
    yield 1
    yield 2
    yield 3


gen3 = simple_gen()
print(next(gen3))  # 1
result = gen3.close()
print(result)  # None (close returns None)

# Verify generator is closed
try:
    next(gen3)
    print("ERROR: should have raised StopIteration")
except StopIteration:
    print("correctly closed")


# Generator that catches GeneratorExit
def cleanup_gen():
    try:
        yield 1
        yield 2
    except GeneratorExit:
        print("cleanup on close")
        raise  # Must re-raise GeneratorExit


gen4 = cleanup_gen()
print(next(gen4))  # 1
gen4.close()  # Prints "cleanup on close"


# Generator that yields values after catching exception
def continues_after_throw():
    try:
        yield 1
    except ValueError:
        pass
    yield 2
    yield 3


gen5 = continues_after_throw()
print(next(gen5))  # 1
try:
    gen5.throw(ValueError)
except StopIteration:
    pass
# Generator continues
print(next(gen5))  # 2


# Echo generator using send
def echo():
    value = None
    while True:
        received = yield value
        value = received


gen6 = echo()
next(gen6)  # Start
print(gen6.send("hello"))  # "hello"
print(gen6.send("world"))  # "world"


print("generator protocol tests done")
