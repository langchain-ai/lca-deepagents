# python/m2/m2.3_homework_filled.py
"""Reference copy of m2.3_homework.py with TODOs 1 and 2 filled in so you
can run it end to end and see what "done" looks like. This is just one
possible answer, so yours might be different. Explore!"""

from uuid import uuid4

from deepagents import create_deep_agent
from deepagents.backends.langsmith import LangSmithSandbox
from langsmith.sandbox import SandboxClient

from models import model

client = SandboxClient()
ls_sandbox = client.create_sandbox(name=f"lca-deepagents-homework-{uuid4().hex[:8]}")
print(f"Sandbox: {ls_sandbox.name}  (id: {ls_sandbox.id})")
backend = LangSmithSandbox(sandbox=ls_sandbox)

# TODO 1 filled in
SYSTEM_PROMPT = (
    "You are a curious lab assistant who loves quick experiments. When "
    "asked to run code, write the script to a file first, then execute "
    "it, and explain what the result means in plain language."
)

# TODO 2 filled in
TASK = (
    "Write a Python script that simulates rolling two six-sided dice "
    "10,000 times, save it to dice_sim.py, and run it. Report the "
    "distribution of sums from 2 to 12 and which sum came up most often."
)

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
