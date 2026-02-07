"""Integration tests for programs/internal/ test files.

These tests run the Python programs through p2w and compare output to CPython.
The main test class (TestProgramExecution) actually runs each program and compares
outputs, using xfail for programs that don't work yet.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from p2w.compiler import compile_to_wat
from p2w.runner import run_python, run_wat, wat_to_wasm

# Path to test programs
PROGRAMS_DIR = Path(__file__).parent.parent.parent / "programs" / "internal"


def has_wasm_tools() -> bool:
    """Check if wasm-tools is available."""
    try:
        subprocess.run(
            ["wasm-tools", "--version"],
            check=True,
            capture_output=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def has_node_with_wasm_gc() -> bool:
    """Check if Node.js with WASM GC support is available."""
    try:
        result = subprocess.run(
            ["node", "--version"],
            check=True,
            capture_output=True,
            text=True,
        )
        version = result.stdout.strip()
        major = int(version.lstrip("v").split(".")[0])
        return major >= 22
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
        return False


# Programs that are known to work - these MUST pass
WORKING_PROGRAMS: set[str] = {
    "assign.py",
    "boolean_logic.py",
    "boolean_none.py",
    "builtin_functions.py",
    "builtins_extended.py",
    "bytes_encoding.py",
    "bytes_literals.py",
    "bytes_methods.py",
    "chained_assignment.py",
    "chained_calls.py",
    "class.py",
    "closures_nested.py",
    "class_advanced.py",
    "class_hierarchy.py",
    "class_inherit_super.py",
    "class_property_basic.py",
    "class_property.py",
    "class_special_methods.py",
    "class_staticclassmethod.py",
    "class_super.py",
    "comparison_types.py",
    "comprehensions.py",
    "comprehensions_advanced.py",
    "constant_folding.py",
    "constructors_advanced.py",
    "context_manager.py",
    "context_managers.py",
    "control_flow.py",
    "control_flow_advanced.py",
    "decorators_basic.py",
    "decorators.py",
    "del_statements.py",
    "dict_construct.py",
    "dict_methods.py",
    "dict_set_edge_cases.py",
    "dict_unpacking.py",
    "ellipsis.py",
    "exception_chaining_simple.py",
    "exception_chaining.py",
    "exception_patterns.py",
    "exceptions.py",
    "fstring_formatting.py",
    "generator_expr.py",
    "generators.py",
    "fstrings.py",
    "function_args.py",
    "functions.py",
    "global_nonlocal.py",
    "hash_collections.py",
    "int_base.py",
    "isinstance_classes.py",
    "isinstance_comprehensive.py",
    "iteration_patterns.py",
    "js_object_methods.py",
    "kwargs_call.py",
    "lambda.py",
    "large_integers.py",
    "list_array_backed.py",
    "list_edge_cases.py",
    "list_methods.py",
    "listcomp_basic.py",
    "match_statements.py",
    "matmult.py",
    "minmax_mixed.py",
    "lists.py",
    "negative_indexing.py",
    "numeric_edge_cases.py",
    "operators.py",
    "print.py",
    "print_advanced.py",
    "repr_types.py",
    "reserved_words.py",
    "scope.py",
    "set_literals.py",
    "slices.py",
    "sort_advanced.py",
    "sorted_comprehensive.py",
    "sorted_numbers.py",
    "special_methods.py",
    "starred.py",
    "string_methods.py",
    "string_operations.py",
    "super_explicit.py",
    "unpacking_advanced.py",
    "strings.py",
    "tuples.py",
    "type_annotations.py",
    "type_builtin.py",
    "type_constructors.py",
    "type_conversions.py",
    "walrus.py",
    "walrus_patterns.py",
}

# Programs that are out of scope (require features we won't implement)
OUT_OF_SCOPE: set[str] = {
    "async.py",  # Requires async/await
    "generator_protocol.py",  # Requires send()/throw() methods
}


def get_test_programs() -> list[str]:
    """Get list of test program names."""
    if not PROGRAMS_DIR.exists():
        return []
    return sorted([
        p.name for p in PROGRAMS_DIR.glob("*.py") if not p.name.startswith("_")
    ])


# Generate test parameters
test_programs = get_test_programs()


class TestCompilation:
    """Test that programs compile to WAT without errors.

    This is the first stage - just checking that the compiler doesn't crash.
    Programs that use unimplemented features will xfail here.
    """

    @pytest.mark.parametrize("program", test_programs)
    def test_program_compiles(self, program: str) -> None:
        """Test that program compiles to WAT."""
        if program in OUT_OF_SCOPE:
            pytest.skip(f"Out of scope: {program}")

        program_path = PROGRAMS_DIR / program
        source = program_path.read_text()

        try:
            wat = compile_to_wat(source)
            assert "(module" in wat, "WAT should contain module"
        except (NotImplementedError, NameError, RecursionError) as e:
            if program in WORKING_PROGRAMS:
                pytest.fail(f"WORKING program failed to compile: {e}")
            pytest.xfail(f"Compilation not implemented: {e}")
        except Exception as e:
            if program in WORKING_PROGRAMS:
                pytest.fail(f"WORKING program failed to compile: {e}")
            pytest.xfail(f"Compilation failed: {e}")


@pytest.mark.skipif(
    not has_wasm_tools(),
    reason="wasm-tools not available",
)
class TestWatValidity:
    """Test that generated WAT is valid (accepted by wasm-tools).

    This is the second stage - checking that the WAT can be converted to WASM.
    """

    @pytest.mark.parametrize("program", test_programs)
    def test_wat_is_valid(self, program: str) -> None:
        """Test that generated WAT is valid."""
        if program in OUT_OF_SCOPE:
            pytest.skip(f"Out of scope: {program}")

        program_path = PROGRAMS_DIR / program
        source = program_path.read_text()

        # First compile
        try:
            wat = compile_to_wat(source)
        except Exception as e:
            pytest.skip(f"Compilation failed: {e}")
            return

        # Then validate WAT
        try:
            wasm = wat_to_wasm(wat)
            assert len(wasm) > 0, "WASM should not be empty"
        except subprocess.CalledProcessError as e:
            if program in WORKING_PROGRAMS:
                pytest.fail(f"WORKING program produced invalid WAT: {e.stderr}")
            pytest.xfail(f"Invalid WAT: {e.stderr[:200]}")


@pytest.mark.skipif(
    not has_wasm_tools() or not has_node_with_wasm_gc(),
    reason="wasm-tools or Node.js 22+ not available",
)
class TestProgramExecution:
    """Test that programs execute correctly and match CPython output.

    This is the main test class. It actually runs each program through:
    1. p2w compiler (Python -> WAT)
    2. wasm-tools (WAT -> WASM)
    3. Node.js (execute WASM)

    And compares the output to running the same program with CPython.
    """

    @pytest.mark.parametrize("program", test_programs)
    def test_program_output_matches_cpython(self, program: str) -> None:
        """Test that program output matches CPython."""
        if program in OUT_OF_SCOPE:
            pytest.skip(f"Out of scope: {program}")

        program_path = PROGRAMS_DIR / program
        source = program_path.read_text()

        # Get expected output from CPython
        try:
            python_output = run_python(source)
        except subprocess.CalledProcessError as e:
            pytest.skip(f"CPython failed: {e.stderr}")
            return

        # Try to compile with p2w
        try:
            wat = compile_to_wat(source)
        except (NotImplementedError, NameError, RecursionError) as e:
            if program in WORKING_PROGRAMS:
                pytest.fail(f"WORKING program failed to compile: {e}")
            pytest.xfail(f"Compilation not implemented: {e}")
            return
        except Exception as e:
            if program in WORKING_PROGRAMS:
                pytest.fail(f"WORKING program failed to compile: {e}")
            pytest.xfail(f"Compilation failed: {e}")
            return

        # Try to convert WAT to WASM
        try:
            wat_to_wasm(wat)
        except subprocess.CalledProcessError as e:
            if program in WORKING_PROGRAMS:
                pytest.fail(f"WORKING program produced invalid WAT: {e.stderr}")
            pytest.xfail(f"Invalid WAT: {e.stderr[:200]}")
            return

        # Try to execute WASM
        try:
            p2w_output = run_wat(wat)
        except subprocess.CalledProcessError as e:
            if program in WORKING_PROGRAMS:
                pytest.fail(f"WORKING program failed to execute: {e.stderr}")
            pytest.xfail(f"Execution failed: {e.stderr[:200]}")
            return

        # Compare outputs
        if p2w_output != python_output:
            msg = (
                f"Output mismatch:\n"
                f"  CPython: {python_output!r}\n"
                f"  p2w:   {p2w_output!r}"
            )
            if program in WORKING_PROGRAMS:
                pytest.fail(f"WORKING program output mismatch: {msg}")
            pytest.xfail(msg)
            return

        # If we get here for a non-WORKING program, it unexpectedly passed!
        if program not in WORKING_PROGRAMS:
            # This is actually good - the test passes, and we should add it to WORKING_PROGRAMS
            pass  # Test passes - consider adding to WORKING_PROGRAMS


class TestWorkingPrograms:
    """Explicit tests for programs that MUST work.

    These tests fail (not xfail) if a WORKING program doesn't work.
    """

    @pytest.mark.skipif(
        not has_wasm_tools() or not has_node_with_wasm_gc(),
        reason="wasm-tools or Node.js 22+ not available",
    )
    @pytest.mark.parametrize("program", sorted(WORKING_PROGRAMS))
    def test_working_program(self, program: str) -> None:
        """Test that a WORKING program produces correct output."""
        program_path = PROGRAMS_DIR / program
        if not program_path.exists():
            pytest.fail(f"WORKING program not found: {program}")

        source = program_path.read_text()

        # Must succeed - no xfail allowed
        python_output = run_python(source)
        wat = compile_to_wat(source)
        p2w_output = run_wat(wat)

        assert p2w_output == python_output, (
            f"Output mismatch for WORKING program {program}:\n"
            f"  CPython: {python_output!r}\n"
            f"  p2w:   {p2w_output!r}"
        )
