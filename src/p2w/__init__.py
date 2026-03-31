"""p2w: Python subset to WebAssembly compiler."""

from __future__ import annotations

import argparse
import pathlib
import sys
from importlib.metadata import version

from p2w.compiler import compile_to_wat


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="p2w",
        description="Compile Python source to WebAssembly (WAT format).",
    )
    parser.add_argument(
        "source",
        help="Python source file to compile",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="write WAT output to file instead of stdout",
    )
    parser.add_argument(
        "-r",
        "--run",
        action="store_true",
        help="compile and run immediately (requires wasmtime)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="show compilation details on stderr",
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="show debug information (AST dump, generated WAT)",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {version('p2w')}",
    )
    return parser


def main() -> None:
    """Entry point for p2w CLI."""
    parser = _build_parser()
    args = parser.parse_args()

    source_path = pathlib.Path(args.source)
    if not source_path.exists():
        print(f"p2w: error: file not found: {args.source}", file=sys.stderr)
        sys.exit(1)

    source = source_path.read_text()

    if args.debug:
        import ast

        tree = ast.parse(source)
        print("--- AST ---", file=sys.stderr)
        print(ast.dump(tree, indent=2), file=sys.stderr)
        print("---", file=sys.stderr)

    if args.verbose:
        print(f"Compiling {args.source}...", file=sys.stderr)

    wat_code = compile_to_wat(source)

    if args.verbose:
        lines = wat_code.count("\n")
        print(f"Generated {lines} lines of WAT.", file=sys.stderr)

    if args.run:
        from p2w.runner import run_wat

        output = run_wat(wat_code)
        print(output, end="")
    elif args.output:
        pathlib.Path(args.output).write_text(wat_code)
        if args.verbose:
            print(f"Wrote {args.output}", file=sys.stderr)
    else:
        print(wat_code)


__all__ = ["compile_to_wat", "main"]
