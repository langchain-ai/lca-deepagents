// typescript/m5/sales_assistant/agent.ts
/**
 * Chinook Sales Assistant.
 *
 * Uses a local FilesystemBackend, a QuickJS code interpreter for arithmetic
 * and data prep, and a dedicated chart tool for rendering.
 *
 * Start with:
 *     ./start.sh
 */
import { dirname } from "node:path";
import { fileURLToPath } from "node:url";

import { MultiServerMCPClient } from "@langchain/mcp-adapters";
import { createCodeInterpreterMiddleware } from "@langchain/quickjs";
import { context } from "langchain";
import { FilesystemBackend, createDeepAgent } from "deepagents";

import { strongModel } from "../../models.js";
import { buildSubagents } from "./subagents.js";
import { renderPieChart } from "./tools/chart.js";
import { markdownToHtml } from "./tools/html.js";

const HERE = dirname(fileURLToPath(import.meta.url));

const SYSTEM_PROMPT = context`
  You are a sales assistant for Jane Peacock, a Sales Support Agent at
  Chinook, an online music distributor. Follow your operating manual (loaded
  from your memory) and use the matching playbook from /skills/ for each task.`;

const enableSearch = Boolean(process.env.TAVILY_API_KEY);
if (!enableSearch) {
  console.log("TAVILY_API_KEY not set — newsletter research subagent disabled.");
}

const backend = new FilesystemBackend({ rootDir: HERE, virtualMode: true });

const client = new MultiServerMCPClient({
  "mock-mail": { transport: "http", url: "http://127.0.0.1:5002/mcp" },
});
const mailTools = await client.getTools();

export const graph = createDeepAgent({
  model: strongModel,
  tools: [markdownToHtml, renderPieChart, ...mailTools],
  systemPrompt: SYSTEM_PROMPT,
  subagents: buildSubagents(backend, { enableSearch, mailTools }),
  skills: ["/skills"],
  memory: ["/AGENTS.md"],
  backend,
  middleware: [createCodeInterpreterMiddleware()],
  name: "chinook-sales-assistant",
});
