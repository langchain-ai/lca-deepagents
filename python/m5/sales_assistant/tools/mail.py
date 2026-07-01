# python/m5/sales_assistant/tools/mail.py
"""Mail tools for the inbox-manager subagent.

These are plain LangChain tools — no MCP discovery at startup. Each call
opens a short-lived MCP session to the mock mail server (started separately
via start.sh) and invokes the named tool by name.

Tool names mirror the MCP server's tool names so the inbox-manager prompt
stays accurate.
"""

from __future__ import annotations

import logging

from langchain_core.tools import tool
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

logger = logging.getLogger("chinook-sales-assistant")

_MAIL_SERVER_URL = "http://127.0.0.1:5001/mcp"


async def _call(tool_name: str, arguments: dict) -> str:
    """Open a short-lived MCP session and invoke one tool by name."""
    async with streamablehttp_client(_MAIL_SERVER_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)
            return result.content[0].text if result.content else ""


@tool
async def mail_list_messages(query: str = "") -> str:
    """List messages in the inbox.

    Returns a summary (id, sender, subject, date, snippet) for each message —
    not the full body. Use mail_read_message to open one. The optional query is
    a case-insensitive substring matched against subject and sender; leave it
    empty to list everything.
    """
    return await _call("list_messages", {"query": query})


@tool
async def mail_read_message(message_id: str) -> str:
    """Return the full message (sender, subject, date, complete body) by id."""
    return await _call("read_message", {"message_id": message_id})


@tool
async def mail_create_draft(to: str, subject: str, body: str) -> str:
    """Save a reply to the drafts folder. Does NOT send.

    Mirrors a real Gmail "create draft" call: the message is staged for the
    human to review and send later. In this course a human-in-the-loop gate
    runs before this tool, so a draft is only written after explicit approval.
    """
    return await _call("create_draft", {"to": to, "subject": subject, "body": body})


MAIL_TOOLS = [mail_list_messages, mail_read_message, mail_create_draft]
