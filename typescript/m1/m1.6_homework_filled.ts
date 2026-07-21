// typescript/m1/m1.6_homework_filled.ts
/**
 * Reference copy of m1.6_homework.ts with TODOs 1 and 2 filled in so you
 * can run it end to end and see what "done" looks like. This is just one
 * possible answer, so yours might be different. Explore!
 */

import { MultiServerMCPClient } from "@langchain/mcp-adapters";
import { createDeepAgent } from "deepagents";

import { model } from "../models.js";

// TODO 1 filled in: a different public MCP server than the lab's,
// X Docs, which searches X's public API documentation.
async function buildTools() {
  const client = new MultiServerMCPClient({
    "x-docs": {
      transport: "http",
      url: "https://docs.x.com/mcp",
    },
  });

  const tools = await client.getTools();

  const ALLOWED = new Set(["search_x"]);
  return { client, tools: tools.filter((t) => ALLOWED.has(t.name)) };
}

// TODO 2 filled in
const QUESTION =
  "Use the X Docs tool to search the X API documentation: what HTTP " +
  "status code and error code does the API return when a rate limit " +
  "is exceeded?";

const { client, tools } = await buildTools();

try {
  const agent = createDeepAgent({ model, tools });

  const result = await agent.invoke({
    messages: [{ role: "user", content: QUESTION }],
  });

  console.log(result.messages.at(-1)?.content);
} finally {
  await client.close();
}
