# python/m5/sales_assistant/test_diagnostic.py
"""Layered diagnostic tests for the Chinook Sales Assistant.

Runs all capability layers in order and prints a summary. Start both
services first, then run this in a second terminal:

    ./start.sh                                    # terminal 1
    uv run python test_diagnostic.py              # terminal 2 (no-sandbox)
    uv run python test_diagnostic.py --sandbox    # terminal 2 (sandbox)
"""

from __future__ import annotations

import argparse
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


OUTPUTS_DIR = Path(__file__).parent / "outputs"

_sandbox_available: bool = False
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
        from agent_no_sandbox import MAIL_SERVER
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



async def test_retrieve_output_chart(client) -> Result:
    label = "retrieve_output — sales chart from Chinook DB lands in outputs/"
    print(f"  Running: {label}...", end=" ", flush=True)
    if not _sandbox_available:
        print("skipped")
        return Result(label, "SKIP", note="running agent does not expose retrieve_output")
    for f in OUTPUTS_DIR.glob("diag_genre_revenue_*.png"):
        f.unlink()
    try:
        thread = await client.threads.create()
        _, messages = await _ask_in_thread(
            client, thread["thread_id"],
            "Query the Chinook database for total revenue by genre (top 5 genres). "
            "Generate a bar chart, save it to /retrieve/diag_genre_revenue.png, "
            "then call retrieve_output to copy it locally.",
        )
        tool_outs = _tool_outputs(messages, "retrieve_output")
        matches = sorted(OUTPUTS_DIR.glob("diag_genre_revenue_*.png"))
        target = matches[-1] if matches else None
        passed = bool(target) and bool(tool_outs)
        detail = (f"{target.stat().st_size:,} bytes" if target
                  else f"file missing; retrieve_output returned: {tool_outs}")
        print("done")
        return Result(label, "PASS" if passed else "FAIL", detail)
    except Exception as exc:
        print("done")
        return Result(label, "FAIL", str(exc))


async def test_retrieve_output_reuse(client) -> Result:
    label = "retrieve_output — second chart in same thread (sandbox reuse)"
    print(f"  Running: {label}...", end=" ", flush=True)
    if not _sandbox_available:
        print("skipped")
        return Result(label, "SKIP", note="running agent does not expose retrieve_output")
    for f in OUTPUTS_DIR.glob("diag_country_sales_*.png"):
        f.unlink()
    try:
        thread = await client.threads.create()
        await _ask_in_thread(
            client, thread["thread_id"],
            "Query the Chinook database for total revenue by genre (top 5). "
            "Generate a bar chart, save it to /retrieve/diag_reuse_first.png, "
            "then call retrieve_output.",
        )
        _, messages = await _ask_in_thread(
            client, thread["thread_id"],
            "Now generate a bar chart of total sales by country for the top 5 countries. "
            "Save it to /retrieve/diag_country_sales.png then call retrieve_output.",
        )
        tool_outs = _tool_outputs(messages, "retrieve_output")
        matches = sorted(OUTPUTS_DIR.glob("diag_country_sales_*.png"))
        target = matches[-1] if matches else None
        passed = bool(target) and bool(tool_outs)
        detail = (f"{target.stat().st_size:,} bytes" if target
                  else f"file missing; retrieve_output returned: {tool_outs}")
        print("done")
        return Result(label, "PASS" if passed else "FAIL", detail)
    except Exception as exc:
        print("done")
        return Result(label, "FAIL", str(exc))


async def test_retrieve_output_missing(client) -> Result:
    label = "retrieve_output — missing file returns clean error string"
    print(f"  Running: {label}...", end=" ", flush=True)
    if not _sandbox_available:
        print("skipped")
        return Result(label, "SKIP", note="running agent does not expose retrieve_output")
    try:
        thread = await client.threads.create()
        _, messages = await _ask_in_thread(
            client, thread["thread_id"],
            "Call retrieve_output with sandbox_path='/retrieve/does_not_exist.png' "
            "and tell me exactly what it returned.",
        )
        tool_outs = _tool_outputs(messages, "retrieve_output")
        last = tool_outs[-1] if tool_outs else ""
        passed = bool(tool_outs) and any(
            kw in last.lower() for kw in ("error", "not_found", "file_not_found")
        )
        detail = repr(last[:80]) if last else "retrieve_output was not called"
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
    test_retrieve_output_chart,
    test_retrieve_output_reuse,
    test_retrieve_output_missing,
]


async def main() -> None:
    global _sandbox_available
    parser = argparse.ArgumentParser()
    parser.add_argument("--sandbox", action="store_true",
                        help="Enable sandbox tests (requires sandbox server)")
    args = parser.parse_args()
    _sandbox_available = args.sandbox

    client = get_client(url=API_URL)

    print(f"\nChinook Sales Assistant — Diagnostic\n{'─' * 42}")
    mode = "sandbox" if _sandbox_available else "no-sandbox"
    print(f"  Mode: {mode}\n")

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
