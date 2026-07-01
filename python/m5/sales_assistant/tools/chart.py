# python/m5/tools/chart.py
"""Optional territory chart rendering, via a LangSmith sandbox.

Chart rendering requires matplotlib, which we ship as a sandbox tool rather
than a local dependency. That way students who don't enable the sandbox still
get a fully working assistant — they just don't get the chart. The territory
report skill produces a complete numbers-only report in that case.

The tool is only registered when ENABLE_SANDBOX is set (see agent.py).
"""

from __future__ import annotations

import json
import uuid
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

    def _run(sandbox, cmd: str) -> None:
        result = sandbox.run(cmd)
        if result.exit_code != 0:
            raise RuntimeError(
                f"Command failed (exit {result.exit_code}): {cmd}\n"
                f"stdout: {result.stdout}\nstderr: {result.stderr}"
            )

    sandbox_name = f"lca-chart-{uuid.uuid4().hex[:8]}"
    client = SandboxClient()
    sandbox = client.create_sandbox(name=sandbox_name)
    try:
        _run(sandbox, "pip3 install matplotlib --break-system-packages")
        sandbox.write("/render_chart.py", script.encode("utf-8"))
        _run(sandbox, "python3 /render_chart.py")
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
