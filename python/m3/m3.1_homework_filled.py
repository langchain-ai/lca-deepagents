# python/m3/m3.1_homework_filled.py
"""Reference copy of m3.1_homework.py with TODOs 1 and 2 filled in so you
can run it end to end and see what "done" looks like. This is just one
possible answer, so yours might be different. Explore!"""

import asyncio

from deepagents import create_deep_agent
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver

from models import model


# TODO 1 filled in
def build_turns() -> list[str]:
    return [
        "I'm planning a vegetable garden for my backyard this spring, about 200 square feet.",
        "The plot gets full sun until roughly 2pm, then partial shade the rest of the day.",
        "I want to grow tomatoes, bell peppers, and some kind of leafy green, plus strawberries along the border.",
        "My soil test came back at pH 6.8 with low nitrogen, so I bought a balanced organic fertilizer.",
        "I'm also thinking about adding a small drip irrigation line instead of hand-watering every day.",
        "Quick recap: what did I say I wanted to plant, and what's the soil situation?",
    ]


# TODO 2 filled in
MAX_INPUT_TOKENS = 700

model.profile = {**model.profile, "max_input_tokens": MAX_INPUT_TOKENS}

agent = create_deep_agent(
    model=model,
    checkpointer=MemorySaver(),
    system_prompt="You are a helpful assistant. Keep every response to one sentence.",
)

THREAD = {"configurable": {"thread_id": "homework"}}


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
    turns = build_turns()
    for i, message in enumerate(turns, 1):
        print(f"\n{'─' * 50}")
        print(f"Turn {i}  User:  {message}")
        response = await turn(message)
        print(f"Turn {i}  Agent: {response}")
        await show_state()


if __name__ == "__main__":
    asyncio.run(main())
