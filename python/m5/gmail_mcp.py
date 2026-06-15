# python/m5/gmail_mcp.py
"""Gmail MCP discovery — the plumbing that hands `agent.py` its Gmail tools.

This is deliberately split out of `agent.py` so that file reads as just the
agent. The one function the agent calls is `load_gmail_tools()`.

The Gmail tools come from an MCP server. Asking that server for its tool list is
an async call, so discovery happens up front (in the async graph factory) before
the agent is built. Two backends, selected by the GMAIL_BACKEND env var:

- "mock" (default): launch the bundled local stdio server, `mcp/mock_gmail_server.py`.
- "real": a hosted Gmail MCP server + OAuth, from the checked-in `mcp_real.json`.
- "none": skip Gmail entirely.

Discovery always degrades gracefully: a missing or broken Gmail server just means
the assistant runs without Gmail tools, never a failed startup.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import tempfile
from pathlib import Path

logger = logging.getLogger("chinook-sales-assistant")

HERE = Path(__file__).resolve().parent
# Written outside the project tree so `langgraph dev`'s file watcher doesn't see
# it change and trigger a reload at graph-build time.
GENERATED_MCP_CONFIG = Path(tempfile.gettempdir()) / "lca_m5_mcp.generated.json"

# Keep the MCP session manager alive for the life of the server. The MCP tools
# call back into it lazily; if it were garbage-collected the stdio subprocess
# (mock Gmail) would be torn down and the tools would stop working.
_mcp_session_manager = None


def _write_mock_mcp_config() -> Path:
    """Write an MCP config that launches the bundled mock Gmail server over
    stdio, using absolute paths so it works regardless of the server's CWD."""
    config = {
        "mcpServers": {
            "gmail": {
                "command": sys.executable,
                "args": [str(HERE / "mcp" / "mock_gmail_server.py")],
            }
        }
    }
    GENERATED_MCP_CONFIG.write_text(json.dumps(config, indent=2), encoding="utf-8")
    return GENERATED_MCP_CONFIG


def _mcp_config_path() -> Path | None:
    """Resolve which MCP config to load based on GMAIL_BACKEND.

    - "mock" (default): generate and use the local stdio mock server config.
    - "real": use the checked-in mcp_real.json (hosted Gmail + OAuth).
    - "none": skip Gmail entirely.
    """
    backend = os.environ.get("GMAIL_BACKEND", "mock").strip().lower()
    if backend == "none":
        return None
    if backend == "real":
        real = HERE / "mcp_real.json"
        return real if real.exists() else None
    return _write_mock_mcp_config()


async def load_gmail_tools() -> list:
    """Discover Gmail MCP tools, tolerating any failure.

    Returns the tools list (possibly empty). Never raises — a missing or broken
    Gmail server just means the assistant runs without Gmail tools.
    """
    global _mcp_session_manager

    config_path = _mcp_config_path()
    if config_path is None:
        logger.info("Gmail disabled (GMAIL_BACKEND=none or no config).")
        return []

    try:
        from deepagents_code.mcp_tools import get_mcp_tools

        tools, session_manager, server_infos = await get_mcp_tools(str(config_path))
        _mcp_session_manager = session_manager  # keep alive
        for info in server_infos:
            if info.status not in ("ok", "connected"):
                logger.warning(
                    "MCP server %r status=%s: %s",
                    info.name, info.status, getattr(info, "error", ""),
                )
        logger.info("Loaded %d Gmail MCP tool(s).", len(tools))
        return tools
    except Exception as exc:  # noqa: BLE001 - resilience is the whole point
        logger.warning("Could not load Gmail MCP tools (%s). Continuing without.", exc)
        return []
