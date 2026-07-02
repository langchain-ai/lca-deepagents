# python/m5/sales_assistant/test_sandbox_quick.py
"""Quick sandbox smoke test — completes in ~30 seconds.

Verifies the sandbox agent is running and retrieve_output works end-to-end.
Start the sandbox server first, then run:

    ENABLE_SANDBOX=1 ./start.sh        # terminal 1
    uv run python test_sandbox_quick.py  # terminal 2
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from dotenv import load_dotenv
from langgraph_sdk import get_client

load_dotenv(Path(__file__).parent / "../../.env")

API_URL = "http://127.0.0.1:2024"
OUTPUTS_DIR = Path(__file__).parent / "outputs"
TARGET = OUTPUTS_DIR / "quick_check.txt"


async def main() -> None:
    client = get_client(url=API_URL)

    TARGET.unlink(missing_ok=True)

    print("Creating thread...")
    thread = await client.threads.create()

    print("Asking agent to write and retrieve a file...")
    run = await client.runs.create(
        thread["thread_id"],
        "agent",
        input={"messages": [{"role": "user", "content":
            "Write the text 'sandbox ok' to /retrieve/quick_check.txt in the sandbox, "
            "then call retrieve_output with sandbox_path='/retrieve/quick_check.txt'."
        }]},
    )
    await client.runs.join(thread["thread_id"], run["run_id"])

    if TARGET.exists():
        content = TARGET.read_text().strip()
        print(f"PASS — outputs/quick_check.txt exists: {repr(content)}")
    else:
        print("FAIL — outputs/quick_check.txt not found")


asyncio.run(main())
