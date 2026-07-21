# python/m1/m1.8_homework.py
"""M1.8 Homework: Gate Your Own Action Tool.

THE IDEA
Lab 1 gated one action tool, send_email, behind interrupt_on and walked
through approve/edit/reject on it. This homework asks you to do the same
thing for an action tool of your own choosing: post a tweet, book a
meeting room, place an order, delete a file, whatever you like.

WHAT YOU FILL IN
  TODO 1: define your own @tool-decorated action tool. Pick any
    side-effecting action you like; the function body can just return a
    confirmation string, the same way Lab 1's send_email did.
  TODO 2: configure interrupt_on for your tool with an allowed_decisions
    list of your choosing, and write a system prompt plus an initial user
    request that would lead the model to propose calling it.

The review loop below (borrowed from Lab 1, unchanged) prints any
pending tool call and asks you to approve, edit, or reject it. Run the
script more than once, picking a different choice each time, to see both
an approve/edit path and a reject path.

RUN
  cd python
  uv run ./m1/m1.8_homework.py
"""

import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

from deepagents import create_deep_agent
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from models import model


# ════════════════════════════════════════════════════════════════════════
# TODO 1: Define your own action tool.
#
# Requirements:
#   - Keep the @tool decorator.
#   - Give it a real docstring describing the action it performs.
#   - Have it take at least one argument and return a confirmation
#     string, the same way send_email returned a confirmation string
#     instead of actually sending mail.
#
# Example shape (delete this and write your own):
#   @tool
#   def post_tweet(content: str) -> str:
#       """Post a tweet with the given content."""
#       return f"Tweet posted: {content!r}"
# ════════════════════════════════════════════════════════════════════════

@tool
def your_action_tool(argument: str) -> str:
    """TODO 1: replace this docstring and body with your own action tool."""
    raise NotImplementedError("TODO 1: see the comment block above")


# ════════════════════════════════════════════════════════════════════════
# TODO 2: Configure interrupt_on for your tool, and write a system prompt
# plus an initial user request that would lead the model to propose
# calling it.
#
# Requirements:
#   - interrupt_on should name your tool (rename your_action_tool if you
#     like) and an allowed_decisions list, e.g.
#     {"your_action_tool": {"allowed_decisions": ["approve", "edit", "reject"]}}
#   - SYSTEM_PROMPT should tell the agent when to use your tool.
#   - INITIAL_REQUEST should be a user message that would make the agent
#     want to call it.
# ════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = "TODO 2: replace this with your own system prompt."
INITIAL_REQUEST = "TODO 2: replace this with a request that would trigger your tool."
INTERRUPT_ON = {"your_action_tool": True}  # TODO 2: replace with your own allowed_decisions config

if "TODO 1" in your_action_tool.description:
    raise NotImplementedError("TODO 1: see the comment block above")
if "TODO 2" in SYSTEM_PROMPT or "TODO 2" in INITIAL_REQUEST:
    raise NotImplementedError("TODO 2: see the comment block above")

agent = create_deep_agent(
    model=model,
    tools=[your_action_tool],
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
            key = next(iter(edited_args))
            edited_args[key] = input(f"New value for '{key}': ")
            decisions.append(
                {
                    "type": "edit",
                    "edited_action": {"name": req["name"], "args": edited_args},
                }
            )
        else:
            decisions.append(
                {"type": "reject", "message": "User rejected this action."}
            )

    result = agent.invoke(Command(resume={"decisions": decisions}), config=config, version="v2")

for msg in result.value["messages"]:
    if hasattr(msg, "name") and msg.name == "your_action_tool":
        print(msg.content)
        break
