# python/m5/homework/call_agent_api.py
"""M5.2 Homework, part 2: Talk to Your Deployed Agent Over the Agent
Server API.

THE IDEA
So far you've only ever reached your deployed agent through Studio's chat
panel. This script reaches it the way any other client would: over the
same Agent Server API this lesson covers (Threads, Runs), using the
LangGraph SDK instead of a browser. The harness below creates a thread
and starts a run for you; you just supply the question to ask.

BEFORE YOU RUN THIS
  In one terminal, leave this running:
    cd python/m5/homework
    uv run langgraph dev
  Then, in a second terminal:
    cd python
    uv run ./m5/homework/call_agent_api.py

WHAT YOU FILL IN
  TODO 3: write a QUESTION that should make your agent (from agent.py)
    call the tool you wrote for TODO 1.
"""

import asyncio

from langgraph_sdk import get_client

API_URL = "http://127.0.0.1:2024"
ASSISTANT_ID = "agent"  # matches the "agent" key in langgraph.json's "graphs"

# TODO 3: replace this with a question that should trigger your tool.
QUESTION = "TODO 3: replace this with a question for your deployed agent."


def _last_ai_text(messages: list) -> str:
    for msg in reversed(messages):
        if msg.get("type") == "ai":
            return msg.get("content", "")
    return ""


async def main() -> None:
    client = get_client(url=API_URL)

    # Create a thread over the API -- the same POST /threads endpoint the
    # lesson's "Threads" section describes.
    thread = await client.threads.create()
    print(f"Created thread {thread['thread_id']} via POST /threads")

    # Start a run and wait for it to finish -- POST /threads/{id}/runs/wait.
    result = await client.runs.wait(
        thread["thread_id"],
        ASSISTANT_ID,
        input={"messages": [{"role": "user", "content": QUESTION}]},
    )
    print("\n--- Agent response (received over HTTP, not agent.invoke()) ---")
    print(_last_ai_text(result["messages"]))


if QUESTION.startswith("TODO 3"):
    raise NotImplementedError("TODO 3: see the comment block above")

asyncio.run(main())
