# python/m5/sales_assistant/test_diagnostic.py
"""Layered diagnostic tests for the Chinook Sales Assistant.

Runs all capability layers in order and prints a summary. Start both
services first, then run this in a second terminal:

    ./start.sh                          # terminal 1
    uv run python test_diagnostic.py    # terminal 2
"""

from __future__ import annotations

import asyncio
import subprocess
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from langgraph_sdk import get_client

# Load the same .env that langgraph.json points at.
load_dotenv(Path(__file__).parent / "../../.env")

API_URL = "http://127.0.0.1:2024"
Status = Literal["PASS", "FAIL", "SKIP"]


# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------

@dataclass
class Result:
    label: str
    status: Status
    detail: str = ""
    note: str = ""  # shown in summary for SKIP


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _last_ai_text(messages: list) -> str:
    for msg in reversed(messages):
        if msg.get("type") == "ai":
            content = msg.get("content", "")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                return "\n".join(
                    b["text"] for b in content
                    if isinstance(b, dict) and b.get("type") == "text"
                )
    return ""


async def _ask(client, prompt: str) -> tuple[str, list]:
    thread = await client.threads.create()
    _, messages = await _ask_in_thread(client, thread["thread_id"], prompt)
    return _last_ai_text(messages), messages


async def _ask_in_thread(client, thread_id: str, prompt: str) -> tuple[str, list]:
    """Send a follow-up message to an existing thread, printing a dot every 5s."""
    run = await client.runs.create(
        thread_id=thread_id,
        assistant_id=_assistant_id,
        input={"messages": [{"role": "user", "content": prompt}]},
    )
    # Poll manually so we can print progress dots while waiting.
    while True:
        state = await client.runs.get(thread_id, run["run_id"])
        if state["status"] in ("success", "error", "timeout"):
            break
        print(".", end="", flush=True)
        await asyncio.sleep(5)
    state = await client.threads.get_state(thread_id)
    messages = state["values"].get("messages", [])
    return _last_ai_text(messages), messages


def _tool_outputs(messages: list, tool_name: str) -> list[str]:
    return [
        m.get("content", "")
        for m in messages
        if m.get("type") == "tool" and m.get("name") == tool_name
    ]


_assistant_id: str = "agent"

def _reset_inbox() -> None:
    subprocess.run(
        ["uv", "run", "python", "mcp/send_to_inbox.py", "--reset"],
        capture_output=True,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

async def test_server_reachable(client) -> Result:
    label = "LangGraph server — reachable at port 2024"
    print(f"  Running: {label}...", end=" ", flush=True)
    try:
        await client.assistants.search()
        print("done")
        return Result(label, "PASS")
    except Exception as exc:
        print("done")
        return Result(label, "FAIL",
                      f"{exc} — is ./start.sh running?")


async def test_hello(client) -> Result:
    label = "Hello — LLM connectivity"
    print(f"  Running: {label}...", end=" ", flush=True)
    try:
        reply, _ = await _ask(client, "Hello! Just say hi back in one sentence.")
        if reply:
            print("done")
            return Result(label, "PASS", textwrap.shorten(reply, 80))
        print("done")
        return Result(label, "FAIL", "(empty reply)")
    except Exception as exc:
        print("done")
        return Result(label, "FAIL", str(exc))


async def test_agents_md(client) -> Result:
    label = "AGENTS.md — memory file loaded"
    print(f"  Running: {label}...", end=" ", flush=True)
    try:
        reply, _ = await _ask(
            client,
            "Repeat the diagnostic token from your operating manual. "
            "It appears as italic text near the top of the file.",
        )
        passed = "CHINOOK-READY" in reply
        print("done")
        return Result(label, "PASS" if passed else "FAIL",
                      textwrap.shorten(reply, 80))
    except Exception as exc:
        print("done")
        return Result(label, "FAIL", str(exc))


async def test_skills_loaded(client) -> Result:
    label = "skills/ — playbooks readable"
    print(f"  Running: {label}...", end=" ", flush=True)
    try:
        reply, _ = await _ask(
            client,
            "What task playbooks or skills do you have available? List their names.",
        )
        keywords = ["rfq", "quote", "newsletter", "territory"]
        passed = any(kw in reply.lower() for kw in keywords)
        print("done")
        return Result(label, "PASS" if passed else "FAIL",
                      textwrap.shorten(reply, 80))
    except Exception as exc:
        print("done")
        return Result(label, "FAIL", str(exc))


async def test_chinook_analyst(client) -> Result:
    label = "chinook-analyst — database query"
    print(f"  Running: {label}...", end=" ", flush=True)
    try:
        reply, _ = await _ask(client, "How many tracks are in the Chinook database?")
        passed = "3503" in reply or "3,503" in reply
        print("done")
        return Result(label, "PASS" if passed else "FAIL",
                      textwrap.shorten(reply, 80))
    except Exception as exc:
        print("done")
        return Result(label, "FAIL", str(exc))


async def test_code_interpreter(client) -> Result:
    label = "Code interpreter — exact arithmetic"
    print(f"  Running: {label}...", end=" ", flush=True)
    try:
        reply, _ = await _ask(
            client,
            "Use the code interpreter to calculate: 37 tracks at $0.99 each. "
            "What is the exact total?",
        )
        passed = "36.63" in reply
        print("done")
        return Result(label, "PASS" if passed else "FAIL",
                      textwrap.shorten(reply, 80))
    except Exception as exc:
        print("done")
        return Result(label, "FAIL", str(exc))


async def test_mail_tool_names(client) -> Result:
    label = "inbox-manager — MCP tool names discovered correctly"
    print(f"  Running: {label}...", end=" ", flush=True)
    try:
        from agent import MAIL_SERVER
        from langchain_mcp_adapters.client import MultiServerMCPClient

        mcp_client = MultiServerMCPClient({"mock-mail": MAIL_SERVER})
        tools = await mcp_client.get_tools()
        names = {t.name for t in tools}
        expected = {"mail_list_messages", "mail_read_message", "mail_create_draft"}
        missing = expected - names
        passed = not missing
        detail = f"found: {sorted(names)}" if passed else f"missing: {sorted(missing)}"
        print("done")
        return Result(label, "PASS" if passed else "FAIL", detail)
    except Exception as exc:
        print("done")
        return Result(label, "FAIL", str(exc))


async def test_inbox_manager(client) -> Result:
    label = "inbox-manager — mail MCP tool call"
    print(f"  Running: {label}...", end=" ", flush=True)
    _reset_inbox()
    try:
        reply, _ = await _ask(client, "Do I have any messages in my inbox?")
        passed = "morgan" in reply.lower() or "message" in reply.lower()
        print("done")
        return Result(label, "PASS" if passed else "FAIL",
                      textwrap.shorten(reply, 80))
    except Exception as exc:
        print("done")
        return Result(label, "FAIL", str(exc))


async def test_hitl_interrupt(client) -> Result:
    label = "Human-in-the-loop — draft triggers interrupt"
    print(f"  Running: {label}...", end=" ", flush=True)
    try:
        thread = await client.threads.create()
        run = await client.runs.create(
            thread_id=thread["thread_id"],
            assistant_id=_assistant_id,
            input={"messages": [{"role": "user", "content":
                "Draft a reply to the email from Morgan Vale saying we will get "
                "back to them within 24 hours. Save the draft."
            }]},
        )
        await client.runs.join(thread["thread_id"], run["run_id"])
        state = await client.threads.get_state(thread["thread_id"])
        tasks = state.get("tasks", [])
        interrupted = any(t.get("interrupts") for t in tasks if isinstance(t, dict))
        print("done")
        return Result(label, "PASS" if interrupted else "FAIL",
                      "interrupt fired" if interrupted else "run completed without interrupt")
    except Exception as exc:
        print("done")
        return Result(label, "FAIL", str(exc))



async def test_sandbox_chart(client) -> Result:
    label = "sandbox chart — agent writes+runs matplotlib, chart lands in sandbox outputs/"
    print(f"  Running: {label}...", end=" ", flush=True)
    try:
        thread = await client.threads.create()
        _, messages = await _ask_in_thread(
            client, thread["thread_id"],
            "Query the Chinook database for total revenue by genre (top 5 genres). "
            "Write and run a Python script to save a pie chart as "
            "/outputs/diag_genre_revenue.png.",
        )
        tool_outs = _tool_outputs(messages, "execute")
        from langsmith.sandbox import ResourceNotFoundError, SandboxClient

        sandbox_client = SandboxClient()
        sandbox = await asyncio.to_thread(sandbox_client.get_sandbox, f"thread-{thread['thread_id']}")
        try:
            content = await asyncio.to_thread(sandbox.read, "/outputs/diag_genre_revenue.png")
            passed = len(content) > 0
            detail = f"{len(content):,} bytes"
        except ResourceNotFoundError:
            passed = False
            detail = f"file missing in sandbox; execute returned: {tool_outs}"
        print("done")
        return Result(label, "PASS" if passed else "FAIL", detail)
    except Exception as exc:
        print("done")
        return Result(label, "FAIL", str(exc))


async def test_async_genre_research(client) -> Result:
    label = "newsletter-agent (async) — background launch + notifier-driven newsletter save"
    print(f"  Running: {label}...", end=" ", flush=True)
    try:
        thread = await client.threads.create()
        thread_id = thread["thread_id"]

        # Pin to two genres so the test doesn't first need a chinook-analyst
        # lookup, and only fires two real Tavily searches instead of four.
        launch_reply, launch_messages = await _ask_in_thread(
            client, thread_id,
            "Create this week's newsletter for exactly these two genres: "
            "Jazz and Rock. Do not ask chinook-analyst for genres.",
        )

        # The launch turn should fire off exactly one async task (the whole
        # newsletter job) and stop, not block waiting for it — check that via
        # the SDK, not by inference from the message text.
        state = await client.threads.get_state(thread_id)
        tasks = state["values"].get("async_tasks", {})
        launched_non_blocking = len(tasks) == 1
        if not launched_non_blocking:
            print("done")
            return Result(label, "FAIL",
                          f"expected exactly 1 async task after launch turn, got {len(tasks)}: {textwrap.shorten(launch_reply, 80)}")

        # Wait for the completion notifier to wake this thread once the task
        # reaches a terminal status, and for the assembled newsletter to land
        # in the sandbox — polling live server state, not the (necessarily
        # stale) launch-turn snapshot above.
        from langsmith.sandbox import SandboxClient

        sandbox_client = SandboxClient()
        # newsletter-agent itself does several rounds of Tavily search + LLM
        # calls per genre (sequentially, inside its own single run), so this
        # can take a while even for two genres.
        deadline = asyncio.get_event_loop().time() + 900
        newsletter_files: list[str] = []
        while asyncio.get_event_loop().time() < deadline:
            state = await client.threads.get_state(thread_id)
            tasks = state["values"].get("async_tasks", {})
            all_terminal = len(tasks) == 1 and all(t["status"] in ("success", "error", "cancelled") for t in tasks.values())
            if all_terminal:
                sandbox = await asyncio.to_thread(sandbox_client.get_sandbox, f"thread-{thread_id}")
                listing = await asyncio.to_thread(
                    sandbox.run, "find /outputs -maxdepth 1 -type f -name 'newsletter-*.html'"
                )
                newsletter_files = [line for line in listing.stdout.splitlines() if line.strip()]
                if newsletter_files:
                    break
            print(".", end="", flush=True)
            await asyncio.sleep(5)

        passed = bool(newsletter_files)
        statuses = {tid: t["status"] for tid, t in tasks.items()}
        detail = f"newsletter: {newsletter_files}, task statuses: {statuses}" if passed else \
            f"no newsletter after timeout; task statuses: {statuses}"
        print("done")
        return Result(label, "PASS" if passed else "FAIL", detail)
    except Exception as exc:
        print("done")
        return Result(label, "FAIL", str(exc))


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

TESTS = [
    test_server_reachable,
    test_hello,
    test_agents_md,
    test_skills_loaded,
    test_chinook_analyst,
    test_code_interpreter,
    test_mail_tool_names,
    test_inbox_manager,
    test_hitl_interrupt,
    test_sandbox_chart,
    test_async_genre_research,
]


async def main() -> None:
    client = get_client(url=API_URL)

    print(f"\nChinook Sales Assistant — Diagnostic\n{'─' * 42}\n")

    results: list[Result] = []

    for test_fn in TESTS:
        result = await test_fn(client)
        results.append(result)

        # Stop immediately if the server isn't reachable — all other tests will fail too.
        if test_fn is test_server_reachable and result.status == "FAIL":
            print("  (server not reachable — skipping remaining tests)")
            break

    # Summary
    passed = sum(1 for r in results if r.status == "PASS")
    failed = sum(1 for r in results if r.status == "FAIL")
    skipped = sum(1 for r in results if r.status == "SKIP")

    print(f"\n{'─' * 42}")
    print("Summary\n")
    icons = {"PASS": "✓", "FAIL": "✗", "SKIP": "–"}
    for r in results:
        icon = icons[r.status]
        print(f"  {icon}  {r.label}")
        if r.status == "FAIL" and r.detail:
            print(f"       {textwrap.shorten(r.detail, 72)}")
        if r.status == "SKIP" and r.note:
            print(f"       ({r.note})")

    totals = f"{passed} passed"
    if failed:
        totals += f", {failed} failed"
    if skipped:
        totals += f", {skipped} skipped"
    print(f"\n{totals}")
    print(f"{'─' * 42}\n")


if __name__ == "__main__":
    asyncio.run(main())
