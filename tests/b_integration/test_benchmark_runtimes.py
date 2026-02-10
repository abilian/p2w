"""Integration tests for p2w.benchmark.runtimes module."""

from __future__ import annotations

import pytest

from p2w.benchmark.runtimes import (
    detect_cpython,
    detect_nodejs,
    detect_pypy,
    detect_runtimes,
    run_python,
    run_python_multi,
    run_wasm_nodejs,
)


class TestRuntimeDetection:
    """Tests for runtime detection functions."""

    def test_detect_cpython(self) -> None:
        """Test CPython detection."""
        info = detect_cpython()

        # CPython should be available in test environment
        assert info.name == "cpython"
        assert info.available is True
        assert info.path is not None
        assert len(info.version) > 0
        assert "." in info.version  # Version like "3.12.0"

    def test_detect_pypy(self) -> None:
        """Test PyPy detection."""
        info = detect_pypy()

        assert info.name == "pypy"
        # PyPy might or might not be available
        if info.available:
            assert info.path is not None
            assert len(info.version) > 0
        else:
            assert info.path is None

    def test_detect_nodejs(self) -> None:
        """Test Node.js detection."""
        info = detect_nodejs()

        assert info.name == "nodejs"
        # Node.js should be available in test environment
        assert info.available is True
        assert info.path is not None
        assert len(info.version) > 0

    def test_detect_runtimes(self) -> None:
        """Test detection of all runtimes."""
        runtimes = detect_runtimes()

        assert "cpython" in runtimes
        assert "pypy" in runtimes
        assert "nodejs" in runtimes

        # At minimum, CPython and Node.js should be available
        assert runtimes["cpython"].available is True
        assert runtimes["nodejs"].available is True


class TestPythonExecution:
    """Tests for Python execution functions."""

    def test_run_python_cpython(self) -> None:
        """Test running Python on CPython."""
        source = "print('hello world')"
        output, elapsed = run_python(source, runtime="cpython")

        assert output.strip() == "hello world"
        assert elapsed > 0
        assert elapsed < 10  # Should be fast

    def test_run_python_computation(self) -> None:
        """Test running computational Python code."""
        source = """
result = sum(i * i for i in range(1000))
print(result)
"""
        output, elapsed = run_python(source, runtime="cpython")

        assert output.strip() == "332833500"
        assert elapsed > 0

    @pytest.mark.skipif(
        not detect_pypy().available,
        reason="PyPy not available",
    )
    def test_run_python_pypy(self) -> None:
        """Test running Python on PyPy."""
        source = "print('hello from pypy')"
        output, elapsed = run_python(source, runtime="pypy")

        assert output.strip() == "hello from pypy"
        assert elapsed > 0

    def test_run_python_error(self) -> None:
        """Test handling of Python errors."""
        source = "raise ValueError('test error')"
        output, _ = run_python(source, runtime="cpython")

        assert "[EXIT" in output
        assert "ValueError" in output

    def test_run_python_invalid_runtime(self) -> None:
        """Test error on invalid runtime."""
        with pytest.raises(ValueError, match="not available"):
            run_python("print(1)", runtime="invalid_runtime")

    def test_run_python_multi(self) -> None:
        """Test running Python multiple times."""
        source = "print('test')"
        output, stats = run_python_multi(
            source,
            runtime="cpython",
            warmup=1,
            runs=3,
        )

        assert output.strip() == "test"
        assert len(stats.times) == 3
        assert stats.mean > 0
        assert stats.cv >= 0  # CV can be 0 if perfectly consistent


class TestWasmExecution:
    """Tests for WASM execution via Node.js."""

    @pytest.fixture
    def simple_wasm(self) -> bytes:
        """Create a simple WASM module for testing."""
        from p2w.compiler import compile_to_wat
        from p2w.runner import wat_to_wasm

        source = """
result = 2 + 2
print(result)
"""
        wat_code = compile_to_wat(source)
        return wat_to_wasm(wat_code)

    @pytest.fixture
    def compute_wasm(self) -> bytes:
        """Create a WASM module with computation for timing tests."""
        from p2w.compiler import compile_to_wat
        from p2w.runner import wat_to_wasm

        source = """
def compute():
    total = 0
    for i in range(100):
        total = total + i
    return total

print(compute())
"""
        wat_code = compile_to_wat(source)
        return wat_to_wasm(wat_code)

    @pytest.mark.skipif(
        not detect_nodejs().available,
        reason="Node.js not available",
    )
    def test_run_wasm_nodejs(self, simple_wasm: bytes) -> None:
        """Test running WASM on Node.js."""
        output, stats = run_wasm_nodejs(simple_wasm, warmup=1, runs=3)

        assert output.strip() == "4"
        assert len(stats.times) == 3
        assert stats.mean > 0

    @pytest.mark.skipif(
        not detect_nodejs().available,
        reason="Node.js not available",
    )
    def test_run_wasm_nodejs_timing(self, compute_wasm: bytes) -> None:
        """Test WASM timing consistency."""
        output, stats = run_wasm_nodejs(compute_wasm, warmup=2, runs=5)

        assert output.strip() == "4950"
        assert len(stats.times) == 5
        assert stats.mean > 0
        # After warmup, times should be relatively consistent
        # Allow for some variation in CI environments
        assert stats.cv < 1.0  # Less than 100% variation


class TestRuntimeInfo:
    """Tests for RuntimeInfo dataclass."""

    def test_runtime_info_immutable(self) -> None:
        """Test that RuntimeInfo is immutable."""
        info = detect_cpython()

        with pytest.raises(Exception):  # FrozenInstanceError
            info.name = "other"  # type: ignore[misc]
