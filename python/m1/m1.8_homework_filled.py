# python/m1/m1.8_homework_filled.py
"""Reference copy of m1.8_homework.py with TODOs 1 and 2 filled in so you
can run it end to end and see what "done" looks like. This is just one
possible answer, so yours might be different. Explore!"""

import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

from deepagents import create_deep_agent
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from models import model


# TODO 1 filled in
@tool
def post_tweet(content: str) -> str:
    """Post a tweet with the given content."""
    return f"Tweet posted: {content!r}"


# TODO 2 filled in
SYSTEM_PROMPT = """You are a social media assistant that drafts and posts tweets.

Rules:
- Use post_tweet when the user asks you to post something.
- Keep tweets under 280 characters and upbeat in tone.
- Do not claim a tweet was posted until the tool result confirms it.
"""
INITIAL_REQUEST = "Post a tweet announcing that our new product launches this Friday."
INTERRUPT_ON = {"post_tweet": {"allowed_decisions": ["approve", "edit", "reject"]}}

agent = create_deep_agent(
    model=model,
    tools=[post_tweet],
    system_prompt=SYSTEM_PROMPT,
    interrupt_on=INTERRUPT_ON,
    checkpointer=MemorySaver(),
)

config = {"configurable": {"thread_id": "m1-8-homework-demo"}}

result = agent.invoke(
    {"messages": [{"role": "user", "content": INITIAL_REQUEST}]},
    config=config,
    version="v2",
)

while result.interrupts:
    pending = result.interrupts[0].value
    decisions = []
    for req in pending["action_requests"]:
        print(f"\nApproval required for {req['name']}:")
        print(req["args"])

        choice = input("\nApprove, edit, or reject? (approve/edit/reject): ").strip().lower()
        if choice in ("approve", "yes", "y"):
            decisions.append({"type": "approve"})
        elif choice in ("edit", "e"):
            edited_args = dict(req["args"])
            edited_args["content"] = input("New tweet content: ")
            decisions.append(
                {
                    "type": "edit",
                    "edited_action": {"name": req["name"], "args": edited_args},
                }
            )
        else:
            decisions.append(
                {"type": "reject", "message": "User rejected this tweet draft."}
            )

    result = agent.invoke(Command(resume={"decisions": decisions}), config=config, version="v2")

for msg in result.value["messages"]:
    if hasattr(msg, "name") and msg.name == "post_tweet":
        print(msg.content)
        break
