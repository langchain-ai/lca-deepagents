# python/m5/agent.py
"""The Chinook Sales Assistant — served as a graph for `langgraph dev`.

This module is just the agent. The Gmail MCP plumbing lives in `gmail_mcp.py`;
all this file does is assemble the agent around whatever tools that discovery
returns.

`langgraph.json` points at the async factory `make_graph`, which langgraph awaits
once at startup. We use a factory (not a plain module-level `agent = ...`) for
one reason: the Gmail tools come from an MCP server, and asking an MCP server for
its tool list is an async call — so we discover the tools up front, then build
the agent around whatever we found. If Gmail is unreachable, discovery returns no
tools and the assistant simply comes up without them.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

# Make the shared workshop model module importable (python/models.py). models.py
# also calls load_dotenv, so env vars (API keys, GMAIL_BACKEND) are loaded.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from models import strong_model  # noqa: E402

from deepagents import create_deep_agent  # noqa: E402
from deepagents.backends import FilesystemBackend  # noqa: E402
from langchain_quickjs import CodeInterpreterMiddleware  # noqa: E402

from gmail_mcp import load_gmail_tools  # noqa: E402
from subagents import build_subagents  # noqa: E402
from tools.html import markdown_to_html  # noqa: E402

logger = logging.getLogger("chinook-sales-assistant")

HERE = Path(__file__).resolve().parent


SYSTEM_PROMPT = (
    "You are a sales assistant for Jane Peacock, a Sales Support Agent at "
    "Chinook, an online music distributor. Follow your operating manual (loaded "
    "from your memory) and use the matching playbook from /skills/ for each task."
)


async def make_graph():
    """Async graph factory — built once by `langgraph dev` at startup."""
    # Real local disk under this module only (virtual_mode locks the agent to
    # this directory: skills/, AGENTS.md, outputs/). Suitable for local dev;
    # not for a multi-tenant web server.
    backend = FilesystemBackend(root_dir=str(HERE), virtual_mode=True)

    enable_search = bool(os.environ.get("TAVILY_API_KEY"))
    if not enable_search:
        logger.info("TAVILY_API_KEY not set — newsletter research subagent disabled.")

    gmail_tools = await load_gmail_tools()

    # The main agent holds NO gated tools. Gmail (gmail_create_draft) lives on
    # the inbox-manager subagent and SQL writes (add_customer) on chinook-analyst,
    # each with its own approval gate — so the always-present general-purpose
    # subagent, which inherits the main agent's tools, can never reach a write
    # ungated. The main agent keeps only safe tools plus the interpreter.
    tools = [markdown_to_html]

    # Optional sandbox-backed chart tool (the course's optional feature).
    if os.environ.get("ENABLE_SANDBOX"):
        from tools.chart import render_chart

        tools.append(render_chart)

    return create_deep_agent(
        model=strong_model,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
        subagents=build_subagents(
            backend, enable_search=enable_search, gmail_tools=gmail_tools
        ),
        skills=["/skills"],
        memory=["/AGENTS.md"],
        backend=backend,
        middleware=[CodeInterpreterMiddleware()],
        name="chinook-sales-assistant",
    )
