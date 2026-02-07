"""p2w: Python subset to WebAssembly compiler."""

from __future__ import annotations

import pathlib
import sys

from p2w.compiler import compile_to_wat


def main() -> None:
    """Entry point for p2w CLI."""
    if len(sys.argv) < 2:
        print("Usage: p2w <source.py>")
        sys.exit(1)

    source_file = sys.argv[1]
    source = pathlib.Path(source_file).read_text()

    wat_code = compile_to_wat(source)
    print(wat_code)


__all__ = ["compile_to_wat", "main"]
