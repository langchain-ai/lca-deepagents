"""Stop this lesson's running sandboxes.

Run on shutdown by start.sh so a student closing langgraph dev stops
billing for sandbox compute immediately, instead of waiting out
idle_ttl_seconds. Only touches sandboxes named "thread-*" (this project's
naming convention from agent.py) that are currently "ready" — never touches
other sandboxes in the workspace.
"""

from __future__ import annotations

from pathlib import Path

from dotenv import dotenv_values
from langsmith.sandbox import SandboxClient

# Load the key explicitly from python/.env rather than relying on the
# ambient shell environment, which may hold an unrelated LANGSMITH_API_KEY
# (e.g. from an outer shell/session) that silently points at the wrong
# workspace — this bit us once already when building this lesson.
ENV_PATH = Path(__file__).resolve().parents[2] / ".env"


def main() -> None:
    api_key = dotenv_values(ENV_PATH).get("LANGSMITH_API_KEY")
    client = SandboxClient(api_key=api_key)
    targets = [
        sb
        for sb in client.list_sandboxes()
        if sb.name.startswith("thread-") and getattr(sb, "status", None) == "ready"
    ]
    for sb in targets:
        try:
            client.stop_sandbox(sb.name)
            print(f"Stopped sandbox {sb.name}")
        except Exception as exc:
            print(f"Could not stop sandbox {sb.name}: {exc}")


if __name__ == "__main__":
    main()
