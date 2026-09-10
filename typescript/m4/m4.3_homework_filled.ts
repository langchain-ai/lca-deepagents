// typescript/m4/m4.3_homework_filled.ts
/**
 * Reference copy of m4.3_homework.ts with TODOs 1 and 2 filled in so you
 * can run it end to end and see what "done" looks like. This is just one
 * possible answer, so yours might be different. Explore!
 */

import { dirname, join } from "node:path";
import { mkdirSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { createDeepAgent, FilesystemBackend, type SubAgent } from "deepagents";
import { createCodeInterpreterMiddleware } from "@langchain/quickjs";

import { model, strongModel } from "../models.js";

const DATA_DIR = join(dirname(fileURLToPath(import.meta.url)), "homework_data");
mkdirSync(DATA_DIR, { recursive: true });
const CORPUS_PATH = join(DATA_DIR, "my_corpus.txt");

// TODO 1 filled in
function buildCorpus(): string {
  return `=== TICKET 1 ===
Customer says the app crashes every time they open the settings page on
Android 14. Includes a screenshot of the error.

=== TICKET 2 ===
Customer was charged twice for their monthly subscription this billing
cycle and wants one of the charges refunded.

=== TICKET 3 ===
Customer is asking how to export their data to a CSV file before they
cancel their account.

=== TICKET 4 ===
Customer's invoice shows a charge for a plan they downgraded from two
months ago; they want the difference refunded.

=== TICKET 5 ===
Customer reports that search results are sorted incorrectly when filtering
by date instead of relevance.

=== TICKET 6 ===
Customer says a promo code was applied but they were still billed the full
price, and they'd like a refund for the discount amount.

=== TICKET 7 ===
Customer wants to know if there's a dark mode planned for the mobile app.
`;
}

writeFileSync(CORPUS_PATH, buildCorpus());

// TODO 2 filled in
function buildPrompts(): { scannerPrompt: string; mainPrompt: string } {
  const scannerPrompt = `You are reviewing one customer support ticket for
billing complaints: any mention of being overcharged, charged twice, billed
the wrong amount, or requesting a refund because of an incorrect charge.

You will be given one ticket's label and its full text.

Return ONLY a JSON object: {"is_billing_complaint": true/false, "summary":
"<one sentence, or empty string if false>"}. If the ticket is not about a
billing problem, return is_billing_complaint: false.`;

  const mainPrompt = `You have access to a support ticket log at
/my_corpus.txt: a set of tickets, each starting with a line formatted
exactly as "=== TICKET N ===".

Run a workflow that reads the file, splits it into its individual tickets,
and dispatches one section-scanner subagent call per ticket — never read a
ticket's full text into your own context; let the interpreter hold the
file, and let each subagent hold only its own ticket. Collect every
subagent's findings into one final report listing only the tickets flagged
as billing complaints, with their one-sentence summaries.`;

  return { scannerPrompt, mainPrompt };
}

const { scannerPrompt, mainPrompt } = buildPrompts();

const sectionScanner: SubAgent = {
  name: "section-scanner",
  description: "Scan one support ticket for billing complaints. Delegate one ticket per call.",
  systemPrompt: scannerPrompt,
  model,
};

export const agent = createDeepAgent({
  model: strongModel,
  middleware: [createCodeInterpreterMiddleware()],
  systemPrompt: mainPrompt,
  subagents: [sectionScanner],
  backend: new FilesystemBackend({ rootDir: DATA_DIR, virtualMode: true }),
});

const result = await agent.invoke(
  {
    messages: [{
      role: "user",
      content: "Run a workflow to scan every section of my_corpus.txt and report what you find.",
    }],
  },
  { recursionLimit: 100 }
);
console.log(result.messages.at(-1)?.content);

// The interpreter's QuickJS runtime can throw during its own async teardown
// after many subagent dispatches (a known @langchain/quickjs beta issue) —
// exit immediately now that the real result above is already printed.
process.exit(0);
