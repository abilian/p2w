"""p2w compiler package - Python AST to WebAssembly Text (WAT).

This package compiles a subset of Python to WAT using WASM GC for memory management.
"""

from __future__ import annotations

from p2w.compiler.builtins import BUILTINS, BuiltinFunc
from p2w.compiler.compiler import WasmCompiler, compile_to_wat
from p2w.compiler.context import LexicalEnv

__all__ = [
    "BUILTINS",
    "BuiltinFunc",
    "LexicalEnv",
    "WasmCompiler",
    "compile_to_wat",
]
