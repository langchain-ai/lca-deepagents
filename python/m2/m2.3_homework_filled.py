# python/m2/m2.3_homework_filled.py
"""Reference copy of m2.3_homework.py with TODOs 1-3 filled in so you
can run it end to end and see what "done" looks like. This is just one
possible answer, so yours might be different. Explore!"""

from pathlib import Path
from uuid import uuid4

from deepagents import create_deep_agent
from deepagents.backends.langsmith import LangSmithSandbox
from langsmith.sandbox import SandboxClient

from models import model

# TODO 1 filled in
SYSTEM_PROMPT = (
    "You are a data visualization assistant. When asked to run code, "
    "write the script to a file first, then execute it. Install any "
    "packages you need with pip before importing them. When asked for "
    "a chart, use matplotlib and save it as a .png file."
)

# TODO 2 filled in
TASK_ONE = (
    "Generate 12 months of made-up monthly rainfall totals (in mm) for "
    "a fictional city, save them to rainfall.json, and print them."
)
TASK_TWO = (
    "Read rainfall.json (don't regenerate the numbers) and create a bar "
    "chart of monthly rainfall. Save it to /chart.png."
)

# TODO 3 filled in
CHART_PATH = "/chart.png"

client = SandboxClient()
ls_sandbox = client.create_sandbox(name=f"lca-deepagents-homework-{uuid4().hex[:8]}")
print(f"Sandbox: {ls_sandbox.name}  (id: {ls_sandbox.id})")
backend = LangSmithSandbox(sandbox=ls_sandbox)

agent = create_deep_agent(
    model=model,
    backend=backend,
    system_prompt=SYSTEM_PROMPT,
)

try:
    result = agent.invoke({"messages": [{"role": "user", "content": TASK_ONE}]})
    print("--- Task 1 ---")
    print(result["messages"][-1].content)

    result = agent.invoke({"messages": [{"role": "user", "content": TASK_TWO}]})
    print("\n--- Task 2 (same sandbox, should see Task 1's file) ---")
    print(result["messages"][-1].content)

    chart_bytes = ls_sandbox.read(CHART_PATH)
    out_path = Path(__file__).parent / "homework_chart.png"
    out_path.write_bytes(chart_bytes)
    print(f"Chart saved to {out_path}")
finally:
    client.delete_sandbox(ls_sandbox.name)
