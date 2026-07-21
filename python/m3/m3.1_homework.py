# python/m3/m3.1_homework.py
"""M3.1 Homework: Trigger Chained Summarization.

THE IDEA
In the lesson, you watched SummarizationMiddleware compress a demo
conversation ONCE, past the 85% threshold. But summarization doesn't just
fire once and stop: on a long enough conversation it fires again, and again
each time it re-summarizes the previous summary plus whatever's new since,
while the FULL evicted history keeps piling up in a single backend file at
/conversation_history/{thread_id}.md. 

This homework asks you to build a conversation on a topic you pick that's 
long enough to trigger summarization AT LEAST TWICE, then confirm two things: 
the model can still recall a detail from your very first turn (after being 
compacted multiple times), and the conversation history file on the backend 
actually accumulated multiple "Summarized at ..." sections 
instead of losing earlier ones.

WHAT YOU FILL IN
  TODO 1: write your own list of user turns (at least 8) about a topic YOU
    pick. Put an important detail in one of your first two turns, then keep
    talking about the topic for several more turns, and end with a turn
    that asks the agent to recall that early detail.
  TODO 2: choose model.profile["max_input_tokens"] so summarization fires
    at least twice before your last turn, not just once. Tune it by trial
    and error, same as the lesson did with 700.

RUN
  cd python
  uv run ./m3/m3.1_homework.py
"""

import asyncio

from deepagents import create_deep_agent
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver

from models import model


# ════════════════════════════════════════════════════════════════════════
# TODO 1: Write your own multi-turn scenario.
#
# Requirements:
#   - At least 8 user turns, all about ONE topic of your choosing.
#   - One of your first two turns should state a concrete detail (a number,
#     a name, a decision).
#   - Your last turn should ask the agent to recall that detail, after
#     several more turns of unrelated follow-up on the same topic.
#
# Example shape (delete this and write your own):
#   return [
#       "I'm planning a two-week trip to ...",
#       "My total budget is ...",
#       ...,
#       ...,
#       ...,
#       "Quick recap: what was my total budget?",
#   ]
# ════════════════════════════════════════════════════════════════════════

def build_turns() -> list[str]:
    """TODO 1: return your own list of user turns (at least 8)."""
    raise NotImplementedError("TODO 1: see the comment block above")


# ════════════════════════════════════════════════════════════════════════
# TODO 2: Choose the summarization threshold.
#
# Lower model.profile["max_input_tokens"] to a value that makes
# SummarizationMiddleware fire (at 85% of that number) AT LEAST TWICE
# across your conversation from TODO 1, not just once. The lesson used 700
# for a 5-turn demo that fired once; your number depends on how many turns
# you wrote and how long they are.
# ════════════════════════════════════════════════════════════════════════

MAX_INPUT_TOKENS = None  # TODO 2: replace None with your chosen integer threshold

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
