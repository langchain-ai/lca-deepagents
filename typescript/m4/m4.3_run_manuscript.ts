// typescript/m4/m4.3_run_manuscript.ts
/**
 * Run the manuscript agent, then self-check its findings against the known
 * seeded corruptions in data/epic_corpus_key.json — an immediate, exact way to
 * see whether the workflow's book-by-book dispatch actually covered everything.
 *
 * This check is for your own feedback while working through the lab, not a
 * submitted grade — the key ships openly alongside the corpus.
 */

import { dirname, join } from "node:path";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { agent } from "./m4_3_manuscript_agent.js";

const DATA_DIR = join(dirname(fileURLToPath(import.meta.url)), "data");

const result = await agent.invoke(
  {
    messages: [{
      role: "user",
      content: "Run a workflow to find every corrupted sentence in the manuscript.",
    }],
  },
  { recursionLimit: 200 }
);

const report = result.messages.at(-1)?.content as string;
console.log(report);

const seeded: { sentence: string }[] = JSON.parse(readFileSync(join(DATA_DIR, "epic_corpus_key.json"), "utf-8"));
const seededSentences = new Set(seeded.map((entry) => entry.sentence));
const foundSentences = new Set([...seededSentences].filter((s) => report.includes(s)));

const missed = [...seededSentences].filter((s) => !foundSentences.has(s));
console.log(`\nSelf-check: ${foundSentences.size}/${seededSentences.size} seeded corruptions appear in the report.`);
if (missed.length) {
  console.log("Missed:");
  for (const s of missed.sort()) {
    console.log(`  - ${s}`);
  }
}

process.exit(0);
