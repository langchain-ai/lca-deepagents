# python/m5/mcp/mock_gmail_server.py
"""A local, offline stand-in for a Gmail MCP server.

This is **Path B** of the course's two Gmail options (see the module README).
Students who don't want to set up real Gmail OAuth get a zero-config MCP server
that speaks the exact same three tools the assistant uses either way:

    list_messages(query)            -> summaries of inbox mail
    read_message(message_id)        -> the full body of one message
    create_draft(to, subject, body) -> save a reply to the drafts folder

Because the tool names and signatures match what a real Gmail MCP server would
expose, the agent code never branches on which backend is in use — only the MCP
config the agent loads changes (see GMAIL_BACKEND in agent.py).

State is a small JSON file managed by mail_store.py. Run directly, this script
serves over stdio and is launched as a subprocess by the MCP client.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from mail_store import load_store, next_id, save_store

mcp = FastMCP("mock-gmail")


@mcp.tool()
def list_messages(query: str = "") -> list[dict]:
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
def read_message(message_id: str) -> dict:
    """Return the full message (sender, subject, date, complete body) by id."""
    store = load_store()
    for m in store["inbox"]:
        if m.get("id") == message_id:
            return m
    return {"error": f"No message with id {message_id!r}."}


@mcp.tool()
def create_draft(to: str, subject: str, body: str) -> dict:
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
    mcp.run()  # stdio transport
