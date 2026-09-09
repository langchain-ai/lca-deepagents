# python/m5/subagents.py
"""The specialist subagents for the Chinook Sales Assistant.

They are built by a function rather than defined at import time because the
chinook-analyst's MemoryMiddleware needs the *same* filesystem backend the main
agent uses (so the schema it discovers and the memory it reads point at the same
file on disk).

- chinook-analyst — owns the database; self-bootstraps the schema into its own
  AGENTS.md; gates new-customer writes behind human approval.
- inbox-manager   — owns the mail (MCP) tools; gates saving a draft behind
  human approval. Only present when mail tools were discovered.
- quote-reviewer  — sanity-checks a drafted quote before it's sent.

genre-researcher itself is still an in-process (synchronous) subagent, but not
of the main agent — it's used inside newsletter-agent, a standalone graph
(see `newsletter_agent_graph.py`) launched via `AsyncSubAgentMiddleware` so
the whole newsletter job (research + assembly) runs in the background
instead of blocking the main agent. `GENRE_PROMPT` stays in this module and
is imported from there.

Why the inbox-manager lives in a subagent: the general-purpose subagent (always present)
inherits the *main* agent's tools, so any gated tool placed on the main agent
could be invoked ungated through delegation. Keeping `mail_create_draft` and
`add_customer` solely on gated specialists means the only path to either write
runs through its human-approval gate.
"""

from __future__ import annotations

from deepagents import MemoryMiddleware
from deepagents.backends.protocol import BackendProtocol
from tools.sql import add_customer, introspect_schema, query_chinook

from models import model, strong_model

# Allow all three agent-inbox decisions on the gated write.
_APPROVE_EDIT_REJECT = {"allowed_decisions": ["approve", "edit", "reject"]}


ANALYST_PROMPT = """You are the chinook-analyst, the data specialist for the \
Chinook Sales Assistant. You are the only agent that touches the database.

Detailed operating instructions and the database schema live in your memory \
(loaded automatically). Follow them. In short: answer with exact figures from \
`query_chinook`, learn the schema once with `introspect_schema` and record it \
in your memory, and use `add_customer` only when asked to add a genuinely new \
customer (a human approves that write)."""

INBOX_PROMPT = """You are the inbox-manager, the email specialist for the \
Chinook Sales Assistant. You own Jane's inbox and are the only agent that \
touches it.

Your tools (MCP, prefixed with the server name "mail"):
- `mail_list_messages` — list inbox messages (optionally filtered by a query).
- `mail_read_message` — read one message in full by id.
- `mail_create_draft` — save a reply to the drafts folder. It NEVER sends.

When asked to find or read mail, return a tight summary the caller can act on \
(sender, subject, and the key content) — not the raw dump.

When asked to save a draft, just call `mail_create_draft` with the given \
recipient, subject, and body. Saving a draft pauses automatically for Jane to \
approve, edit, or reject — that pause IS the approval, so don't ask for \
permission in prose first; make the call. Never invent a send tool; you only \
ever create drafts."""

REVIEWER_PROMPT = """You are the quote-reviewer. You receive a drafted quote — \
line items (description, quantity, unit price, line total), any discount, and \
the grand total — and you check it before it goes to the customer.

Verify:
- The arithmetic: quantity x unit price for each line, and the grand total.
- Internal consistency: any stated discount is actually applied; nothing is \
double-counted or missing.
- Plausibility: unit prices look like catalogue prices (tracks are normally \
about $0.99); totals aren't off by an order of magnitude.

Reply concisely: either "Looks correct" with a one-line confirmation, or a \
short list of specific corrections. Do not rewrite the customer email — just \
review the numbers and terms."""

GENRE_PROMPT = """You are a music journalist researching one genre for an \
online music distributor's weekly newsletter.

You will be given a single genre and a private research folder to work in.

How to work:
1. Use internet_search to find recent, noteworthy developments in that genre \
   — new releases, notable artists, trends, or events. Run a few searches.
2. Save the COMPLETE, verbatim output of ALL your searches to a single file: \
   write_file("/research/<genre>/sources.md", ...). Do NOT summarize or trim. \
   This keeps the bulky material out of the editor's context.
3. Only then, from what you found, write one tight newsletter segment.

Return ONLY the finished segment as your reply:
- A markdown section: a "## <Genre>" heading followed by ~120-180 words.
- Lively but factual; name specific artists and releases.
- Do NOT paste raw search results into your reply — those live in your files."""


def build_subagents(
    backend: BackendProtocol,
    *,
    mail_tools: list,
) -> list[dict]:
    """Return the subagent specs, wired to the shared filesystem backend."""

    chinook_analyst = {
        "name": "chinook-analyst",
        "description": (
            "Query the Chinook database for catalogue prices, customer records, "
            "purchase history, and territory metrics, and add new customers "
            "(with approval). Delegate all database work here."
        ),
        "system_prompt": ANALYST_PROMPT,
        "tools": [query_chinook, introspect_schema, add_customer],
        "model": model,
        # Per-subagent memory: its own AGENTS.md, on the same backend the main
        # agent uses, so the schema it writes is the schema it later reads.
        "middleware": [
            MemoryMiddleware(
                backend=backend,
                sources=["/agents/chinook-analyst/AGENTS.md"],
            )
        ],
        # The one gated write — pauses for human approval before inserting.
        "interrupt_on": {"add_customer": _APPROVE_EDIT_REJECT},
    }

    quote_reviewer = {
        "name": "quote-reviewer",
        "description": (
            "Review a drafted quote (line items, discount, total) for correct "
            "arithmetic and sane pricing before it is sent. Send it the numbers."
        ),
        "system_prompt": REVIEWER_PROMPT,
        "model": strong_model,
    }

    inbox_manager = {
        "name": "inbox-manager",
        "description": (
            "Read Jane's inbox and save reply drafts. Delegate any "
            "email work here: finding/reading messages and creating a "
            "draft reply (which pauses for Jane's approval)."
        ),
        "system_prompt": INBOX_PROMPT,
        "tools": mail_tools,
        "model": model,
        "interrupt_on": {"mail_create_draft": _APPROVE_EDIT_REJECT},
    }

    return [chinook_analyst, quote_reviewer, inbox_manager]
