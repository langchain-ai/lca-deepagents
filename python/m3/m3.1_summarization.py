"""
python/m3/m3.x_summarization.py

Demonstrates how the built-in SummarizationMiddleware compresses conversation
history when the context window fills up.

By default the trigger is 85% of the model's real context window (200k tokens
for Claude Haiku 4.5), which is impractical to hit in a demo. This example
overrides model.profile["max_input_tokens"] to a small value so summarization
fires after a few turns.

Run:
    cd python && uv run ./m3/m3.x_summarization.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from models import model

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver

from deepagents import create_deep_agent

# Shrink the reported context window so summarization triggers at ~595 tokens
# (85% of 700) instead of the real threshold. Must use model object, not string.
model.profile = {**model.profile, "max_input_tokens": 700}

agent = create_deep_agent(
    model=model,
    checkpointer=MemorySaver(),
    system_prompt="You are a helpful assistant. Keep every response to one sentence.",
)

THREAD = {"configurable": {"thread_id": "demo"}}


async def turn(message: str) -> str:
    result = await agent.ainvoke(
        {"messages": [HumanMessage(content=message)]},
        config=THREAD,
    )
    return result["messages"][-1].content


async def show_state() -> None:
    state = await agent.aget_state(THREAD)
    messages = state.values.get("messages", [])
    event = state.values.get("_summarization_event")
    print(f"  stored : {len(messages)} message(s) (raw history, never trimmed)")
    if event:
        cutoff = event.get("cutoff_index", "?")
        print(f"  model saw : summary + messages[{cutoff}:]  [SUMMARIZED]")


async def main() -> None:
    turns = [
        "My name is Alex. I work at Acme Corp.",
        "What is 2 + 2?",
        "I have been building a distributed cache for three months.",
        "What is the capital of France?",
        "What do you remember about me?",
    ]

    for i, message in enumerate(turns, 1):
        print(f"\n{'─' * 50}")
        print(f"Turn {i}  User:  {message}")
        response = await turn(message)
        print(f"Turn {i}  Agent: {response}")
        await show_state()


if __name__ == "__main__":
    asyncio.run(main())
