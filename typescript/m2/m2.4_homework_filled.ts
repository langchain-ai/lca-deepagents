// typescript/m2/m2.4_homework_filled.ts
/**
 * Reference copy of m2.4_homework.ts with TODOs 1 and 2 filled in so you
 * can run it end to end and see what "done" looks like. This is just one
 * possible answer, so yours might be different. Explore!
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

// TODO 1 filled in
const TASK = context`
  Which country's customers generated the most total revenue, and what
  is the single best-selling track (by revenue) among customers from
  that country? Each answer depends on the previous one.`;

// TODO 2 filled in
function evalAnswer(answerText: string): void {
  const db = new DatabaseSync(DB_PATH);
  let topCountry: { Country: string; rev: number };
  let topTrack: { Name: string; rev: number };
  try {
    topCountry = db
      .prepare(
        `SELECT Customer.Country, SUM(InvoiceLine.UnitPrice * InvoiceLine.Quantity) AS rev
         FROM InvoiceLine
         JOIN Invoice USING(InvoiceId)
         JOIN Customer USING(CustomerId)
         GROUP BY Customer.Country
         ORDER BY rev DESC
         LIMIT 1`
      )
      .get() as { Country: string; rev: number };

    topTrack = db
      .prepare(
        `SELECT Track.Name, SUM(InvoiceLine.UnitPrice * InvoiceLine.Quantity) AS rev
         FROM InvoiceLine
         JOIN Invoice USING(InvoiceId)
         JOIN Customer USING(CustomerId)
         JOIN Track USING(TrackId)
         WHERE Customer.Country = ?
         GROUP BY Track.TrackId
         ORDER BY rev DESC
         LIMIT 1`
      )
      .get(topCountry.Country) as { Name: string; rev: number };
  } finally {
    db.close();
  }

  console.log("\n--- Eval check ---");
  console.log(`Expected top country: ${topCountry.Country}`);
  console.log(`Expected top track: ${topTrack.Name}`);

  const checks: Record<string, boolean> = {
    "mentions expected country": answerText.toLowerCase().includes(topCountry.Country.toLowerCase()),
    "mentions expected track": answerText.toLowerCase().includes(topTrack.Name.toLowerCase()),
  };
  for (const [label, passed] of Object.entries(checks)) {
    console.log(`  [${passed ? "PASS" : "FAIL"}] ${label}`);
  }
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
