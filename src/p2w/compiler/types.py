"""Type representation for compile-time type inference.

These types represent the p2w type system at compile time,
enabling specialized code generation for known types.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class BobType:
    """Base class for p2w types."""


@dataclass(frozen=True)
class IntType(BobType):
    """Integer type (i31 or INT64) - boxed."""


@dataclass(frozen=True)
class FloatType(BobType):
    """Float type (f64) - boxed."""


# Native WASM types - these use unboxed WASM locals directly
@dataclass(frozen=True)
class I32Type(BobType):
    """Native 32-bit integer - stored as WASM i32."""


@dataclass(frozen=True)
class I64Type(BobType):
    """Native 64-bit integer - stored as WASM i64."""


@dataclass(frozen=True)
class F64Type(BobType):
    """Native 64-bit float - stored as WASM f64."""


@dataclass(frozen=True)
class StringType(BobType):
    """String type."""


@dataclass(frozen=True)
class BoolType(BobType):
    """Boolean type."""


@dataclass(frozen=True)
class NoneType(BobType):
    """None type."""


@dataclass(frozen=True)
class ListType(BobType):
    """List type with optional element type."""

    element_type: BobType | None = None


@dataclass(frozen=True)
class DictType(BobType):
    """Dict type with optional key/value types."""

    key_type: BobType | None = None
    value_type: BobType | None = None


@dataclass(frozen=True)
class TupleType(BobType):
    """Tuple type with element types."""

    element_types: tuple[BobType, ...] = ()


@dataclass(frozen=True)
class FunctionType(BobType):
    """Function type with parameter and return types."""

    param_types: tuple[BobType, ...] = ()
    return_type: BobType | None = None


@dataclass(frozen=True)
class ClassType(BobType):
    """Class type."""

    name: str = ""


@dataclass(frozen=True)
class UnknownType(BobType):
    """Unknown type (requires runtime dispatch)."""


# Singleton instances for common types
INT = IntType()
FLOAT = FloatType()
STRING = StringType()
BOOL = BoolType()
NONE = NoneType()
UNKNOWN = UnknownType()

# Native WASM type singletons
I32 = I32Type()
I64 = I64Type()
F64 = F64Type()


def combine_types(left: BobType, right: BobType, op: str) -> BobType:
    """Determine result type of binary operation.

    Args:
        left: Type of left operand
        right: Type of right operand
        op: Operation ('+', '-', '*', '/', etc.)

    Returns:
        Result type of the operation
    """
    # Native type operations - preserve native types
    match (left, right, op):
        # i32 operations
        case (
            I32Type(),
            I32Type(),
            "+" | "-" | "*" | "//" | "%" | "&" | "|" | "^" | "<<" | ">>",
        ):
            return I32
        case (I32Type(), I32Type(), "/"):
            return F64  # Division returns float

        # i64 operations
        case (
            I64Type(),
            I64Type(),
            "+" | "-" | "*" | "//" | "%" | "&" | "|" | "^" | "<<" | ">>",
        ):
            return I64
        case (I64Type(), I64Type(), "/"):
            return F64

        # f64 operations
        case (F64Type(), F64Type(), "+" | "-" | "*" | "/" | "//" | "%" | "**"):
            return F64

        # Mixed native types: promote to larger/float
        case (I32Type(), I64Type(), _) | (I64Type(), I32Type(), _):
            return I64
        case (I32Type() | I64Type(), F64Type(), _) | (
            F64Type(),
            I32Type() | I64Type(),
            _,
        ):
            return F64

        # Native + boxed type: preserve native type
        case (
            I32Type(),
            IntType(),
            "+" | "-" | "*" | "//" | "%" | "&" | "|" | "^" | "<<" | ">>",
        ):
            return I32
        case (
            IntType(),
            I32Type(),
            "+" | "-" | "*" | "//" | "%" | "&" | "|" | "^" | "<<" | ">>",
        ):
            return I32
        case (
            I64Type(),
            IntType(),
            "+" | "-" | "*" | "//" | "%" | "&" | "|" | "^" | "<<" | ">>",
        ):
            return I64
        case (
            IntType(),
            I64Type(),
            "+" | "-" | "*" | "//" | "%" | "&" | "|" | "^" | "<<" | ">>",
        ):
            return I64
        case (
            F64Type(),
            FloatType() | IntType(),
            "+" | "-" | "*" | "/" | "//" | "%" | "**",
        ):
            return F64
        case (
            FloatType() | IntType(),
            F64Type(),
            "+" | "-" | "*" | "/" | "//" | "%" | "**",
        ):
            return F64

    # Division always returns float
    if op == "/":
        return FLOAT

    match (left, right, op):
        # Float involved = float for numeric ops
        case (FloatType(), _, "+" | "-" | "*" | "//" | "%" | "**"):
            return FLOAT
        case (_, FloatType(), "+" | "-" | "*" | "//" | "%" | "**"):
            return FLOAT

        # int + int = int
        case (IntType(), IntType(), _):
            return INT

        # str + str = str (concatenation)
        case (StringType(), StringType(), "+"):
            return STRING

        # str * int or int * str = str (repetition)
        case (StringType(), IntType(), "*") | (IntType(), StringType(), "*"):
            return STRING

        # list + list = list (concatenation)
        case (ListType() as lt, ListType() as rt, "+"):
            if lt.element_type == rt.element_type:
                return ListType(lt.element_type)
            return ListType()

        # list * int or int * list = list (repetition)
        case (ListType() as lt, IntType(), "*"):
            return ListType(lt.element_type)
        case (IntType(), ListType() as rt, "*"):
            return ListType(rt.element_type)

    return UNKNOWN


def is_numeric(typ: BobType) -> bool:
    """Check if type is numeric (int or float, boxed or native)."""
    return isinstance(typ, (IntType, FloatType, I32Type, I64Type, F64Type))


def is_native_type(typ: BobType) -> bool:
    """Check if type is a native WASM type (unboxed)."""
    return isinstance(typ, (I32Type, I64Type, F64Type))


def is_native_int(typ: BobType) -> bool:
    """Check if type is a native integer type."""
    return isinstance(typ, (I32Type, I64Type))


def is_native_float(typ: BobType) -> bool:
    """Check if type is a native float type."""
    return isinstance(typ, F64Type)


def get_native_wasm_type(typ: BobType) -> NativeType | None:
    """Get the corresponding NativeType for a BobType."""
    match typ:
        case I32Type():
            return NativeType.I32
        case I64Type():
            return NativeType.I64
        case F64Type():
            return NativeType.F64
    return None


def is_known(typ: BobType) -> bool:
    """Check if type is known (not Unknown)."""
    return not isinstance(typ, UnknownType)


class NativeType(Enum):
    """Native WASM types for unboxed variable storage.

    Variables with these types can be stored directly in WASM locals
    without boxing, eliminating struct.new/struct.get overhead.
    """

    F64 = "f64"  # 64-bit float
    I32 = "i32"  # 32-bit integer (for small ints, loop counters)
    I64 = "i64"  # 64-bit integer (for large ints)
