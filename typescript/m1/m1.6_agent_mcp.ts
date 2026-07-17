import { MultiServerMCPClient } from "@langchain/mcp-adapters";
import { createDeepAgent } from "deepagents";

import { model } from "../models.js";

const ALLOWED = new Set(["search_docs_by_lang_chain"]);

const client = new MultiServerMCPClient({
  "docs-langchain": {
    transport: "http",
    url: "https://docs.langchain.com/mcp",
  },
});

try {
  let tools = await client.getTools();

  console.log(`\ndocs-langchain: ${tools.length} tool(s)`);
  for (const t of tools) {
    console.log(`  ${t.name}`);
    console.log(`  ${t.description?.slice(0, 90)}`);
  }

  tools = tools.filter((t) => ALLOWED.has(t.name));

  const agent = createDeepAgent({ model, tools });

  const result = await agent.invoke({
    messages: [
      {
        role: "user",
        content:
          "Use the LangChain docs MCP tool to explain what MCP is and how LangChain uses MCP tools.",
      },
    ],
  });

  console.log(result.messages.at(-1)?.content);
} finally {
  await client.close();
}