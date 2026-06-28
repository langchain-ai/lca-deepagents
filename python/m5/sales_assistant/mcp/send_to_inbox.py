# python/m5/sales_assistant/mcp/send_to_inbox.py
"""Drop a message into the mock mailbox — the offline stand-in for "a customer
just emailed you."

Run with no arguments to load the bundled RFQ fixture(s) from ``seeds/``; or
pass --from / --subject / --body to inject a custom message. Either way the new
message lands in the inbox and the assistant can find it with list_messages.

Examples:
    uv run python mcp/send_to_inbox.py
    uv run python mcp/send_to_inbox.py --reset
    uv run python mcp/send_to_inbox.py --from "a@b.example" \\
        --subject "Quote please" --body "Can I get 12 Jazz tracks?"
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from mail_store import _SEEDS_DIR, _empty_store, load_store, next_id, save_store


def main() -> None:
    parser = argparse.ArgumentParser(description="Inject a message into the mock inbox.")
    parser.add_argument("--from", dest="sender", help="Sender address.")
    parser.add_argument("--subject", help="Message subject.")
    parser.add_argument("--body", help="Message body.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Clear the mailbox (inbox + drafts) and re-seed from seeds/.",
    )
    args = parser.parse_args()

    if args.reset:
        store = _empty_store()
        for seed in sorted(_SEEDS_DIR.glob("*.json")):
            store["inbox"].append(json.loads(Path(seed).read_text(encoding="utf-8")))
        save_store(store)
        print(f"Mailbox reset. Inbox now has {len(store['inbox'])} message(s).")
        return

    store = load_store()
    if args.sender or args.subject or args.body:
        msg = {
            "id": next_id(store["inbox"], "msg"),
            "from": args.sender or "unknown@example.com",
            "subject": args.subject or "(no subject)",
            "date": "2026-06-14T12:00:00Z",
            "body": args.body or "",
        }
        store["inbox"].append(msg)
        save_store(store)
        print(f"Injected {msg['id']} from {msg['from']!r}.")
    else:
        # No custom fields: make sure the seed fixtures are present.
        load_store()  # seeds on first use
        store = load_store()
        print(f"Inbox has {len(store['inbox'])} message(s). Use --reset to re-seed.")


if __name__ == "__main__":
    main()
