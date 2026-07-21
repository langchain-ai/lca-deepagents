// typescript/m4/m4.2_homework.ts
/**
 * M4.2 Homework: Give Each Subagent Its Own Scoped Scratch Folder.
 *
 * THE IDEA
 * The lab's genre-researcher subagents each wrote raw search notes to their own
 * assigned /research/<genre>/ folder, kept out of the editor's context by
 * FilesystemPermission scoping: researchers could write under /research/**, the
 * editor could not.
 *
 * This homework asks you to build a small team of 2 subagent types for a
 * domain YOU pick (e.g., trip planning, home renovation), each with its own
 * private, permission-scoped folder under /scratch/<name>/ to stash raw notes
 * in before answering. The harness below wires up the scratch folder, the
 * permissions, and the write-before-answering instruction for you; you just
 * decide who your two subagents are.
 *
 * WHAT YOU FILL IN
 *   TODO 1: for each of the two entries in SUBAGENT_SPECS, fill in "name",
 *     "description" (when the main agent should call it), and "rolePrompt"
 *     (who this subagent is and what its job is). Everything else -- the
 *     scratch folder, the permissions, the instruction to save raw notes
 *     before answering -- is handled for you.
 *   TODO 2: write the main agent's system prompt, telling it which subagent
 *     to call for which part of the job, and a user request that should
 *     trigger delegation to BOTH subagents.
 *
 * RUN
 *   cd typescript
 *   pnpm tsx ./m4/m4.2_homework.ts
 */

import { createDeepAgent, type FilesystemPermission, type SubAgent, type FileData } from "deepagents";

import { model, strongModel } from "../models.js";

const SCRATCH_ROOT = "/scratch";

function scratchPath(subagentName: string): string {
  return `${SCRATCH_ROOT}/${subagentName}/notes.md`;
}

// Scope a subagent to write only under its own scratch folder -- the same
// first-match-wins allow-then-deny pattern the lab used for
// researchPermissions/editorPermissions.
function scratchPermissions(subagentName: string): FilesystemPermission[] {
  return [
    { operations: ["read", "write"], paths: [`${SCRATCH_ROOT}/${subagentName}/**`], mode: "allow" },
    { operations: ["write"], paths: ["/**"], mode: "deny" },
  ];
}

function scratchInstruction(subagentName: string): string {
  return (
    `Before you answer, call write_file on "${scratchPath(subagentName)}" ` +
    "with your raw notes or reasoning. Then give your final answer using " +
    "only the polished result -- do not repeat those raw notes in your reply."
  );
}

interface SubagentSpec {
  name: string;
  description: string;
  rolePrompt: string;
}

function buildSubagents(specs: SubagentSpec[]): SubAgent[] {
  return specs.map((spec) => ({
    name: spec.name,
    description: spec.description,
    systemPrompt: spec.rolePrompt + "\n\n" + scratchInstruction(spec.name),
    permissions: scratchPermissions(spec.name),
  }));
}

// ════════════════════════════════════════════════════════════════════════
// TODO 1: Fill in your two subagents.
//
// For each entry: "name" is the handle the main agent calls it by, kebab-
// case (e.g. "flight-finder"). "description" is how the main agent decides
// which one to use. "rolePrompt" is that subagent's own job description --
// don't mention scratch files or write_file here, that's added for you.
// ════════════════════════════════════════════════════════════════════════

const SUBAGENT_SPECS: SubagentSpec[] = [
  {
    name: "TODO-1-name-1",
    description: "TODO 1: when should the main agent delegate to this one?",
    rolePrompt: "TODO 1: who is this subagent, and what is its job?",
  },
  {
    name: "TODO-1-name-2",
    description: "TODO 1: when should the main agent delegate to this one?",
    rolePrompt: "TODO 1: who is this subagent, and what is its job?",
  },
];

// ════════════════════════════════════════════════════════════════════════
// TODO 2: Write the main agent's system prompt and a triggering request.
//
// MAIN_PROMPT should tell the main agent about each subagent by name and
// when to call it (mirror how EDITOR_PROMPT in the lab named
// genre-researcher and explained the job).
// USER_REQUEST should be a task that should make the main agent delegate to
// BOTH of your subagents.
// ════════════════════════════════════════════════════════════════════════

const MAIN_PROMPT = `TODO 2: replace this with your own main agent system prompt.`;
const USER_REQUEST =
  "TODO 2: replace this with a request that should trigger delegation to both subagents.";

for (const spec of SUBAGENT_SPECS) {
  if (spec.name.startsWith("TODO-1")) {
    throw new Error("TODO 1: see the comment block above");
  }
}
if (MAIN_PROMPT.startsWith("TODO 2") || USER_REQUEST.startsWith("TODO 2")) {
  throw new Error("TODO 2: see the comment block above");
}

const team = buildSubagents(SUBAGENT_SPECS);

// The main agent must never write into any subagent's scratch folder either.
const MAIN_PERMISSIONS: FilesystemPermission[] = [
  { operations: ["write"], paths: [`${SCRATCH_ROOT}/**`], mode: "deny" },
];

const agent = createDeepAgent({
  model: strongModel,
  name: "Homework_Team_Agent",
  systemPrompt: MAIN_PROMPT,
  subagents: team,
  permissions: MAIN_PERMISSIONS,
});

const result = await agent.invoke(
  { messages: [{ role: "user", content: USER_REQUEST }] },
  { recursionLimit: 50 }
);
console.log(result.messages.at(-1)?.content);

const files: Record<string, FileData> = (result as { files?: Record<string, FileData> }).files ?? {};
console.log("\n--- Scratch folder isolation check ---");
for (const spec of SUBAGENT_SPECS) {
  const path = scratchPath(spec.name);
  console.log(`  ${path}: ${path in files ? "found" : "not written (subagent may not have been called)"}`);
}

const scratchFiles = Object.keys(files).filter((p) => p.startsWith(SCRATCH_ROOT + "/"));
const expected = new Set(SUBAGENT_SPECS.map((spec) => scratchPath(spec.name)));
const stray = scratchFiles.filter((p) => !expected.has(p));
if (stray.length > 0) {
  console.log(`  Unexpected scratch files (isolation may have failed): ${JSON.stringify(stray)}`);
} else {
  console.log("  No stray scratch files -- each subagent wrote only to its own folder.");
}
