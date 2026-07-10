// typescript/m2/m2.4_interpreter_agent.ts
import { randomUUID } from "node:crypto";
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

const TASK =
  "Who is our top-selling artist, what is their best-selling album, " +
  "what is the most-purchased track on that album, " +
  "and how many distinct customers have bought that track? " +
  "Each answer depends on the result of the previous query.";

const SYSTEM =
  "You are a sales analyst for Chinook Digital Music Store. " +
  "Use the query_chinook tool to query the database. " +
  "Key tables: Artist(ArtistId, Name), Album(AlbumId, Title, ArtistId), " +
  "Track(TrackId, Name, AlbumId), " +
  "InvoiceLine(InvoiceLineId, InvoiceId, TrackId, UnitPrice, Quantity). " +
  "Revenue is InvoiceLine.UnitPrice * InvoiceLine.Quantity.";

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
    description: "Execute a read-only SQL query against the Chinook database. Returns a JSON-encoded string.",
    schema: z.object({ sql: z.string() }),
  }
);

// --- Agent with interpreter ---
// Additional information is added to the system prompt to guide the agent to use
// the interpreter as well as some hints on how to use it.

const agentWith = createDeepAgent({
  model,
  tools: [queryChinook],
  middleware: [createCodeInterpreterMiddleware({ ptc: ["query_chinook"] })],
  systemPrompt:
    SYSTEM +
    " The eval tool supports Programmatic Tool Calling (PTC): JavaScript" +
    " running inside eval() can call query_chinook via tools.queryChinook()." +
    " For dependent queries where each answer requires a result from the" +
    " previous, prefer a single eval() call that chains all queries in" +
    " JavaScript — intermediate values stay in variables and never return to the model.",
});

const resultWith = await agentWith.invoke(
  { messages: [{ role: "user", content: TASK }] },
  { configurable: { thread_id: randomUUID() } }
);

console.log("=== With interpreter ===");
console.log(resultWith.messages[resultWith.messages.length - 1].content);

// --- Agent without interpreter ---

const agentWithout = createDeepAgent({
  model,
  tools: [queryChinook],
  systemPrompt: SYSTEM,
});

const resultWithout = await agentWithout.invoke(
  { messages: [{ role: "user", content: TASK }] },
  { configurable: { thread_id: randomUUID() } }
);

console.log("\n=== Without interpreter ===");
console.log(resultWithout.messages[resultWithout.messages.length - 1].content);
