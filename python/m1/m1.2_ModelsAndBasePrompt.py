"""
python/m1/m1.2_ModelsAndBasePrompt.py

Lab 1: Models & the Base System Prompt.

A Deep Agent always injects its own BASE system prompt (and a filesystem
backend) on every model call, no matter which model you hand it. That
scaffolding comes from the deepagents SDK, not from the model provider, so
swapping the model leaves the BASE prompt and file tools unchanged. (The one
model-specific part is the harness-profile SUFFIX, introduced in Lab 2.)

The model comes from the shared python/models.py. To switch providers, edit
that one file (comment the active line, uncomment another) and re-run; you'll
see the BASE prompt and file tools stay identical.

Run:
    uv run --project python python python/m1/m1.2_ModelsAndBasePrompt.py
"""

import sys
from pathlib import Path

from langchain_core.messages import HumanMessage

from deepagents import create_deep_agent

# BASE_AGENT_PROMPT is the SDK's built-in base prompt, the BASE segment that
# deepagents injects on every call. We import it only to show where it lives.
from deepagents.graph import BASE_AGENT_PROMPT

# The shared model config lives in python/models.py; switch providers there.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from models import model  # noqa: E402


def main() -> None:
    print("The SDK's built-in BASE system prompt (first 300 chars):")
    print(f"  {BASE_AGENT_PROMPT[:300]!r} ...")
    print("\nThis BASE text is injected by deepagents on EVERY call, for EVERY")
    print("model. It comes from the SDK, not from the model provider.\n")

    # No system_prompt, no tools, no filesystem config; nothing but the model.
    # Everything else the agent gets is supplied by the SDK.
    agent = create_deep_agent(model=model)

    result = agent.invoke(
        {"messages": [HumanMessage(content="In one sentence, what can you help me with?")]}
    )
    print(f"Agent: {result['messages'][-1].content}")

    print(f"\n{'─' * 50}")
    print("Now switch the model: open python/models.py, comment out the active")
    print("line, uncomment another (e.g. openai:gpt-4.1-mini), and re-run.")
    print("Then compare the two runs in LangSmith:")
    print("  - Same BASE system prompt (the text above)")
    print("  - Same filesystem tools (ls, read_file, write_file, ...)")
    print("  - The model-specific part is the SUFFIX (harness profile):")
    print("    claude-haiku-4-5 / claude-sonnet-4-6 each ship one; gpt-4.1-mini has none.")


if __name__ == "__main__":
    main()
