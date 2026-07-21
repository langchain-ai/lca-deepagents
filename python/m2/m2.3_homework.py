# python/m2/m2.3_homework.py
"""M2.3 Homework: Prove Persistence in Your Own Sandbox.

THE IDEA
Lab 1 wired up a sandboxed coding assistant for one fixed task: writing
and running a Fibonacci script. This homework asks you to pick your own
PAIR of tasks for the SAME sandbox to run, one after another, so you can
see that the sandbox's filesystem sticks around between invoke() calls
instead of resetting each time. TASK_TWO reads TASK_ONE's saved data and
turns it into a matplotlib chart, which you then read back from the
sandbox the same way Lab 2 reads its chart back.

WHAT YOU FILL IN
  TODO 1: write a system prompt describing the kind of coding assistant
    you want (a persona, a set of working rules, whatever you like), as
    long as it tells the agent to write code to a file before running it
    (the same pattern Lab 1 used) and to use matplotlib for charts.
  TODO 2: write TWO task messages for the same agent/sandbox. TASK_ONE
    should have the agent generate or compute some numeric data and save
    it to a file. TASK_TWO must read that file back (don't regenerate
    the data) and chart it with matplotlib, saving the image to a
    sandbox path you choose and tell the agent explicitly.
  TODO 3: set CHART_PATH to the exact sandbox path you told the agent to
    save the chart to in TASK_TWO, so it can be read back afterward.

RUN
  cd python
  uv run ./m2/m2.3_homework.py
  open m2/homework_chart.png
"""

from pathlib import Path
from uuid import uuid4

from deepagents import create_deep_agent
from deepagents.backends.langsmith import LangSmithSandbox
from langsmith.sandbox import SandboxClient

from models import model

# ════════════════════════════════════════════════════════════════════════
# TODO 1: Write a system prompt for your sandboxed data/charts assistant.
#
# Requirements:
#   - Give it a persona (data analyst, scientist, whatever fits your data).
#   - Tell it to write code to a file before running it (the same pattern
#     Lab 1 used).
#   - Tell it to install any packages it needs with pip before importing
#     them (the same pattern Lab 2 used) - matplotlib is not preinstalled.
#   - Tell it to use matplotlib when asked to build a chart.
#
# Example (delete this and write your own):
#   SYSTEM_PROMPT = (
#       "You are a data visualization assistant. When asked to run code, "
#       "write the script to a file first, then execute it. Install any "
#       "packages you need with pip before importing them. When asked "
#       "for a chart, use matplotlib and save it as a .png file."
#   )
# ════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = None  # TODO 1: replace with your own system prompt


# ════════════════════════════════════════════════════════════════════════
# TODO 2: Write two tasks that share the sandbox's state.
#
# TASK_ONE: have the agent generate or compute some numeric data (made up
#   or calculated) and save it to a file.
# TASK_TWO: a SEPARATE request, sent afterward to the same agent, that
#   reads TASK_ONE's file (without regenerating the data) and uses
#   matplotlib to chart it, saving the image to a path you pick and
#   state explicitly (e.g. "save the chart to /chart.png"), so TODO 3
#   can read it back. Don't have TASK_TWO regenerate the data itself,
#   that would work even without a persistent sandbox and wouldn't prove
#   anything.
#
# Example (delete this and write your own):
#   TASK_ONE = (
#       "Generate 12 months of made-up monthly rainfall totals (in mm) "
#       "for a fictional city, save them to rainfall.json, and print them."
#   )
#   TASK_TWO = (
#       "Read rainfall.json (don't regenerate the numbers) and create a "
#       "bar chart of monthly rainfall. Save it to /chart.png."
#   )
# ════════════════════════════════════════════════════════════════════════

TASK_ONE = None  # TODO 2: replace with your first task message
TASK_TWO = None  # TODO 2: replace with a second task that charts TASK_ONE's file


# ════════════════════════════════════════════════════════════════════════
# TODO 3: Point CHART_PATH at wherever TASK_TWO saves the chart.
#
# This must match the exact sandbox path you told the agent to use in
# TASK_TWO. It's used below to read the chart back from the sandbox and
# save it locally, the same way Lab 2 reads /genre_revenue.png back.
# ════════════════════════════════════════════════════════════════════════

CHART_PATH = None  # TODO 3: replace with the sandbox path used in TASK_TWO

if SYSTEM_PROMPT is None:
    raise NotImplementedError("TODO 1: see the comment block above")
if TASK_ONE is None or TASK_TWO is None:
    raise NotImplementedError("TODO 2: see the comment block above")
if CHART_PATH is None:
    raise NotImplementedError("TODO 3: see the comment block above")

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
