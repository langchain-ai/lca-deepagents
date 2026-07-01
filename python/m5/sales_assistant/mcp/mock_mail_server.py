# python/m5/sales_assistant/mcp/mock_mail_server.py
"""A local, offline mock mail MCP server.

Exposes three tools over HTTP (streamable-http transport) on port 5002:

    mail_list_messages(query)            -> summaries of inbox mail
    mail_read_message(message_id)        -> the full body of one message
    mail_create_draft(to, subject, body) -> save a reply to the drafts folder

State is a small JSON file managed by mail_store.py. Started by start.sh
before langgraph dev so make_graph() can discover the tools at startup.
"""

from __future__ import annotations

from mail_store import load_store, next_id, save_store
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("mock-mail", host="127.0.0.1", port=5002)


@mcp.tool()
def mail_list_messages(query: str = "") -> list[dict]:
    """List messages in the inbox.

    Returns a summary (id, sender, subject, date, snippet) for each message —
    not the full body. Use read_message to open one. The optional ``query`` is
    a case-insensitive substring matched against the subject and sender, mostly
    to mirror Gmail's search box; leave it empty to list everything.
    """
    store = load_store()
    q = query.strip().lower()
    out = []
    for m in store["inbox"]:
        haystack = f"{m.get('subject', '')} {m.get('from', '')}".lower()
        if q and q not in haystack:
            continue
        body = m.get("body", "")
        out.append(
            {
                "id": m.get("id"),
                "from": m.get("from"),
                "subject": m.get("subject"),
                "date": m.get("date"),
                "snippet": body[:140] + ("…" if len(body) > 140 else ""),
            }
        )
    return out


@mcp.tool()
def mail_read_message(message_id: str) -> dict:
    """Return the full message (sender, subject, date, complete body) by id."""
    store = load_store()
    for m in store["inbox"]:
        if m.get("id") == message_id:
            return m
    return {"error": f"No message with id {message_id!r}."}


@mcp.tool()
def mail_create_draft(to: str, subject: str, body: str) -> dict:
    """Save a reply to the drafts folder. Does NOT send.

    Mirrors a real Gmail "create draft" call: the message is staged for the
    human to review and send later. In this course a human-in-the-loop gate
    runs before this tool, so a draft is only written after explicit approval.
    """
    store = load_store()
    draft = {
        "id": next_id(store["drafts"], "draft"),
        "to": to,
        "subject": subject,
        "body": body,
    }
    store["drafts"].append(draft)
    save_store(store)
    return {"status": "draft_saved", "draft_id": draft["id"], "to": to, "subject": subject}


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
