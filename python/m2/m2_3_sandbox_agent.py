import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from models import model
from deepagents import create_deep_agent
from deepagents.backends.langsmith import LangSmithSandbox
from langsmith.sandbox import SandboxClient

client = SandboxClient()
ls_sandbox = client.create_sandbox(name="lca-deepagents-lab")
print(f"Sandbox: {ls_sandbox.name}  (id: {ls_sandbox.id})")
backend = LangSmithSandbox(sandbox=ls_sandbox)

agent = create_deep_agent(
    model=model,
    backend=backend,
    system_prompt=(
        "You are a coding assistant. When asked to run code, write the script "
        "to a file first, then execute it. Show the output in your final answer."
    ),
)

try:
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Write a Python script that prints the first 15 Fibonacci numbers, "
                        "save it to fib.py, and run it."
                    ),
                }
            ]
        }
    )
    print(result["messages"][-1].content)
finally:
    client.delete_sandbox(ls_sandbox.name)
