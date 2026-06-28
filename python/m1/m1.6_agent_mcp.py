import asyncio

from deepagents import create_deep_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

from models import model

ALLOWED = {"search_docs_by_lang_chain"}


async def main():
    client = MultiServerMCPClient({
        "docs-langchain": {
            "transport": "http",
            "url": "https://docs.langchain.com/mcp",
        }
    })
    tools = await client.get_tools()

    print(f"\ndocs-langchain: {len(tools)} tool(s)")
    for t in tools:
        print(f"  {t.name}")
        print(f"  {t.description[:90]}")

    tools = [t for t in tools if t.name in ALLOWED]

    agent = create_deep_agent(model=model, tools=tools)

    result = await agent.ainvoke({
        "messages": [{"role": "user", "content": "Use the LangChain docs MCP tool to explain what MCP is and how LangChain uses MCP tools."}]
    })
    print(result["messages"][-1].content)


asyncio.run(main())
