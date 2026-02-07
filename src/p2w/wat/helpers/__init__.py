"""WAT runtime helper functions.

This package contains the runtime helper functions used by the p2w compiler,
organized into cohesive modules.
"""

from __future__ import annotations

from p2w.wat.builtins.direct import DIRECT_BUILTINS_CODE

from .arithmetic import ARITHMETIC_CODE
from .bytes_ops import BYTES_OPS_CODE
from .comparisons import COMPARISONS_CODE
from .containers import CONTAINERS_CODE
from .core import CORE_CODE
from .dicts import DICTS_CODE
from .exceptions import EXCEPTIONS_CODE
from .generators import GENERATORS_CODE
from .integers import INTEGERS_CODE
from .js_interop import JS_INTEROP_CODE
from .lists import LISTS_CODE
from .objects import OBJECTS_CODE
from .sets import SETS_CODE
from .sorting import SORTING_CODE
from .strings import STRINGS_CODE
from .tuples import TUPLES_CODE

# Combine all helper code in dependency order
HELPERS_CODE = (
    CORE_CODE
    + INTEGERS_CODE
    + STRINGS_CODE
    + COMPARISONS_CODE
    + TUPLES_CODE
    + LISTS_CODE
    + DICTS_CODE
    + SETS_CODE
    + BYTES_OPS_CODE
    + CONTAINERS_CODE
    + ARITHMETIC_CODE
    + OBJECTS_CODE
    + EXCEPTIONS_CODE
    + GENERATORS_CODE
    + SORTING_CODE
    + JS_INTEROP_CODE
    + DIRECT_BUILTINS_CODE  # Optimized direct-call builtins
)

__all__ = ["HELPERS_CODE"]
