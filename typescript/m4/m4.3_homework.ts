// typescript/m4/m4.3_homework.ts
/**
 * M4.3 Homework: Write Your Own Dynamic Subagent Workflow.
 *
 * THE IDEA
 * The lab gave the main agent a 2MB manuscript split into labeled books and
 * had it write a "workflow" that dispatched one book-scanner subagent per
 * book, so the full corpus never entered the main model's own context. This
 * homework asks you to do the same shape of thing on a scenario of your own
 * choosing: a synthetic corpus of your own, split into your own labeled
 * sections, and a subagent that scans each section for something other than
 * anachronisms.
 *
 * A few starting points, if you want one:
 *   - A Sherlock Holmes story, split by chapter, scanned for clues the
 *     detective mentions but never actually explains.
 *   - The script of Bee Movie or Shrek, split by scene, scanned for lines
 *     that don't match the character who supposedly says them.
 *   - Your own corrupted classic, like the lab's, but seeded with a
 *     different kind of error: wrong units, swapped character names,
 *     continuity errors between chapters.
 *
 * WHAT YOU FILL IN
 *   TODO 1: write your own corpus, a single string split into at least 5
 *     labeled sections using a consistent header format (like the lab's
 *     "=== EPIC BOOK N ===").
 *   TODO 2: write the section-scanner's system prompt (what should it flag in
 *     one section?) and the main agent's system prompt (telling it to run a
 *     workflow that splits your corpus and dispatches one scanner call per
 *     section).
 *
 * RUN
 *   cd typescript
 *   pnpm tsx ./m4/m4.3_homework.ts
 *
 * NOTE
 *   This uses the code interpreter (@langchain/quickjs), same as the lab.
 *   Make sure you've run `pnpm install` from typescript/ so it's installed.
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

// ════════════════════════════════════════════════════════════════════════
// TODO 1: Write your own corpus.
//
// Requirements:
//   - A single string with at least 5 labeled sections.
//   - Pick a consistent header format, e.g. "=== SECTION N ===" or
//     "=== TICKET N ===", and stick to it exactly: the main agent's prompt
//     (TODO 2) needs to describe the same format so it can split on it.
//   - Plant something worth finding in a few of the sections (an off-topic
//     sentence, a specific keyword, whatever your scanner in TODO 2 is
//     looking for) so there's something for the workflow to actually
//     surface.
//
// Example shape (delete this and write your own):
//   return `=== SECTION 1 ===
//   ...
//
//   === SECTION 2 ===
//   ...
//   `;
// ════════════════════════════════════════════════════════════════════════

function buildCorpus(): string {
  // TODO 1: return your own corpus string with at least 5 sections.
  throw new Error("TODO 1: see the comment block above");
}

writeFileSync(CORPUS_PATH, buildCorpus());

// ════════════════════════════════════════════════════════════════════════
// TODO 2: Write the scanner and main agent prompts.
//
// Return { scannerPrompt, mainPrompt }:
//   - scannerPrompt: what the section-scanner subagent should look for in
//     ONE section it's handed, and what it should return.
//   - mainPrompt: tells the main agent about the corpus file, the header
//     format from TODO 1, and to run a WORKFLOW that splits the corpus and
//     dispatches one scanner call per section (the word "workflow" is what
//     triggers code-based dispatch, see the lesson).
// ════════════════════════════════════════════════════════════════════════

function buildPrompts(): { scannerPrompt: string; mainPrompt: string } {
  // TODO 2: return { scannerPrompt, mainPrompt }.
  throw new Error("TODO 2: see the comment block above");
}

const { scannerPrompt, mainPrompt } = buildPrompts();

const sectionScanner: SubAgent = {
  name: "section-scanner",
  description:
    "Scan one section of the corpus for whatever the scanner prompt " +
    "asks for. Delegate one section per call.",
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
