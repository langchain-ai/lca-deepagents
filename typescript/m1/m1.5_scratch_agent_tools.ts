import { DatabaseSync } from "node:sqlite";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { z } from "zod";
import { tool } from "langchain";
import { createDeepAgent } from "deepagents";

import { model } from "../models.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const DB_PATH = join(__dirname, "chinook.db");
const db = new DatabaseSync(DB_PATH);

const SYSTEM_PROMPT = `You are a SQL analyst with access to the Chinook music store database.

Rules:
- Use read_sql for SELECT queries.
- Do not modify the database.
- If a tool returns an error, revise the SQL and try again.
- Show your SQL in your final answer.
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

const agent = createDeepAgent({
  model,
  name: "SQL_Agent",
  tools: [readSql],
  systemPrompt: SYSTEM_PROMPT,
});

const result = await agent.invoke({
  messages: [{ role: "user", content: "Which five genres have the most tracks?" }],
});

console.log(result.messages.at(-1)?.content);
