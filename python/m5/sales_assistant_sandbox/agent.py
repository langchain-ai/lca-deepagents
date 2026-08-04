# python/m5/sales_assistant_sandbox/agent.py
"""Chinook Sales Assistant.

The entire filesystem — skills, memory, and anything the agent writes or
runs — lives inside a per-thread LangSmith sandbox. Skills and AGENTS.md are
seeded into the sandbox once, when it's created, from local disk. There is
no local filesystem route the agent can read from or write to at runtime, so
there is nothing for an untrusted execution result to bridge back to.

Charts have no dedicated tool: the agent writes a Python script with
write_file and runs it with execute (added automatically because the backend
supports sandboxed command execution), the same way it would run any other
generated code.

Start with:
    ./start.sh
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import os
from pathlib import Path

from async_research import build_async_research_middleware
from deepagents import create_deep_agent
from deepagents.backends import StateBackend
from deepagents.backends.langsmith import LangSmithSandbox
from langchain_core.runnables import RunnableConfig
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_quickjs import CodeInterpreterMiddleware
from langgraph_sdk.runtime import ServerRuntime
from subagents import build_subagents
from tools.html import markdown_to_html

from models import strong_model

logger = logging.getLogger(__name__)

HERE = Path(__file__).resolve().parent

SYSTEM_PROMPT = (
    "You are a sales assistant for Jane Peacock, a Sales Support Agent at "
    "Chinook, an online music distributor. Follow your operating manual (loaded "
    "from your memory) and use the matching playbook from /skills/ for each task.\n\n"
    "Your entire filesystem — skills, memory, and anything you write — lives "
    "inside an isolated sandbox; there is no separate local filesystem. To "
    "produce a chart, write a Python script with write_file and run it with "
    "execute (e.g. `pip install matplotlib && python3 <script>`), saving the "
    "image under /outputs/."
)

MAIL_SERVER = {"transport": "streamable-http", "url": "http://127.0.0.1:5002/mcp"}

_enable_search = bool(os.environ.get("TAVILY_API_KEY"))
if not _enable_search:
    logger.info("TAVILY_API_KEY not set — newsletter research subagent disabled.")


def _lookup_or_create(name: str) -> tuple:
    """Return (sandbox, freshly_created) for a thread-scoped sandbox.

    Reuses a ready sandbox, restarts a stopped one, waits out a transitional
    one, or creates a new one — same lookup pattern regardless of outcome, so
    a thread's follow-up turns land in the same sandbox as its first.
    """
    from langsmith.sandbox import SandboxClient

    client = SandboxClient()
    existing = [s for s in client.list_sandboxes() if s.name == name]
    if existing:
        sb = existing[0]
        status = getattr(sb, "status", "ready")
        if status == "ready":
            logger.info("Reusing sandbox %s", name)
            return sb, False
        if status == "stopped":
            logger.info("Restarting stopped sandbox %s", name)
            try:
                return client.start_sandbox(name, timeout=15), False
            except Exception as exc:
                raise RuntimeError(
                    "Sandbox is not available — please try again in a moment."
                ) from exc
        logger.info("Waiting for sandbox %s (status: %s)", name, status)
        try:
            return client.wait_for_sandbox(name, timeout=15), False
        except Exception as exc:
            raise RuntimeError(
                "Sandbox is not available — please try again in a moment."
            ) from exc
    try:
        # idle_ttl_seconds bounds compute cost if a student walks away
        # mid-session; delete_after_stop_seconds bounds it further, since
        # the server default (~14 days) is way more than a classroom needs
        # a stopped sandbox to stick around for.
        sb = client.create_sandbox(
            name=name, idle_ttl_seconds=600, delete_after_stop_seconds=3600
        )
        logger.info("Created sandbox %s", name)
        return sb, True
    except Exception:
        # Another thread created it between our list and our create — look it up
        existing = [s for s in client.list_sandboxes() if s.name == name]
        if existing:
            logger.info("Reusing sandbox %s (race recovery)", name)
            return existing[0], False
        raise


def _seed_skills_and_memory(ls_backend: LangSmithSandbox) -> None:
    """Upload /skills and /AGENTS.md from local disk into a fresh sandbox."""
    files: list[tuple[str, bytes]] = [("/AGENTS.md", (HERE / "AGENTS.md").read_bytes())]
    for path in (HERE / "skills").rglob("*"):
        if path.is_file():
            files.append((f"/skills/{path.relative_to(HERE / 'skills')}", path.read_bytes()))
    results = ls_backend.upload_files(files)
    for (path, _), result in zip(files, results):
        if result.error:
            logger.warning("Failed to seed %s into sandbox: %s", path, result.error)


async def _sandbox_backend_for_thread(thread_id: str) -> LangSmithSandbox:
    """Look up (or create) this thread's sandbox and seed it if it's new."""
    sandbox, freshly_created = await asyncio.to_thread(_lookup_or_create, f"thread-{thread_id}")
    backend = LangSmithSandbox(sandbox)
    if freshly_created:
        await asyncio.to_thread(_seed_skills_and_memory, backend)
    return backend


# Thread-scoped sandbox pattern:
# https://docs.langchain.com/langsmith/graph-rebuild#context-manager-factory
#
# The factory accepts ServerRuntime so the server can signal whether it is
# processing an actual run (execution_runtime is non-None) or handling
# introspection calls (get_schema, get_graph, assistants.read, …). When
# execution_runtime is None we skip sandbox setup and fall back to an
# in-memory backend — same graph topology, no sandbox, no real filesystem
# access at all. Real runs get their own thread-scoped sandbox looked up by
# thread_id.
@contextlib.asynccontextmanager
async def make_graph(config: RunnableConfig, runtime: ServerRuntime):
    if runtime.execution_runtime:
        thread_id = config.get("configurable", {}).get("thread_id")
        backend = await _sandbox_backend_for_thread(thread_id)
    else:
        backend = StateBackend()

    client = MultiServerMCPClient({"mock-mail": MAIL_SERVER})
    mail_tools = await client.get_tools()
    middleware = [CodeInterpreterMiddleware(ptc=["execute", "write_file"])]
    if _enable_search:
        middleware.append(build_async_research_middleware())
    yield create_deep_agent(
        model=strong_model,
        tools=[markdown_to_html] + mail_tools,
        system_prompt=SYSTEM_PROMPT,
        subagents=build_subagents(backend, mail_tools=mail_tools),
        skills=["/skills"],
        memory=["/AGENTS.md"],
        backend=backend,
        middleware=middleware,
        name="chinook-sales-assistant",
    )
