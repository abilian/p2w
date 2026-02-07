"""WAT (WebAssembly Text) code generation modules.

This package contains the WAT code strings used by the p2w compiler.
The code is organized into logical modules for maintainability.
"""

from __future__ import annotations

from .builtins import BUILTINS_CODE
from .helpers import HELPERS_CODE
from .imports import IMPORTS_CODE, POST_TYPES_GLOBALS
from .types import TYPES_CODE

__all__ = [
    "BUILTINS_CODE",
    "HELPERS_CODE",
    "IMPORTS_CODE",
    "POST_TYPES_GLOBALS",
    "TYPES_CODE",
]
