import sys
import asyncio
import contextlib
import io
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models import model
from deepagents import create_deep_agent
from deepagents_code.mcp_tools import get_mcp_tools

MCP_CONFIG = Path(__file__).resolve().parent / ".mcp.json"

MCP_CONFIG.write_text(json.dumps({
    "mcpServers": {
        "docs-langchain": {
            "type": "http",
            "url": "https://docs.langchain.com/mcp",
            "allowedTools": ["search_docs_by_lang_chain"]
        }
    }
}, indent=2))


async def main():
    tools, session_manager, server_infos = await get_mcp_tools(str(MCP_CONFIG))

    for info in server_infos:
        print(f"\n{info.name} ({info.transport}): {len(info.tools)} tool(s)")
        for t in info.tools:
            print(f"  {t.name}")
            print(f"  {t.description[:90]}")

    agent = create_deep_agent(model=model, tools=tools)

    result = await agent.ainvoke({
        "messages": [{"role": "user", "content": "How does LangGraph's interrupt API work, and what role does a checkpointer play?"}]
    })
    print(result["messages"][-1].content)

    if session_manager:
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                await session_manager.cleanup()
        except Exception:
            pass


asyncio.run(main())
