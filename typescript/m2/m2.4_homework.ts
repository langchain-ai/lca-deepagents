// typescript/m2/m2.4_homework.ts
/**
 * M2.4 Homework: Ask Your Own Question, Then Grade It.
 *
 * THE IDEA
 * Lab 2 asked one fixed, dependent-query question about the Chinook
 * database and let the interpreter chain four SQL queries together inside
 * a single eval() call. This homework asks you to pose your OWN question
 * about the database (anything queryChinook and a little JavaScript can
 * answer, simple or dependent, your call), and then, since this lesson is
 * also about evaluating what an agent's code produces, write your own quick
 * eval check that judges whether the agent's answer looks right. There's no
 * single right question or eval method here, that's the point.
 *
 * WHAT YOU FILL IN
 *   TODO 1: write your own natural-language question about the Chinook
 *     database (see the schema hints in SYSTEM below) for the interpreter
 *     agent to answer using eval() and queryChinook.
 *   TODO 2: write a small evalAnswer(...) function that independently
 *     checks whether the agent's final answer looks correct. However you
 *     want to do this is fine: run your own SQL query and compare, check
 *     for an expected keyword or number, or just print both side by side
 *     for your own judgment call. Pick whatever level of rigor makes sense
 *     for your question.
 *
 * RUN
 *   cd typescript
 *   pnpm tsx ./m2/m2.4_homework.ts
 */

import { randomUUID } from "node:crypto";
import { DatabaseSync } from "node:sqlite";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { z } from "zod";
import { context, tool } from "langchain";
import { createDeepAgent } from "deepagents";
import { createCodeInterpreterMiddleware } from "@langchain/quickjs";

import { model } from "../models.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const DB_PATH = join(__dirname, "chinook.db");

const SYSTEM = context`
  You are a sales analyst for Chinook Digital Music Store.
  Use the query_chinook tool to query the database.
  Key tables: Artist(ArtistId, Name), Album(AlbumId, Title, ArtistId),
  Track(TrackId, Name, AlbumId, GenreId), Genre(GenreId, Name),
  Customer(CustomerId, FirstName, LastName, Country),
  Invoice(InvoiceId, CustomerId),
  InvoiceLine(InvoiceLineId, InvoiceId, TrackId, UnitPrice, Quantity).
  Revenue is InvoiceLine.UnitPrice * InvoiceLine.Quantity.
  The eval tool supports Programmatic Tool Calling (PTC): JavaScript
  running inside eval() can call query_chinook via tools.queryChinook().`;

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

// ════════════════════════════════════════════════════════════════════════
// TODO 1: Write your own question about the Chinook database.
//
// Pick anything the queryChinook tool can answer: top customers by
// country, which artist has the most albums, average invoice total by
// year, whatever you're curious about. A question with a couple of
// dependent steps (like Lab 2's) is a good excuse to use PTC, but a
// single-query question is a perfectly fine answer too.
// ════════════════════════════════════════════════════════════════════════

const TASK: string | null = null; // TODO 1: replace with your own question

// ════════════════════════════════════════════════════════════════════════
// TODO 2: Write a simple eval check for the agent's answer.
//
// evalAnswer(answerText) runs after the agent responds. Independently
// work out what you believe the right answer is (run your own SQL query,
// do the math by hand, whatever) and compare it against answerText. Print
// whatever verdict makes sense; this doesn't need to be a strict
// pass/fail, a reasoned printout is fine.
// ════════════════════════════════════════════════════════════════════════

function evalAnswer(answerText: string): void {
  throw new Error("TODO 2: see the comment block above");
}

if (TASK === null) {
  throw new Error("TODO 1: see the comment block above");
}

const agent = createDeepAgent({
  model,
  tools: [queryChinook],
  middleware: [createCodeInterpreterMiddleware({ ptc: ["query_chinook"] })],
  systemPrompt: SYSTEM,
});

const result = await agent.invoke(
  { messages: [{ role: "user", content: TASK }] },
  { configurable: { thread_id: randomUUID() } }
);

const answer = String(result.messages.at(-1)?.content ?? "");
console.log(answer);
evalAnswer(answer);
