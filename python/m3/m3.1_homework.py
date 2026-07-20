# python/m3/m3.1_homework.py
"""M3.1 Homework: Summarize Your Own Long-Running Conversation.

THE IDEA
The lab watched SummarizationMiddleware compress a short demo conversation
(a name, a math question, a project note, and so on) once the context
window filled past 85%. This homework asks you to do the same thing on a
SCENARIO YOU pick: something with enough substance that talking about it
for several turns would plausibly build up real context (planning a trip,
outlining a story, debugging a project, prepping for an interview, whatever
you're into). There's no single correct topic or turn count here, that's
the point. Two students doing this homework could end up with completely
different conversations and completely different summarization timing.

WHAT YOU FILL IN
  TODO 1: write your own list of user turns (at least 5) about a topic YOU
    pick. Each turn should read like something a real person would type
    across a multi-turn conversation on that topic, with earlier turns
    containing details a later turn asks the agent to recall.
  TODO 2: choose model.profile["max_input_tokens"] so that summarization
    fires partway through your conversation, not on turn 1 and not so late
    it never fires by your last turn. Tune it by trial and error, same as
    the lab did with 700.

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
#   - At least 5 user turns, all about ONE topic of your choosing (not the
#     lab's "new coworker" chit-chat).
#   - The topic should have enough substance that a real conversation about
#     it would build up context over several turns: earlier turns should
#     contain details that a later turn asks the agent to recall.
#
# Example shape (delete this and write your own):
#   return [
#       "I'm planning a two-week trip to ...",
#       "My budget is ...",
#       ...
#       "Quick recap: what did I say my budget was?",
#   ]
# ════════════════════════════════════════════════════════════════════════

def build_turns() -> list[str]:
    """TODO 1: return your own list of user turns (at least 5)."""
    raise NotImplementedError("TODO 1: see the comment block above")


# ════════════════════════════════════════════════════════════════════════
# TODO 2: Choose the summarization threshold.
#
# Lower model.profile["max_input_tokens"] to a value that makes
# SummarizationMiddleware fire (at 85% of that number) somewhere in the
# MIDDLE of your conversation from TODO 1, not immediately and not never.
# The lab used 700 for its 5-turn demo; your number depends on how long
# your own turns are.
# ════════════════════════════════════════════════════════════════════════

MAX_INPUT_TOKENS = None  # TODO 2: replace None with your chosen integer threshold

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
