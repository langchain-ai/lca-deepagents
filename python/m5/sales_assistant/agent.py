# python/m5/sales_assistant/agent.py
"""The Chinook Sales Assistant — served as a graph for `langgraph dev`.

Mail tools are discovered at startup from the mock mail MCP server
(mcp/mock_mail_server.py), which start.sh brings up before langgraph dev.
make_graph() connects to that already-running server, discovers its tools
via MultiServerMCPClient, and passes them into create_deep_agent.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_quickjs import CodeInterpreterMiddleware
from subagents import build_subagents
from tools.html import markdown_to_html

from models import strong_model

logger = logging.getLogger("chinook-sales-assistant")

HERE = Path(__file__).resolve().parent

SYSTEM_PROMPT = (
    "You are a sales assistant for Jane Peacock, a Sales Support Agent at "
    "Chinook, an online music distributor. Follow your operating manual (loaded "
    "from your memory) and use the matching playbook from /skills/ for each task."
)

MAIL_SERVER = {"transport": "streamable-http", "url": "http://127.0.0.1:5002/mcp"}

_enable_search = bool(os.environ.get("TAVILY_API_KEY"))
if not _enable_search:
    logger.info("TAVILY_API_KEY not set — newsletter research subagent disabled.")

_backend = FilesystemBackend(root_dir=str(HERE), virtual_mode=True)

_tools = [markdown_to_html]
if os.environ.get("ENABLE_SANDBOX"):
    from tools.chart import render_chart
    _tools.append(render_chart)


async def make_graph():
    client = MultiServerMCPClient({"mock-mail": MAIL_SERVER})
    mail_tools = await client.get_tools()
    return create_deep_agent(
        model=strong_model,
        tools=_tools + mail_tools,
        system_prompt=SYSTEM_PROMPT,
        subagents=build_subagents(_backend, enable_search=_enable_search, mail_tools=mail_tools),
        skills=["/skills"],
        memory=["/AGENTS.md"],
        backend=_backend,
        middleware=[CodeInterpreterMiddleware()],
        name="chinook-sales-assistant",
    )
