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


async def main() -> None:
    client = get_client(url=API_URL)

    for f in OUTPUTS_DIR.glob("quick_check_*.txt"):
        f.unlink()

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

    matches = sorted(OUTPUTS_DIR.glob("quick_check_*.txt"))
    if matches:
        content = matches[-1].read_text().strip()
        print(f"PASS — {matches[-1].name} exists: {repr(content)}")
    else:
        print("FAIL — no quick_check_*.txt found in outputs/")


asyncio.run(main())
