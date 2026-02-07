"""Tests for browser demos using simulated JS environment."""

from __future__ import annotations

from p2w.browser_runner import compile_and_run_browser


class TestBrowserBasics:
    """Test basic browser functionality."""

    def test_console_log(self):
        """Test js.console.log works."""
        source = """
import js
js.console.log("Hello from WASM!")
"""
        result = compile_and_run_browser(source)
        assert result["success"], f"Failed: {result.get('error')}"
        assert any(
            log.get("type") == "console.log" and "Hello" in log.get("msg", "")
            for log in result.get("jsLogs", [])
        )

    def test_get_element_by_id(self):
        """Test document.getElementById works."""
        source = """
import js
el = js.document.getElementById("test")
js.console.log("got element")
"""
        result = compile_and_run_browser(source)
        assert result["success"], f"Failed: {result.get('error')}"
        assert any(
            log.get("type") == "getElementById" for log in result.get("jsLogs", [])
        )

    def test_create_element(self):
        """Test document.createElement works."""
        source = """
import js
el = js.document.createElement("div")
js.console.log("created element")
"""
        result = compile_and_run_browser(source)
        assert result["success"], f"Failed: {result.get('error')}"
        assert any(
            log.get("type") == "createElement" and log.get("tag") == "div"
            for log in result.get("jsLogs", [])
        )


class TestCanvasBasics:
    """Test Canvas 2D functionality."""

    def test_get_context(self):
        """Test canvas.getContext works."""
        source = """
import js
canvas = js.document.getElementById("canvas")
ctx = canvas.getContext("2d")
js.console.log("got context")
"""
        result = compile_and_run_browser(source)
        assert result["success"], f"Failed: {result.get('error')}"
        assert any(
            log.get("type") == "getContext" and log.get("contextType") == "2d"
            for log in result.get("jsLogs", [])
        )

    def test_fill_rect(self):
        """Test ctx.fillRect works."""
        source = """
import js
canvas = js.document.getElementById("canvas")
ctx = canvas.getContext("2d")
ctx.fillRect(0, 0, 100, 100)
js.console.log("done")
"""
        result = compile_and_run_browser(source)
        assert result["success"], f"Failed: {result.get('error')}"
        assert any(log.get("type") == "fillRect" for log in result.get("jsLogs", []))

    def test_fill_style(self):
        """Test ctx.fillStyle property assignment."""
        source = """
import js
canvas = js.document.getElementById("canvas")
ctx = canvas.getContext("2d")
ctx.fillStyle = "#ff0000"
js.console.log("done")
"""
        result = compile_and_run_browser(source)
        assert result["success"], f"Failed: {result.get('error')}"
        # fillStyle goes through setProperty
        logs = result.get("jsLogs", [])
        has_fill_style = any(
            (log.get("type") == "setFillStyle")
            or (log.get("type") == "setProperty" and log.get("name") == "fillStyle")
            for log in logs
        )
        assert has_fill_style, f"No fillStyle found in logs: {logs}"

    def test_fill_text(self):
        """Test ctx.fillText works."""
        source = """
import js
canvas = js.document.getElementById("canvas")
ctx = canvas.getContext("2d")
ctx.fillText("Hello", 10, 20)
js.console.log("done")
"""
        result = compile_and_run_browser(source)
        assert result["success"], f"Failed: {result.get('error')}"
        assert any(
            log.get("type") == "fillText" and log.get("text") == "Hello"
            for log in result.get("jsLogs", [])
        )


class TestCanvasWithLoops:
    """Test Canvas operations inside loops - this is where issues occur."""

    def test_simple_loop(self):
        """Test simple loop without canvas."""
        source = """
import js
data = [1, 2, 3]
for x in data:
    js.console.log("item")
js.console.log("done")
"""
        result = compile_and_run_browser(source)
        assert result["success"], f"Failed: {result.get('error')}"
        # Should have 4 console.log calls (3 "item" + 1 "done")
        log_count = sum(
            1 for log in result.get("jsLogs", []) if log.get("type") == "console.log"
        )
        assert log_count == 4, f"Expected 4 logs, got {log_count}"

    def test_canvas_in_loop(self):
        """Test canvas operations in loop."""
        source = """
import js
canvas = js.document.getElementById("canvas")
ctx = canvas.getContext("2d")
ctx.fillStyle = "#f5f5f5"
ctx.fillRect(0, 0, 600, 400)

data = [100, 200, 150]
x = 50
for value in data:
    ctx.fillStyle = "#4a90d9"
    ctx.fillRect(x, 200, 60, 100)
    x = x + 80

js.console.log("done")
"""
        result = compile_and_run_browser(source)
        assert result["success"], (
            f"Failed: {result.get('error')}\nLogs: {result.get('jsLogs')}"
        )

    def test_float_division_in_loop(self):
        """Test float division in loop - this is the problematic case."""
        source = """
import js
data = [120, 200, 150]
max_val = 200
for value in data:
    height = (value / max_val) * 300
    js.console.log("calculated")
js.console.log("done")
"""
        result = compile_and_run_browser(source)
        assert result["success"], (
            f"Failed: {result.get('error')}\nLogs: {result.get('jsLogs')}"
        )

    def test_canvas_with_computed_values(self):
        """Test canvas with computed float values - the full problematic case."""
        source = """
import js
canvas = js.document.getElementById("canvas")
ctx = canvas.getContext("2d")

data = [120, 200, 150]
max_val = 200

x = 50
start_y = 350
for value in data:
    bar_height = (value / max_val) * 300
    ctx.fillStyle = "#4a90d9"
    ctx.fillRect(x, start_y - bar_height, 60, bar_height)
    x = x + 80

js.console.log("done")
"""
        result = compile_and_run_browser(source)
        assert result["success"], (
            f"Failed: {result.get('error')}\nLogs: {result.get('jsLogs')}"
        )


class TestDataDashboardDemo:
    """Test the data dashboard demo."""

    def test_minimal_dashboard(self):
        """Test minimal dashboard without loops."""
        source = """
import js

canvas = js.document.getElementById("chart")
ctx = canvas.getContext("2d")

ctx.fillStyle = "#f5f5f5"
ctx.fillRect(0, 0, 600, 400)

ctx.fillStyle = "#4a90d9"
ctx.fillRect(50, 100, 60, 200)

ctx.fillStyle = "#333"
ctx.font = "20px sans-serif"
ctx.fillText("Test Chart", 250, 30)

js.console.log("done")
"""
        result = compile_and_run_browser(source)
        assert result["success"], f"Failed: {result.get('error')}"


class TestSimulationDemo:
    """Test the simulation demo calculations."""

    def test_float_operations(self):
        """Test float operations used in simulation."""
        source = """
import js

prey = 100.0
predators = 20.0
dt = 0.1

prey_birth = 0.1
predation = 0.02

prey_change = (prey_birth * prey - predation * prey * predators) * dt
js.console.log("calculated")
js.console.log(prey_change)
"""
        result = compile_and_run_browser(source)
        assert result["success"], f"Failed: {result.get('error')}"

    def test_list_append_floats(self):
        """Test appending floats to list."""
        source = """
import js

history = []
history.append(100.0)
history.append(95.0)
history.append(90.0)

js.console.log("appended")
js.console.log(len(history))
"""
        result = compile_and_run_browser(source)
        assert result["success"], f"Failed: {result.get('error')}"
