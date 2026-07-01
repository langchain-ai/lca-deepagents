// typescript/m2/m2.4_interpreter_agent.ts
import { DatabaseSync } from "node:sqlite";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { createCodeInterpreterMiddleware } from "@langchain/quickjs";
import { tool } from "@langchain/core/tools";
import { createDeepAgent } from "deepagents";
import { z } from "zod";

import { model } from "../models.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const DB_PATH = join(__dirname, "chinook.db");

const queryChinook = tool(
  ({ sql }) => {
    const db = new DatabaseSync(DB_PATH);
    try {
      const rows = db.prepare(sql).all();
      return JSON.stringify(rows);
    } finally {
      db.close();
    }
  },
  {
    name: "query_chinook",
    description: "Execute a read-only SQL query against the Chinook database. Returns JSON array of rows.",
    schema: z.object({ sql: z.string() }),
  }
);

const agent = createDeepAgent({
  model,
  tools: [queryChinook],
  middleware: [createCodeInterpreterMiddleware({ ptc: ["query_chinook"] })],
  systemPrompt:
    "You are a sales analyst for Chinook Digital Music Store. " +
    "Use the query_chinook tool to query the database and the eval tool " +
    "to process results programmatically with JavaScript. " +
    "Key tables: Genre(GenreId, Name), Track(TrackId, Name, GenreId), " +
    "InvoiceLine(InvoiceLineId, InvoiceId, TrackId, UnitPrice, Quantity). " +
    "When joining tables, qualify revenue as InvoiceLine.UnitPrice * InvoiceLine.Quantity.",
});

const result = await agent.invoke(
  {
    messages: [
      {
        role: "user",
        content:
          "Use a single eval() call with programmatic tool calling to do this: " +
          "First query the top 5 genres by total revenue. " +
          "Then, for each of those genres, make a second query to find the " +
          "top-selling track in that genre. " +
          "The second set of queries should be driven by the results of the first — " +
          "use Promise.all so they run in parallel. " +
          "Return a formatted list showing each genre, its total revenue, " +
          "and its top track.",
      },
    ],
  },
  { configurable: { thread_id: "lab-m2.4" } }
);

console.log(result.messages[result.messages.length - 1].content);
