# python/m5/sales_assistant/test_diagnostic.py
"""Layered diagnostic tests for the Chinook Sales Assistant.

Runs all capability layers in order and prints a summary. Start both
services first, then run this in a second terminal:

    ./start.sh                          # terminal 1
    uv run python test_diagnostic.py    # terminal 2
"""

from __future__ import annotations

import asyncio
import os
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
    run = await client.runs.create(
        thread_id=thread["thread_id"],
        assistant_id="agent",
        input={"messages": [{"role": "user", "content": prompt}]},
    )
    await client.runs.join(thread["thread_id"], run["run_id"])
    state = await client.threads.get_state(thread["thread_id"])
    messages = state["values"].get("messages", [])
    return _last_ai_text(messages), messages


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
            assistant_id="agent",
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


async def test_chart_sandbox_direct(client) -> Result:
    label = "Chart sandbox — render_chart direct (matplotlib + LangSmith sandbox)"
    print(f"  Running: {label}...", end=" ", flush=True)
    if not os.environ.get("ENABLE_SANDBOX"):
        print("skipped")
        return Result(label, "SKIP", note="set ENABLE_SANDBOX=1 to run this test")
    try:
        import json
        from tools.chart import render_chart

        raw = render_chart.invoke({
            "labels": ["Rock", "Latin", "Metal"],
            "values": [300.0, 137.0, 85.0],
            "title": "Diagnostic Chart",
            "output_filename": "test_diagnostic_chart.png",
        })
        result = json.loads(raw)
        passed = result.get("status") == "saved"
        detail = result.get("path") or result.get("error", raw)
        print("done")
        return Result(label, "PASS" if passed else "FAIL", detail)
    except Exception as exc:
        print("done")
        return Result(label, "FAIL", str(exc))


async def test_chart_sandbox_via_agent(client) -> Result:
    label = "Chart sandbox — render_chart via agent"
    print(f"  Running: {label}...", end=" ", flush=True)
    if not os.environ.get("ENABLE_SANDBOX"):
        print("skipped")
        return Result(label, "SKIP", note="set ENABLE_SANDBOX=1 to run this test")
    try:
        reply, _ = await _ask(
            client,
            "Render a simple bar chart showing: Rock=$300, Latin=$137, Metal=$85. "
            "Save it to /outputs/test_chart.png.",
        )
        reply_lower = reply.lower()
        if any(w in reply_lower for w in ("connection", "unavailable", "unreachable")):
            print("skipped")
            return Result(label, "SKIP",
                          note="LangSmith sandbox unreachable — requires sandbox API access")
        passed = "saved" in reply_lower or "png" in reply_lower or "chart" in reply_lower
        print("done")
        return Result(label, "PASS" if passed else "FAIL",
                      textwrap.shorten(reply, 80))
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
    test_inbox_manager,
    test_hitl_interrupt,
    test_chart_sandbox_direct,
    test_chart_sandbox_via_agent,
]


async def main() -> None:
    client = get_client(url=API_URL)

    print(f"\nChinook Sales Assistant — Diagnostic\n{'─' * 42}")

    results: list[Result] = []
    direct_chart_passed = False

    for test_fn in TESTS:
        # Skip the agent chart test if the direct chart test didn't pass.
        if test_fn is test_chart_sandbox_via_agent and not direct_chart_passed:
            label = "Chart sandbox — render_chart via agent"
            print(f"  Running: {label}... skipped")
            results.append(Result(label, "SKIP",
                                  note="skipped — direct sandbox test did not pass"))
            continue

        result = await test_fn(client)
        if test_fn is test_chart_sandbox_direct and result.status == "PASS":
            direct_chart_passed = True
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
