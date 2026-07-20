# python/m1/m1.6_homework.py
"""M1.6 Homework: Explore a Different Corner of MCP.

THE IDEA
The lab connected to the LangChain docs MCP server and filtered its tools
down to just search_docs_by_lang_chain. This homework asks you to explore
a different corner of MCP, in one of two ways, whichever you like:
  (a) connect to a different public MCP server entirely, or
  (b) keep the docs-langchain server from the lab, but change the
      ALLOWED filter to a different tool than the lab used (the lab
      printed every tool name available on that server, so you already
      know what else is there).
Either way, ask the agent something the lab's own question didn't cover.
There's no single correct server, filter, or question here.

WHAT YOU FILL IN
  TODO 1: build and return the filtered list of MCP tools to use, from a
    server and filter of your own choosing.
  TODO 2: write a question that puts your chosen tool(s) to work, on a
    topic the lab's question ("what is MCP...") didn't cover.

RUN
  cd python
  uv run ./m1/m1.6_homework.py
"""

import asyncio
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

from deepagents import create_deep_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

from models import model


# ════════════════════════════════════════════════════════════════════════
# TODO 1: Build your MCP client and return its filtered tool list.
#
# Requirements:
#   - Either point "url" at a different public MCP server than the lab's
#     docs-langchain server (no auth/API key required beyond what your
#     labs already use), or keep docs-langchain and set ALLOWED to a tool
#     other than search_docs_by_lang_chain.
#   - Fetch tools with client.get_tools() and filter them the same way
#     the lab did, with an ALLOWED set.
#
# Example shape (delete this and write your own):
#   async def build_tools():
#       client = MultiServerMCPClient({
#           "my-server": {"transport": "http", "url": "https://..."}
#       })
#       tools = await client.get_tools()
#       ALLOWED = {"some_tool_name"}
#       return [t for t in tools if t.name in ALLOWED]
# ════════════════════════════════════════════════════════════════════════

async def build_tools():
    """TODO 1: build a MultiServerMCPClient, fetch its tools, filter them,
    and return the filtered list."""
    raise NotImplementedError("TODO 1: see the comment block above")


# ════════════════════════════════════════════════════════════════════════
# TODO 2: Write a question that puts your chosen tool(s) to work, on a
# topic the lab's question didn't cover.
# ════════════════════════════════════════════════════════════════════════

QUESTION = "TODO 2: replace with a question that puts your chosen tool(s) to work."


async def main():
    tools = await build_tools()
    agent = create_deep_agent(model=model, tools=tools)
    result = await agent.ainvoke({"messages": [{"role": "user", "content": QUESTION}]})
    print(result["messages"][-1].content)


asyncio.run(main())
