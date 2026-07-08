// typescript/m5/sales_assistant/mcp/send_to_inbox.ts
/**
 * Drop a message into the mock mailbox — the offline stand-in for "a customer
 * just emailed you."
 *
 * Run with no arguments to load the bundled RFQ fixture(s) from seeds/; or
 * pass --from / --subject / --body to inject a custom message. Either way the
 * new message lands in the inbox and the assistant can find it with
 * mail_list_messages.
 *
 * Examples:
 *   npx tsx mcp/send_to_inbox.ts
 *   npx tsx mcp/send_to_inbox.ts --reset
 *   npx tsx mcp/send_to_inbox.ts --from "a@b.example" \
 *     --subject "Quote please" --body "Can I get 12 Jazz tracks?"
 */
import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { parseArgs } from "node:util";

import { SEEDS_DIR, emptyStore, loadStore, nextId, saveStore } from "./mail_store.js";

const { values } = parseArgs({
  options: {
    from: { type: "string" },
    subject: { type: "string" },
    body: { type: "string" },
    reset: { type: "boolean", default: false },
  },
});

function main(): void {
  if (values.reset) {
    const store = emptyStore();
    const seedFiles = readdirSync(SEEDS_DIR).filter((f) => f.endsWith(".json")).sort();
    for (const seed of seedFiles) {
      store.inbox.push(JSON.parse(readFileSync(join(SEEDS_DIR, seed), "utf-8")));
    }
    saveStore(store);
    console.log(`Mailbox reset. Inbox now has ${store.inbox.length} message(s).`);
    return;
  }

  let store = loadStore();
  if (values.from || values.subject || values.body) {
    const msg = {
      id: nextId(store.inbox, "msg"),
      from: values.from || "unknown@example.com",
      subject: values.subject || "(no subject)",
      date: "2026-06-14T12:00:00Z",
      body: values.body || "",
    };
    store.inbox.push(msg);
    saveStore(store);
    console.log(`Injected ${msg.id} from ${JSON.stringify(msg.from)}.`);
  } else {
    // No custom fields: make sure the seed fixtures are present.
    store = loadStore();
    console.log(`Inbox has ${store.inbox.length} message(s). Use --reset to re-seed.`);
  }
}

main();
