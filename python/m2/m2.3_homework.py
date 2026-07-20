# python/m2/m2.3_homework.py
"""M2.3 Homework: Run Your Own Task in a Sandbox.

THE IDEA
Lab 1 wired up a sandboxed coding assistant for one fixed task: writing
and running a Fibonacci script. This homework asks you to pick your own
small task for the sandbox to run: any code or shell command you want the
agent to write, save, and execute safely inside the LangSmith sandbox
instead of on your machine. There's no single right task here, that's the
point. Two students doing this homework could end up with completely
different scripts.

WHAT YOU FILL IN
  TODO 1: write a system prompt describing the kind of coding assistant
    you want (a persona, a set of working rules, whatever you like), the
    same way the lab's system prompt told the agent to write a file
    before executing it.
  TODO 2: write the user message describing YOUR task: any code or shell
    command you want the agent to write, save, and run inside the
    sandbox.

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
# TODO 2: Write your own task.
#
# Pick any code or shell command you want the agent to write, save to a
# file, and execute inside the sandbox. It can be Python, a shell
# one-liner, anything the sandbox can run.
# ════════════════════════════════════════════════════════════════════════

TASK = None  # TODO 2: replace with your own task message

if SYSTEM_PROMPT is None:
    raise NotImplementedError("TODO 1: see the comment block above")
if TASK is None:
    raise NotImplementedError("TODO 2: see the comment block above")

agent = create_deep_agent(
    model=model,
    backend=backend,
    system_prompt=SYSTEM_PROMPT,
)

try:
    result = agent.invoke({"messages": [{"role": "user", "content": TASK}]})
    print(result["messages"][-1].content)
finally:
    client.delete_sandbox(ls_sandbox.name)
