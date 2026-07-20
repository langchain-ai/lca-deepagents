# python/m2/m2.3_homework.py
"""M2.3 Homework: Run Your Own Task in a Sandbox.

THE IDEA
Lab 1 wired up a sandboxed coding assistant for one fixed task: writing
and running a Fibonacci script. This homework asks you to pick your own
PAIR of tasks for the SAME sandbox to run, one after another, so you can
see that the sandbox's filesystem sticks around between invoke() calls
instead of resetting each time. There's no single right task here, that's
the point. Two students doing this homework could end up with completely
different scripts.

WHAT YOU FILL IN
  TODO 1: write a system prompt describing the kind of coding assistant
    you want (a persona, a set of working rules, whatever you like), the
    same way the lab's system prompt told the agent to write a file
    before executing it.
  TODO 2: write TWO task messages for the same agent/sandbox. TASK_ONE
    should have the agent write and run code that saves a file. TASK_TWO
    must depend on that file already being there (read it, extend it,
    reuse a value from it) WITHOUT recreating it, so TASK_TWO only
    succeeds if the sandbox actually kept TASK_ONE's state around.

RUN
  cd python
  uv run ./m2/m2.3_homework.py
"""

from uuid import uuid4

from deepagents import create_deep_agent
from deepagents.backends.langsmith import LangSmithSandbox
from langsmith.sandbox import SandboxClient

from models import model

client = SandboxClient()
ls_sandbox = client.create_sandbox(name=f"lca-deepagents-homework-{uuid4().hex[:8]}")
print(f"Sandbox: {ls_sandbox.name}  (id: {ls_sandbox.id})")
backend = LangSmithSandbox(sandbox=ls_sandbox)


# ════════════════════════════════════════════════════════════════════════
# TODO 1: Write a system prompt for your sandboxed agent.
#
# Give it a persona or a set of working rules, whatever you like, as long
# as it tells the agent to write code to a file before running it (the
# same pattern the lab used).
# ════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = None  # TODO 1: replace with your own system prompt


# ════════════════════════════════════════════════════════════════════════
# TODO 2: Write two tasks that share the sandbox's state.
#
# TASK_ONE: any code you want the agent to write, save to a file, and run.
# TASK_TWO: a SEPARATE request, sent afterward to the same agent, that
#   only makes sense if TASK_ONE's file is still there (e.g. "read the
#   file you just made and compute the average of the numbers in it"
#   rather than "make a new list of numbers and average those"). Don't
#   have TASK_TWO regenerate the data itself, that would work even
#   without a persistent sandbox and wouldn't prove anything.
# ════════════════════════════════════════════════════════════════════════

TASK_ONE = None  # TODO 2: replace with your first task message
TASK_TWO = None  # TODO 2: replace with a second task that reuses TASK_ONE's file

if SYSTEM_PROMPT is None:
    raise NotImplementedError("TODO 1: see the comment block above")
if TASK_ONE is None or TASK_TWO is None:
    raise NotImplementedError("TODO 2: see the comment block above")

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
finally:
    client.delete_sandbox(ls_sandbox.name)
