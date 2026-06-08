"""
python/m1/m1.2_SystemPrompt.py

Lab 2: The System Prompt (the USER slot).

The `system_prompt` you pass to create_deep_agent becomes the USER segment.
It is placed at the FRONT of the assembled prompt, before the SDK's BASE
instructions, so your voice/persona takes precedence:

    create_deep_agent assembles:  USER  +  BASE  ( + SUFFIX )
                                   ^ your prompt     ^ harness profile

This script gives the agent a persona and runs one turn; you can hear the USER
segment take effect right in the terminal. Open LangSmith to see your line
sitting at the very front of the system message, ahead of the BASE block.

Swap SYSTEM_PROMPT below for a different persona (cowboy, pirate, ...) and
re-run to hear the voice change.

The model comes from the shared python/models.py; switch providers there.

Run:
    uv run --project python python python/m1/m1.2_SystemPrompt.py
"""

import sys
from pathlib import Path

from langchain_core.messages import HumanMessage

from deepagents import create_deep_agent

# The shared model config lives in python/models.py; switch providers there.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from models import model  # noqa: E402

# This string becomes the USER segment, the very front of the system prompt.
# Try swapping it for a pirate, a 1920s radio announcer, Shakespeare, ...
SYSTEM_PROMPT = "You are a drawling cowboy. Speak only in cowboy slang, partner."


def main() -> None:
    agent = create_deep_agent(model=model, system_prompt=SYSTEM_PROMPT)

    print("USER segment (your system_prompt):")
    print(f"  {SYSTEM_PROMPT!r}\n")

    # Hear the USER segment win: the persona shapes the reply.
    result = agent.invoke(
        {"messages": [HumanMessage(content="Introduce yourself in two sentences.")]}
    )
    print(f"Agent: {result['messages'][-1].content}")

    print(f"\n{'─' * 50}")
    print("Now open LangSmith and look at the assembled system prompt:")
    print("  - Your persona line sits in the USER slot, at the very front")
    print("  - The SDK's BASE behavior prompt follows it")
    print("  - Then the harness-profile SUFFIX (claude-haiku-4-5 ships one)")


if __name__ == "__main__":
    main()
