# python/m5/homework_filled/call_agent_api.py
"""Reference copy: talks to the deployed storm-chaser agent over the
Agent Server API instead of Studio's chat panel. This is just one
possible answer, so yours might be different. Explore!"""

import asyncio

from langgraph_sdk import get_client

API_URL = "http://127.0.0.1:2024"
ASSISTANT_ID = "agent"  # matches the "agent" key in langgraph.json's "graphs"

# TODO 3 filled in
QUESTION = "What's the windiest wind speed ever recorded?"


def _last_ai_text(messages: list) -> str:
    for msg in reversed(messages):
        if msg.get("type") == "ai":
            return msg.get("content", "")
    return ""


async def main() -> None:
    client = get_client(url=API_URL)

    thread = await client.threads.create()
    print(f"Created thread {thread['thread_id']} via POST /threads")

    result = await client.runs.wait(
        thread["thread_id"],
        ASSISTANT_ID,
        input={"messages": [{"role": "user", "content": QUESTION}]},
    )
    print("\n--- Agent response (received over HTTP, not agent.invoke()) ---")
    print(_last_ai_text(result["messages"]))


asyncio.run(main())
