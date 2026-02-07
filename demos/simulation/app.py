"""Predator-Prey Simulation Demo (p2w/WASM version)

A simplified Lotka-Volterra simulation with static visualization.
"""
import js


def lotka_volterra_step(prey, predators, dt):
    """Perform one step of the Lotka-Volterra equations."""
    # Parameters
    prey_birth = 0.1
    predation = 0.02
    predator_death = 0.1
    conversion = 0.01

    # Calculate changes
    prey_change = (prey_birth * prey - predation * prey * predators) * dt
    predator_change = (conversion * prey * predators - predator_death * predators) * dt

    # Update populations
    new_prey = prey + prey_change
    new_predators = predators + predator_change

    # Ensure non-negative
    if new_prey < 0:
        new_prey = 0
    if new_predators < 0:
        new_predators = 0

    return [new_prey, new_predators]


def run_simulation():
    """Run the simulation and collect data."""
    prey = 100.0
    predators = 20.0
    dt = 0.1
    max_time = 100.0

    prey_history = []
    predator_history = []

    time = 0.0
    while time < max_time:
        prey_history.append(prey)
        predator_history.append(predators)

        result = lotka_volterra_step(prey, predators, dt)
        prey = result[0]
        predators = result[1]
        time = time + dt

    return [prey_history, predator_history]


def draw_chart(canvas, ctx, prey_data, predator_data):
    """Draw the population chart."""
    width = 600
    height = 400
    padding = 50

    # Clear canvas
    ctx.fillStyle = "#1e293b"
    ctx.fillRect(0, 0, width, height)

    # Draw axes
    ctx.strokeStyle = "#64748b"
    ctx.lineWidth = 1
    ctx.beginPath()
    ctx.moveTo(padding, padding)
    ctx.lineTo(padding, height - padding)
    ctx.lineTo(width - padding, height - padding)
    ctx.stroke()

    # Find max population for scaling
    max_pop = 0.0
    for p in prey_data:
        if p > max_pop:
            max_pop = p
    for p in predator_data:
        if p > max_pop:
            max_pop = p

    if max_pop == 0:
        max_pop = 1

    chart_width = width - 2 * padding
    chart_height = height - 2 * padding
    n_points = len(prey_data)
    x_scale = float(chart_width) / float(n_points)
    y_scale = float(chart_height) / max_pop

    # Draw prey line (blue)
    ctx.strokeStyle = "#3b82f6"
    ctx.lineWidth = 2
    ctx.beginPath()
    i = 0
    for p in prey_data:
        x = padding + float(i) * x_scale
        y = height - padding - p * y_scale
        if i == 0:
            ctx.moveTo(x, y)
        else:
            ctx.lineTo(x, y)
        i = i + 1
    ctx.stroke()

    # Draw predator line (red)
    ctx.strokeStyle = "#ef4444"
    ctx.lineWidth = 2
    ctx.beginPath()
    i = 0
    for p in predator_data:
        x = padding + float(i) * x_scale
        y = height - padding - p * y_scale
        if i == 0:
            ctx.moveTo(x, y)
        else:
            ctx.lineTo(x, y)
        i = i + 1
    ctx.stroke()

    # Draw legend
    ctx.font = "14px sans-serif"
    ctx.fillStyle = "#3b82f6"
    ctx.fillRect(width - 120, 20, 15, 15)
    ctx.fillStyle = "#e2e8f0"
    ctx.fillText("Prey", width - 100, 32)

    ctx.fillStyle = "#ef4444"
    ctx.fillRect(width - 120, 45, 15, 15)
    ctx.fillStyle = "#e2e8f0"
    ctx.fillText("Predators", width - 100, 57)

    # Title
    ctx.fillStyle = "#e2e8f0"
    ctx.font = "16px sans-serif"
    ctx.fillText("Predator-Prey Population Dynamics", 150, 25)


def init():
    """Initialize and run the simulation."""
    js.console.log("Simulation starting...")

    # Get canvas
    canvas = js.document.getElementById("sim-canvas")
    ctx = canvas.getContext("2d")

    # Run simulation
    js.console.log("Running Lotka-Volterra simulation...")
    result = run_simulation()
    prey_data = result[0]
    predator_data = result[1]

    js.console.log("Drawing chart...")
    draw_chart(canvas, ctx, prey_data, predator_data)

    js.console.log("Simulation complete!")


# Run
init()
