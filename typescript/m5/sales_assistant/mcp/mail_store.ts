// typescript/m5/sales_assistant/mcp/mail_store.ts
/**
 * A tiny JSON-file mailbox shared by the mock Gmail MCP server and the
 * `send_to_inbox` inject CLI.
 *
 * The store is deliberately dumb: one JSON file with two lists, `inbox` and
 * `drafts`. It exists so the course's Gmail features work offline, with no
 * OAuth, while presenting the same tool surface as a real Gmail MCP server
 * (list_messages / read_message / create_draft). Nothing here is
 * Gmail-specific — it is just enough state to demo the assistant.
 *
 * Paths are resolved from this file's location, so the store works no matter
 * what working directory the MCP subprocess is launched from.
 */
import { existsSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));

// The mailbox lives next to this module, under the module's own directory.
export const STORE_PATH = join(__dirname, "mail_store.json");
export const SEEDS_DIR = join(__dirname, "seeds");

export interface MailMessage {
  id: string;
  from: string;
  subject: string;
  date: string;
  body: string;
}

export interface MailDraft {
  id: string;
  to: string;
  subject: string;
  body: string;
}

export interface MailStore {
  inbox: MailMessage[];
  drafts: MailDraft[];
}

export function emptyStore(): MailStore {
  return { inbox: [], drafts: [] };
}

/** Read the mailbox, seeding it from seeds/ on first use. */
export function loadStore(): MailStore {
  if (existsSync(STORE_PATH)) {
    return JSON.parse(readFileSync(STORE_PATH, "utf-8")) as MailStore;
  }

  const store = emptyStore();
  const seedFiles = existsSync(SEEDS_DIR)
    ? readdirSync(SEEDS_DIR).filter((f) => f.endsWith(".json")).sort()
    : [];
  for (const seed of seedFiles) {
    store.inbox.push(JSON.parse(readFileSync(join(SEEDS_DIR, seed), "utf-8")));
  }
  saveStore(store);
  return store;
}

/** Persist the mailbox to disk. */
export function saveStore(store: MailStore): void {
  writeFileSync(STORE_PATH, JSON.stringify(store, null, 2), "utf-8");
}

/** Return the next sequential id like msg-1 / draft-3. */
export function nextId(messages: { id?: string }[], prefix: string): string {
  const n = 1 + messages.filter((m) => String(m.id ?? "").startsWith(prefix)).length;
  return `${prefix}-${n}`;
}
