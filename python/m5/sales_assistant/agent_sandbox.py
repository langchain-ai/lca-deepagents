# python/m5/sales_assistant/agent_sandbox.py
"""Chinook Sales Assistant — sandbox variant.

Uses a LangSmith sandbox as the execution backend so the agent can install
and run packages (e.g. matplotlib for charts) natively via code execution.
All filesystem operations (skills, AGENTS.md, working files) stay on local
disk via a CompositeBackend that routes "/" to FilesystemBackend.

Each LangGraph thread gets its own sandbox (thread-scoped), looked up by
name so follow-up messages in the same thread reuse the same environment.
Sandboxes are cleaned up automatically by a 10-minute idle TTL.

Start with:
    ENABLE_SANDBOX=1 ./start.sh
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import os
from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from deepagents.backends.composite import CompositeBackend
from deepagents.backends.langsmith import LangSmithSandbox
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph_sdk.runtime import ServerRuntime
from subagents import build_subagents
from tools.html import markdown_to_html

from models import strong_model

logger = logging.getLogger("chinook-sales-assistant")

HERE = Path(__file__).resolve().parent

SYSTEM_PROMPT = (
    "You are a sales assistant for Jane Peacock, a Sales Support Agent at "
    "Chinook, an online music distributor. Follow your operating manual (loaded "
    "from your memory) and use the matching playbook from /skills/ for each task.\n\n"
    "Code runs in an isolated sandbox container. Files you create there (charts, "
    "reports, exports) are not visible on the local filesystem. To make a file "
    "available to the user, write it to /retrieve/<filename> in the sandbox, then "
    "call retrieve_output to copy it to the local outputs/ directory."
)

MAIL_SERVER = {"transport": "streamable-http", "url": "http://127.0.0.1:5002/mcp"}

_enable_search = bool(os.environ.get("TAVILY_API_KEY"))
if not _enable_search:
    logger.info("TAVILY_API_KEY not set — newsletter research subagent disabled.")

_sandbox_client = None


def _get_client():
    global _sandbox_client
    if _sandbox_client is None:
        from langsmith.sandbox import SandboxClient
        _sandbox_client = SandboxClient()
    return _sandbox_client


def _lookup_or_create(name: str):
    client = _get_client()
    existing = [s for s in client.list_sandboxes() if s.name == name]
    if existing:
        logger.info("Reusing sandbox %s", name)
        return existing[0]
    try:
        sb = client.create_sandbox(name=name, idle_ttl_seconds=600)
        logger.info("Created sandbox %s", name)
        return sb
    except Exception:
        # Another thread created it between our list and our create — look it up
        existing = [s for s in client.list_sandboxes() if s.name == name]
        if existing:
            logger.info("Reusing sandbox %s (race recovery)", name)
            return existing[0]
        raise


# Thread-scoped sandbox pattern:
# https://docs.langchain.com/langsmith/graph-rebuild#context-manager-factory
#
# The factory accepts ServerRuntime so the server can signal whether it is
# processing an actual run (execution_runtime is non-None) or handling
# introspection calls (get_schema, get_graph, assistants.read, …). When
# execution_runtime is None we skip the expensive sandbox setup and fall back
# to local filesystem — same graph topology, no sandbox, no MCP round-trip.
# Real runs get their own thread-scoped sandbox looked up by thread_id.
@contextlib.asynccontextmanager
async def make_graph(config: RunnableConfig, runtime: ServerRuntime):
    ls_backend = None

    if ert := runtime.execution_runtime:
        # Real run — look up or create a thread-scoped sandbox
        thread_id = (config.get("configurable") or {}).get("thread_id")
        sandbox = await asyncio.to_thread(_lookup_or_create, f"thread-{thread_id}")
        ls_backend = LangSmithSandbox(sandbox)
        backend = CompositeBackend(
            default=ls_backend,
            routes={"/": FilesystemBackend(root_dir=str(HERE), virtual_mode=True)},
        )
    else:
        # Introspection — same graph shape, no sandbox, no MCP round-trip
        backend = FilesystemBackend(root_dir=str(HERE), virtual_mode=True)

    @tool
    def retrieve_output(sandbox_path: str) -> str:
        """Copy a file from the sandbox to the local outputs/ directory.

        The sandbox runs in an isolated container — files saved there are not
        visible on the local filesystem until explicitly retrieved. To make a
        file available, write it to /retrieve/<filename> inside the sandbox,
        then call this tool to copy it to outputs/<filename> on local disk
        where the user can open it. Files only; directories are not supported.

        Args:
            sandbox_path: File path inside the sandbox, e.g. /retrieve/chart.png
        """
        if ls_backend is None:
            return "retrieve_output is not available in this context."
        responses = ls_backend.download_files([sandbox_path])
        resp = responses[0]
        if resp.content is None:
            return f"Error retrieving {sandbox_path}: {resp.error}"
        # Use only the filename to prevent path traversal on local disk
        filename = Path(sandbox_path).name
        out_path = HERE / "outputs" / filename
        out_path.parent.mkdir(exist_ok=True)
        out_path.write_bytes(resp.content)
        return f"Saved to outputs/{filename}"

    mcp_client = MultiServerMCPClient({"mock-mail": MAIL_SERVER})
    mail_tools = await mcp_client.get_tools()

    yield create_deep_agent(
        model=strong_model,
        tools=[markdown_to_html, retrieve_output] + mail_tools,
        system_prompt=SYSTEM_PROMPT,
        subagents=build_subagents(backend, enable_search=_enable_search, mail_tools=mail_tools),
        skills=["/skills"],
        memory=["/AGENTS.md"],
        backend=backend,
        name="chinook-sales-assistant",
    )
