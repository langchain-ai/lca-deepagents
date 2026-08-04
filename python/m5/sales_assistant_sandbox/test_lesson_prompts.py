# python/m5/sales_assistant/test_lesson_prompts.py
"""End-to-end test for the three lesson prompts from m5.3-the-sales-assistant.md.

Run with both services up:
    uv run python test_lesson_prompts.py

Or via start.sh (which launches the mail server + langgraph dev), then in a
second terminal:
    uv run python test_lesson_prompts.py
"""

from __future__ import annotations

import asyncio
import textwrap

from langgraph_sdk import get_client

API_URL = "http://127.0.0.1:2024"

PROMPTS = [
    (
        "Territory report",
        "How's my book of business looking? Give me a territory report.",
    ),
    (
        "Weekly newsletter",
        'Write this week\'s "This Week in Music" newsletter.',
    ),
    (
        "Process RFQ",
        "Check the inbox for any quote requests and process them.",
    ),
]


def _last_ai_text(messages: list) -> str:
    """Return the text of the last AI message."""
    for msg in reversed(messages):
        if msg.get("type") == "ai":
            content = msg.get("content", "")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                parts = [b["text"] for b in content if isinstance(b, dict) and b.get("type") == "text"]
                return "\n".join(parts)
    return "(no AI message found)"


async def run_prompt(client, label: str, prompt: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {label}")
    print(f"{'=' * 60}")
    print(f"Prompt: {prompt}\n")

    # Reset the mail store before the RFQ test so there's a message to process.
    if label == "Process RFQ":
        import subprocess
        subprocess.run(
            ["uv", "run", "python", "mcp/send_to_inbox.py", "--reset"],
            capture_output=True,
        )
        print("(inbox reset)\n")

    thread = await client.threads.create()
    run = await client.runs.create(
        thread_id=thread["thread_id"],
        assistant_id="agent",
        input={"messages": [{"role": "user", "content": prompt}]},
    )

    # Poll until done, handling interrupts (e.g. draft-approval gate).
    interrupt_count = 0
    while True:
        await client.runs.join(thread["thread_id"], run["run_id"])
        state = await client.threads.get_state(thread["thread_id"])

        # state["next"] is non-empty only when the graph is paused at an interrupt.
        interrupted = bool(state.get("next"))

        if not interrupted or interrupt_count >= 3:
            break

        # Auto-approve the interrupt (mirrors a student clicking "Approve").
        interrupt_count += 1
        tasks = state.get("tasks", [])
        interrupt_info = [
            i
            for t in tasks
            for i in (t.get("interrupts") or [])
        ]
        print(f"  [interrupt #{interrupt_count}] auto-approving: "
              f"{str(interrupt_info[0].get('value', ''))[:80] if interrupt_info else '?'}")

        run = await client.runs.create(
            thread_id=thread["thread_id"],
            assistant_id="agent",
            command={"resume": {"decisions": [{"type": "approve"}]}},
        )

    messages = state["values"].get("messages", [])
    reply = _last_ai_text(messages)
    print(textwrap.fill(reply, width=72, subsequent_indent="  ") if reply else "(empty)")
    print(f"\n[{len(messages)} messages total, {interrupt_count} interrupt(s) handled]")


async def main() -> None:
    client = get_client(url=API_URL)

    # Quick health check.
    try:
        await client.assistants.search()
    except Exception as exc:
        print(f"ERROR: langgraph dev not reachable at {API_URL} — {exc}")
        print("Start it first with:  ./start.sh")
        return

    for label, prompt in PROMPTS:
        await run_prompt(client, label, prompt)

    print(f"\n{'=' * 60}")
    print("  All three prompts complete.")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    asyncio.run(main())
