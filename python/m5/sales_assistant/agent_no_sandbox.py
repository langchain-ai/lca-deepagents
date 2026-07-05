# python/m5/sales_assistant/agent_no_sandbox.py
"""Chinook Sales Assistant — no-sandbox variant.

Uses a local FilesystemBackend and QuickJS code interpreter. No LangSmith
sandbox required. Charts are not available in this configuration.

Start with:
    ./start_no_sandbox.sh
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

logger = logging.getLogger(__name__)

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


async def make_graph():
    client = MultiServerMCPClient({"mock-mail": MAIL_SERVER})
    mail_tools = await client.get_tools()
    return create_deep_agent(
        model=strong_model,
        tools=[markdown_to_html] + mail_tools,
        system_prompt=SYSTEM_PROMPT,
        subagents=build_subagents(_backend, enable_search=_enable_search, mail_tools=mail_tools),
        skills=["/skills"],
        memory=["/AGENTS.md"],
        backend=_backend,
        middleware=[CodeInterpreterMiddleware()],
        name="chinook-sales-assistant",
    )
