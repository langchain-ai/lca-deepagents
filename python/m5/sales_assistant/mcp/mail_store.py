# python/m5/mcp/mail_store.py
"""A tiny JSON-file mailbox shared by the mock Gmail MCP server and the
`send_to_inbox` inject CLI.

The store is deliberately dumb: one JSON file with two lists, ``inbox`` and
``drafts``. It exists so the course's Gmail features work offline, with no
OAuth, while presenting the *same* tool surface as a real Gmail MCP server
(``list_messages`` / ``read_message`` / ``create_draft``). Nothing here is
Gmail-specific — it is just enough state to demo the assistant.

Paths are resolved from this file's location, so the store works no matter
what working directory the MCP subprocess is launched from.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# The mailbox lives next to this module, under the module's own directory.
_STORE_PATH = Path(__file__).resolve().parent / "mail_store.json"
_SEEDS_DIR = Path(__file__).resolve().parent / "seeds"


def _empty_store() -> dict[str, list[dict[str, Any]]]:
    return {"inbox": [], "drafts": []}


def load_store() -> dict[str, list[dict[str, Any]]]:
    """Read the mailbox, seeding it from ``seeds/`` on first use.

    If no store file exists yet, every ``*.json`` fixture in ``seeds/`` is
    loaded into the inbox so a fresh checkout has a quote request waiting.
    """
    if _STORE_PATH.exists():
        with _STORE_PATH.open(encoding="utf-8") as f:
            return json.load(f)

    store = _empty_store()
    for seed in sorted(_SEEDS_DIR.glob("*.json")):
        with seed.open(encoding="utf-8") as f:
            store["inbox"].append(json.load(f))
    save_store(store)
    return store


def save_store(store: dict[str, list[dict[str, Any]]]) -> None:
    """Persist the mailbox to disk."""
    with _STORE_PATH.open("w", encoding="utf-8") as f:
        json.dump(store, f, indent=2)


def next_id(messages: list[dict[str, Any]], prefix: str) -> str:
    """Return the next sequential id like ``msg-1`` / ``draft-3``."""
    n = 1 + sum(1 for m in messages if str(m.get("id", "")).startswith(prefix))
    return f"{prefix}-{n}"
