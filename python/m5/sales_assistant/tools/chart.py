# python/m5/tools/chart.py
"""Optional territory chart rendering, via a LangSmith sandbox.

This is the course's **optional sandbox** feature. Rendering a PNG needs
matplotlib, which we don't want to force into every student's environment — so
instead of installing it locally, we run a short matplotlib script inside an
ephemeral LangSmith sandbox, read the image back, and save it under /outputs.

The tool is only registered when ENABLE_SANDBOX is set (see agent.py). Without
it, the territory-report skill simply produces a numbers-only report — the
assistant still works, it just doesn't draw a picture.
"""

from __future__ import annotations

import json
from pathlib import Path

from langchain_core.tools import tool

_OUTPUTS = Path(__file__).resolve().parent.parent / "outputs"


@tool
def render_chart(
    labels: list[str],
    values: list[float],
    title: str = "Territory Report",
    output_filename: str = "territory_chart.png",
    chart_type: str = "bar",
) -> str:
    """Render a chart (bar or pie) from labels and values and save it as a PNG.

    Runs matplotlib inside an ephemeral sandbox and writes the resulting image
    to the outputs folder. ``chart_type`` is "bar" or "pie". Returns the saved
    path, or an error the assistant can report and work around.
    """
    if len(labels) != len(values) or not labels:
        return json.dumps({"error": "labels and values must be non-empty and equal length."})

    # Imported lazily so the rest of the assistant doesn't depend on the
    # sandbox SDK being importable.
    try:
        from deepagents.backends.langsmith import LangSmithSandbox  # noqa: F401
        from langsmith.sandbox import SandboxClient
    except Exception as exc:  # pragma: no cover - env dependent
        return json.dumps({"error": f"Sandbox SDK unavailable: {exc}"})

    safe_name = Path(output_filename).name  # no path traversal
    script = _CHART_SCRIPT.format(
        labels=json.dumps(labels),
        values=json.dumps(values),
        title=json.dumps(title),
        chart_type=json.dumps(chart_type),
    )

    client = SandboxClient()
    sandbox = client.create_sandbox(name="lca-territory-chart")
    try:
        sandbox.run("pip install matplotlib -q")
        sandbox.write("/render_chart.py", script.encode("utf-8"))
        sandbox.run("python /render_chart.py")
        png = sandbox.read("/chart.png")
        _OUTPUTS.mkdir(exist_ok=True)
        out_path = _OUTPUTS / safe_name
        out_path.write_bytes(png)
        return json.dumps({"status": "saved", "path": f"/outputs/{safe_name}"})
    except Exception as exc:  # pragma: no cover - env dependent
        return json.dumps({"error": f"Chart rendering failed: {exc}"})
    finally:
        try:
            client.delete_sandbox(sandbox.name)
        except Exception:
            pass


_CHART_SCRIPT = """\
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

labels = json.loads('{labels}')
values = json.loads('{values}')
title = json.loads('{title}')
chart_type = json.loads('{chart_type}')

fig, ax = plt.subplots(figsize=(8, 5))
if chart_type == "pie":
    ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90)
    ax.axis("equal")
else:
    ax.bar(labels, values, color="#006DDD")
    ax.set_ylabel("Value")
    plt.xticks(rotation=30, ha="right")
ax.set_title(title)
plt.tight_layout()
plt.savefig("/chart.png", dpi=120)
"""
