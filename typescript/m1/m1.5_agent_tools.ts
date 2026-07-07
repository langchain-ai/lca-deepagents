import { DatabaseSync } from "node:sqlite";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { createInterface } from "node:readline/promises";
import { tool } from "@langchain/core/tools";
import { z } from "zod";
import { Command, INTERRUPT, isInterrupted } from "@langchain/langgraph";
import { MemorySaver } from "@langchain/langgraph";
import { createDeepAgent } from "deepagents";

import { model } from "../models.js";

interface ActionRequest {
  name: string;
  args: Record<string, unknown>;
}

interface ApprovalRequest {
  action_requests: ActionRequest[];
}

const __dirname = dirname(fileURLToPath(import.meta.url));
const DB_PATH = join(__dirname, "chinook.db");
const db = new DatabaseSync(DB_PATH);

const SYSTEM_PROMPT = `
You are a SQL analyst with access to the Chinook music store database.
You have two tools at your disposal: read_sql and write_sql.
- Use read_sql for SELECT queries.
- Use write_sql for INSERT, UPDATE, DELETE, and ALTER operations.
- Think step-by-step: read first, then write.
- If a tool returns an error, revise and retry
- Show the SQL in the final answer.
`;

const readSql = tool(
  ({ query }) => {
    try {
      const rows = db.prepare(query).all();
      return JSON.stringify(rows);
    } catch (e) {
      return `Error: ${e}`;
    }
  },
  {
    name: "read_sql",
    description: "Run a read-only SELECT query against the Chinook music store database.",
    schema: z.object({ query: z.string() }),
  }
);

const writeSql = tool(
  ({ query }) => {
    try {
      const result = db.prepare(query).run();
      return JSON.stringify(result);
    } catch (e) {
      return `Error: ${e}`;
    }
  },
  {
    name: "write_sql",
    description:
      "Execute a write operation (INSERT, UPDATE, DELETE, ALTER) against the Chinook database. Requires human approval before executing.",
    schema: z.object({ query: z.string() }),
  }
);

const checkpointer = new MemorySaver();
const agent = createDeepAgent({
  model,
  systemPrompt: SYSTEM_PROMPT,
  tools: [readSql, writeSql],
  checkpointer,
  interruptOn: { write_sql: true },
});

const config = { configurable: { thread_id: "lab3" } };

let result = await agent.invoke(
  {
    messages: [
      {
        role: "user",
        content:
          "What genres are in the database? Then add a new genre called 'Synthwave'.",
      },
    ],
  },
  config
);

const rl = createInterface({ input: process.stdin, output: process.stdout });

while (isInterrupted<ApprovalRequest>(result) && result[INTERRUPT].length) {
  const pending = result[INTERRUPT][0].value!;
  for (const req of pending.action_requests) {
    console.log(`\nApproval required for ${req.name}:`);
    console.log(`  ${JSON.stringify(req.args)}`);
  }
  const approval = (await rl.question("\nApprove? (yes/no): ")).trim().toLowerCase();
  const decision = ["yes", "y"].includes(approval) ? "approve" : "reject";
  const decisions = pending.action_requests.map(() => ({ type: decision }));
  result = await agent.invoke(new Command({ resume: { decisions } }), config);
}

rl.close();
console.log(result.messages[result.messages.length - 1].content);
