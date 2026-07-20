# python/m1/m1.6_homework_filled.py
"""Reference copy of m1.6_homework.py with TODOs 1 and 2 filled in so you
can run it end to end and see what "done" looks like. This is just one
possible answer, so yours might be different. Explore!"""

import asyncio
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

from deepagents import create_deep_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

from models import model


# TODO 1 filled in: same docs-langchain server as the lab, but this time
# we filter to the OTHER tool the lab printed and never used.
async def build_tools():
    client = MultiServerMCPClient({
        "docs-langchain": {
            "transport": "http",
            "url": "https://docs.langchain.com/mcp",
        }
    })
    tools = await client.get_tools()

    ALLOWED = {"query_docs_filesystem_docs_by_lang_chain"}
    return [t for t in tools if t.name in ALLOWED]


# TODO 2 filled in
QUESTION = (
    "Use the LangChain docs filesystem tool to list what's under the root "
    "directory of the docs, and tell me whether there's a folder related "
    "to deepagents."
)


async def main():
    tools = await build_tools()
    agent = create_deep_agent(model=model, tools=tools)
    result = await agent.ainvoke({"messages": [{"role": "user", "content": QUESTION}]})
    print(result["messages"][-1].content)


asyncio.run(main())
