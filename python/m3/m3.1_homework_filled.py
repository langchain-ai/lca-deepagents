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
        "I'm planning a two-week trip to Japan in April, starting in Tokyo.",
        "My total budget is $4,000 including flights.",
        "What is 2 + 2?",
        "I want to see cherry blossoms and visit at least one hot spring town.",
        "What is the capital of Italy?",
        "For the middle week I'm thinking Kyoto and Osaka by train.",
        "What is 12 times 12?",
        "I booked a JR rail pass already for the Tokyo-Kyoto-Osaka leg.",
        "What is the capital of Germany?",
        "Quick recap: what's my total budget, and what's the very first city I said I'd start in?",
    ]


# TODO 2 filled in
MAX_INPUT_TOKENS = 3000

model.profile = {**model.profile, "max_input_tokens": MAX_INPUT_TOKENS}

agent = create_deep_agent(
    model=model,
    checkpointer=MemorySaver(),
    system_prompt="You are a helpful assistant. Keep every response to one sentence.",
)

THREAD = {"configurable": {"thread_id": "homework"}}
HISTORY_PATH = f"/conversation_history/{THREAD['configurable']['thread_id']}.md"


async def turn(message: str) -> str:
    result = await agent.ainvoke(
        {"messages": [HumanMessage(content=message)]},
        config=THREAD,
    )
    return result["messages"][-1].content


async def show_state(seen_cutoffs: set) -> bool:
    """Print state after a turn. Returns True if this turn produced a NEW
    summarization event (as opposed to still living under a previous one)."""
    state = await agent.aget_state(THREAD)
    messages = state.values.get("messages", [])
    event = state.values.get("_summarization_event")
    print(f"  stored : {len(messages)} message(s) (raw history, never trimmed)")
    if not event:
        return False
    cutoff = event.get("cutoff_index", "?")
    is_new_event = cutoff not in seen_cutoffs
    seen_cutoffs.add(cutoff)
    tag = "  <-- NEW EVENT" if is_new_event else ""
    print(f"  model saw : summary + messages[{cutoff}:]  [SUMMARIZED]{tag}")
    return is_new_event


async def main() -> None:
    turns = build_turns()
    seen_cutoffs: set = set()
    event_count = 0
    for i, message in enumerate(turns, 1):
        print(f"\n{'─' * 50}")
        print(f"Turn {i}  User:  {message}")
        response = await turn(message)
        print(f"Turn {i}  Agent: {response}")
        if await show_state(seen_cutoffs):
            event_count += 1

    print(f"\nSummarization fired {event_count} time(s) across {len(turns)} turns.")
    if event_count < 2:
        print(
            "That's fewer than 2. Lower MAX_INPUT_TOKENS, or add more turns/detail, "
            "so it fires again before the conversation ends."
        )

    state = await agent.aget_state(THREAD)
    history_file = state.values.get("files", {}).get(HISTORY_PATH)
    if history_file:
        content = history_file["content"] if isinstance(history_file, dict) else history_file
        sections = content.count("## Summarized at")
        print(f"\n--- {HISTORY_PATH} ({sections} section(s)) ---")
        print(content)


if __name__ == "__main__":
    asyncio.run(main())
