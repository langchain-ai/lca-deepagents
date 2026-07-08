// typescript/m5/sales_assistant/tools/sql.ts
/**
 * SQL tools for the chinook-analyst subagent.
 *
 * Three tools, with the database's trust boundary baked in:
 *
 * - queryChinook — read-only SELECTs. The connection is opened via
 *   node:sqlite's genuine read-only mode AND the statement is checked to be a
 *   single SELECT, so a model-generated query can never mutate or drop
 *   anything.
 * - introspectSchema — returns the full DDL so the analyst can learn (and
 *   then memorize) the schema on first use.
 * - addCustomer — the one write path: a parameterized INSERT into Customer
 *   only, scoped to the logged-in rep. It is gated by a human-in-the-loop
 *   approval (configured where the subagent is built), so no row is added
 *   without an explicit yes.
 *
 * Model-generated SQL is treated as untrusted input throughout.
 */
import { DatabaseSync } from "node:sqlite";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { tool } from "@langchain/core/tools";
import { z } from "zod";

const __dirname = dirname(fileURLToPath(import.meta.url));
// The database ships with the agent under data/.
const DB_PATH = join(__dirname, "..", "data", "chinook.db");

// The persona: Jane Peacock, Sales Support Agent. "My customers" = SupportRepId.
const REP_EMPLOYEE_ID = 3;

// Statements that may not appear in a read-only query, as defense in depth on
// top of the read-only connection.
const FORBIDDEN = [
  "insert", "update", "delete", "drop", "alter", "create",
  "replace", "truncate", "attach", "detach", "pragma", "vacuum",
];

export const queryChinook = tool(
  ({ sql }: { sql: string }) => {
    const stripped = sql.trim().replace(/;$/, "").trim();
    const lowered = stripped.toLowerCase();

    if (!lowered.startsWith("select") && !lowered.startsWith("with")) {
      return JSON.stringify({ error: "Only SELECT queries are allowed." });
    }
    if (stripped.includes(";")) {
      return JSON.stringify({ error: "Only a single statement is allowed." });
    }
    const padded = ` ${lowered} `;
    if (FORBIDDEN.some((word) => padded.includes(` ${word} `))) {
      return JSON.stringify({ error: "Query contains a forbidden (write) keyword." });
    }

    const db = new DatabaseSync(DB_PATH, { readOnly: true });
    try {
      const rows = db.prepare(stripped).all();
      return JSON.stringify(rows);
    } catch (exc) {
      return JSON.stringify({ error: `SQL error: ${(exc as Error).message}` });
    } finally {
      db.close();
    }
  },
  {
    name: "query_chinook",
    description:
      "Run a read-only SQL SELECT against the Chinook database. Returns a " +
      "JSON array of row objects. Only a single SELECT statement is allowed " +
      "— any attempt to modify the database is rejected. Use this for all " +
      "lookups: catalogue prices, a customer's purchase history, territory " +
      "metrics, and so on.",
    schema: z.object({ sql: z.string() }),
  }
);

export const introspectSchema = tool(
  () => {
    const db = new DatabaseSync(DB_PATH, { readOnly: true });
    try {
      const rows = db
        .prepare(
          "SELECT name, sql FROM sqlite_master " +
            "WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        .all() as { name: string; sql: string | null }[];
      return rows
        .filter((r) => r.sql)
        .map((r) => r.sql)
        .join("\n\n");
    } finally {
      db.close();
    }
  },
  {
    name: "introspect_schema",
    description:
      "Return the full database schema (CREATE statements for every table). " +
      "Call this once to learn the schema, then record it in your memory so " +
      "you don't have to rediscover it on every task.",
    schema: z.object({}),
  }
);

export const addCustomer = tool(
  ({
    firstName,
    lastName,
    email,
    company,
    city,
    state,
    country,
    phone,
  }: {
    firstName: string;
    lastName: string;
    email: string;
    company: string;
    city: string;
    state: string;
    country: string;
    phone: string;
  }) => {
    if (!email || !email.includes("@")) {
      return JSON.stringify({ error: "A valid email is required." });
    }

    // Parameterized insert into Customer only. No other table is reachable
    // and the rep assignment is forced server-side, not taken from the model.
    const db = new DatabaseSync(DB_PATH);
    try {
      const existing = db
        .prepare("SELECT CustomerId FROM Customer WHERE lower(Email) = lower(?)")
        .get(email) as { CustomerId: number } | undefined;
      if (existing) {
        return JSON.stringify({
          error: `Customer with email ${email} already exists (CustomerId ${existing.CustomerId}).`,
        });
      }

      const info = db
        .prepare(
          `INSERT INTO Customer
            (FirstName, LastName, Company, City, State, Country, Phone, Email, SupportRepId)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`
        )
        .run(
          firstName,
          lastName,
          company || null,
          city || null,
          state || null,
          country || null,
          phone || null,
          email,
          REP_EMPLOYEE_ID
        );
      return JSON.stringify({
        status: "created",
        customer_id: info.lastInsertRowid,
        name: `${firstName} ${lastName}`,
        email,
      });
    } catch (exc) {
      return JSON.stringify({ error: `SQL error: ${(exc as Error).message}` });
    } finally {
      db.close();
    }
  },
  {
    name: "add_customer",
    description:
      "Add a NEW customer to the database, assigned to the current sales " +
      "rep. Use this only after confirming the customer is not already in " +
      "the system (search by email or name first). A human approves this " +
      "write before it runs. Returns the new CustomerId on success.",
    schema: z.object({
      firstName: z.string(),
      lastName: z.string(),
      email: z.string(),
      company: z.string().default(""),
      city: z.string().default(""),
      state: z.string().default(""),
      country: z.string().default(""),
      phone: z.string().default(""),
    }),
  }
);
