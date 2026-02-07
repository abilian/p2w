"""WAT builtin functions.

This package contains the Python builtin function implementations,
organized into cohesive modules.
"""

from __future__ import annotations

from .constructors import (
    BOOL_CODE,
    BYTES_CODE,
    CONSTRUCTORS_CODE,
    DICT_CODE,
    FLOAT_CODE,
    INT_CODE,
    LIST_CODE,
    SET_CODE,
    STR_CODE,
    TUPLE_CODE,
)
from .direct import (
    DIRECT_BUILTINS,
    DIRECT_BUILTINS_CODE,
)
from .introspection import (
    CALLABLE_CODE,
    DELATTR_CODE,
    GETATTR_CODE,
    HASATTR_CODE,
    ID_CODE,
    INTROSPECTION_CODE,
    ISINSTANCE_CODE,
    ISSUBCLASS_CODE,
    SETATTR_CODE,
    TYPE_CODE,
)
from .io import (
    IO_CODE,
    PRINT_CODE,
)
from .js_interop import (
    JS_ALERT_CODE,
    JS_GET_ELEMENT_CODE,
    JS_INTEROP_CODE,
    JS_LOG_CODE,
    JS_SET_TEXT_CODE,
)
from .math import (
    ABS_CODE,
    DIVMOD_CODE,
    MATH_CODE,
    POW_CODE,
    ROUND_CODE,
)
from .sequences import (
    ALL_CODE,
    ANY_CODE,
    ENUMERATE_CODE,
    FILTER_CODE,
    LEN_CODE,
    MAP_CODE,
    MAX_CODE,
    MIN_CODE,
    NEXT_CODE,
    RANGE_BUILTIN_CODE,
    REVERSED_CODE,
    SEQUENCES_CODE,
    SORTED_CODE,
    SUM_CODE,
    ZIP_CODE,
)
from .strings import (
    ASCII_CODE,
    BIN_CODE,
    CHR_CODE,
    HEX_CODE,
    OCT_CODE,
    ORD_CODE,
    REPR_CODE,
    STRINGS_CODE,
)
from .super import (
    SUPER_CODE,
)

# Combine all builtin code in dependency order
BUILTINS_CODE = (
    IO_CODE
    + CONSTRUCTORS_CODE
    + SEQUENCES_CODE
    + INTROSPECTION_CODE
    + MATH_CODE
    + STRINGS_CODE
    + SUPER_CODE
    + JS_INTEROP_CODE
    + DIRECT_BUILTINS_CODE  # Optimized direct-call versions
)

__all__ = [
    "ABS_CODE",
    "ALL_CODE",
    "ANY_CODE",
    "ASCII_CODE",
    "BIN_CODE",
    "BOOL_CODE",
    "BUILTINS_CODE",
    "BYTES_CODE",
    "CALLABLE_CODE",
    "CHR_CODE",
    "CONSTRUCTORS_CODE",
    "DELATTR_CODE",
    "DICT_CODE",
    "DIRECT_BUILTINS",
    "DIRECT_BUILTINS_CODE",
    "DIVMOD_CODE",
    "ENUMERATE_CODE",
    "FILTER_CODE",
    "FLOAT_CODE",
    "GETATTR_CODE",
    "HASATTR_CODE",
    "HEX_CODE",
    "ID_CODE",
    "INTROSPECTION_CODE",
    "INT_CODE",
    "IO_CODE",
    "ISINSTANCE_CODE",
    "ISSUBCLASS_CODE",
    "JS_ALERT_CODE",
    "JS_GET_ELEMENT_CODE",
    "JS_INTEROP_CODE",
    "JS_LOG_CODE",
    "JS_SET_TEXT_CODE",
    "LEN_CODE",
    "LIST_CODE",
    "MAP_CODE",
    "MATH_CODE",
    "MAX_CODE",
    "MIN_CODE",
    "NEXT_CODE",
    "OCT_CODE",
    "ORD_CODE",
    "POW_CODE",
    "PRINT_CODE",
    "RANGE_BUILTIN_CODE",
    "REPR_CODE",
    "REVERSED_CODE",
    "ROUND_CODE",
    "SEQUENCES_CODE",
    "SETATTR_CODE",
    "SET_CODE",
    "SORTED_CODE",
    "STRINGS_CODE",
    "STR_CODE",
    "SUM_CODE",
    "SUPER_CODE",
    "TUPLE_CODE",
    "TYPE_CODE",
    "ZIP_CODE",
]
