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
TASK_ONE = (
    "Write a Python script that generates 20 random integers between 1 "
    "and 100, saves them to numbers.json, and prints the list."
)
TASK_TWO = (
    "Read numbers.json (don't regenerate the numbers) and write a second "
    "script that loads it and prints the mean and max of those numbers."
)

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
