// typescript/m4/m4.2_run_newsletter.ts
/**
 * Run the editor agent and save everything it produces.
 *
 * Note on file handling: Deep Agents *can* be given real local disk access (via a
 * FilesystemBackend), but we deliberately don't. This agent runs on the default
 * StateBackend, so its writes land in agent state, not on your machine. Letting an
 * agent write to your filesystem is a permission you grant — and shouldn't, when
 * the agent is acting on untrusted web-search content. Instead, this trusted host
 * code reads the files out of agent state (the "files" channel) after invoke and
 * mirrors them to OUT_DIR: the finished newsletter plus each researcher's raw
 * /research/<genre>/ archive, so you can inspect what was quarantined there.
 */

import { dirname, join, relative, resolve, sep } from "node:path";
import { mkdirSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import type { FileData } from "deepagents";

import { agent } from "./m4_2_newsletter_agent.js";

const OUT_DIR = join(dirname(fileURLToPath(import.meta.url)), "output");
mkdirSync(OUT_DIR, { recursive: true });

const result = await agent.invoke(
  { messages: [{ role: "user", content: "Put together this week's newsletter." }] },
  { recursionLimit: 50 }
);

// The editor's final reply (coordination summary).
console.log(result.messages.at(-1)?.content);

// Everything the agent produced lives in agent state (not on your disk — it ran
// in the default StateBackend). Pull it all out and mirror it to OUT_DIR: the
// editor's newsletter AND each researcher's raw /research/<genre>/ archive.
const files: Record<string, FileData> = (result as { files?: Record<string, FileData> }).files ?? {};
if (!("/output/newsletter.html" in files)) {
  throw new Error("Agent did not write /output/newsletter.html");
}

// FileData entries are objects keyed by "content" (string, or legacy list).
function _content(fd: FileData): string {
  const body = fd.content;
  if (Array.isArray(body)) return body.join("\n");
  if (typeof body === "string") return body;
  return Buffer.from(body).toString("utf-8");
}

const outRoot = resolve(OUT_DIR);
console.log("\nWriting agent files to disk:");
for (const path of Object.keys(files).sort()) {
  // Map the in-state layout onto OUT_DIR: /output/* lands at the root,
  // /research/<genre>/* keeps its folder structure.
  const rel = path.startsWith("/output/") ? path.slice("/output/".length) : path.replace(/^\/+/, "");
  const dest = resolve(join(OUT_DIR, rel));

  // The file contents are UNTRUSTED web-search text, and the path came from
  // the agent — so verify the destination stays inside OUT_DIR before writing
  // (reject any ../ traversal), and only ever write plain text.
  const insideOutRoot = dest === outRoot || dest.startsWith(outRoot + sep);
  if (!insideOutRoot) {
    console.log(`  SKIPPED (escapes output dir): ${path}`);
    continue;
  }

  mkdirSync(dirname(dest), { recursive: true });
  const body = _content(files[path]);
  writeFileSync(dest, body, "utf-8");
  console.log(`  ${path}  ->  ${relative(outRoot, dest)}  (${body.length.toLocaleString()} chars)`);
}

console.log(`\nOpen ${join(OUT_DIR, "newsletter.html")} in your browser to read this week's issue.`);
