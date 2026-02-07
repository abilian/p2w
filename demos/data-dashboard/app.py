"""Data Dashboard Demo - Bar chart visualization."""
import js

# Get canvas and context
canvas = js.document.getElementById("chart")
ctx = canvas.getContext("2d")

# Clear canvas with light gray background
ctx.fillStyle = "#f5f5f5"
ctx.fillRect(0, 0, 600, 400)

# Sample data
data = [120, 200, 150, 80, 180, 90]
labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
max_val = 200

# Chart dimensions
chart_left = 80
chart_bottom = 350
bar_width = 60
bar_gap = 20

# Draw bars
x = chart_left
for value in data:
    # Calculate bar height (proportional to max value)
    bar_height = (value / max_val) * 300

    # Draw bar
    ctx.fillStyle = "#4a90d9"
    ctx.fillRect(x, chart_bottom - bar_height, bar_width, bar_height)

    x = x + bar_width + bar_gap

# Draw title
ctx.fillStyle = "#333"
ctx.font = "24px sans-serif"
ctx.fillText("Monthly Sales", 200, 40)

# Draw Y-axis label
ctx.font = "14px sans-serif"
ctx.fillText("Units", 20, 180)

js.console.log("Dashboard rendered!")
