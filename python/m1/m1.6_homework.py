# python/m1/m1.6_homework.py
"""M1.6 Homework: Connect to a Different MCP Server.

THE IDEA
Lab 1 connected to the LangChain docs MCP server and filtered its tools
down to just search_docs_by_lang_chain. This homework asks you to connect
to a different public MCP server entirely, one that requires no auth
beyond what your labs already use, and put one of its tools to work.

Don't know where to look? A few free, no-auth public servers to try:

- DeepWiki (https://mcp.deepwiki.com/mcp): ask questions about any
  public GitHub repo's code and docs.
- X Docs (https://docs.x.com/mcp): search and retrieve X's public API
  documentation.
  Or find your own!

WHAT YOU FILL IN
TODO 1: build and return the filtered list of MCP tools to use from a
server and filter of your own choosing.
TODO 2: write a question suited to your chosen server's own domain,
not Lab 1's "what is MCP..." question, which won't make sense to
ask a server about GitHub repos, API docs, or whatever you picked.

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

async def build_tools():
    """Build a DeepWiki MCP client, fetch its tools, filter them, and return the filtered list."""

    client = MultiServerMCPClient({
        "deepwiki": {
            "transport": "http",
            "url": "https://mcp.deepwiki.com/mcp",
        }
    })

    tools = await client.get_tools()

    ALLOWED = {"ask_question"}

    return [t for t in tools if t.name in ALLOWED]


# ════════════════════════════════════════════════════════════════════════

# TODO 2: Write a question suited to your chosen server's own domain.

QUESTION = (
    "Using DeepWiki, explain the main architecture of the "
    "langchain-ai/deepagents repository and describe its key components."
)


async def main():
    tools = await build_tools()

    agent = create_deep_agent(
        model=model,
        tools=tools
    )

    result = await agent.ainvoke({
        "messages": [
            {
                "role": "user",
                "content": QUESTION
            }
        ]
    })

    print(result["messages"][-1].content)


asyncio.run(main())