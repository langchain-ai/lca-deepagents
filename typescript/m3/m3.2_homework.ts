// typescript/m3/m3.2_homework.ts
/**
 * M3.2 Homework: Bundle a Reference File Into Your Skill.
 *
 * THE IDEA
 * The lab's two skills (qualify-lead and draft-pitch) are each a single flat
 * SKILL.md file with everything inline. But the lesson also covered a third
 * stage of progressive disclosure: a skill can point to supporting files (a
 * reference doc, a template, a script) that live alongside SKILL.md and that
 * the agent only reads when it actually needs them, instead of stuffing
 * everything into the system prompt up front. This homework asks you to write
 * a skill for a topic or workflow YOU pick (not sales) that bundles a SECOND
 * file with details the agent needs but that aren't in SKILL.md itself, then
 * confirm from the trace that the agent actually called `read_file` on that
 * second file before answering, rather than guessing.
 *
 * WHAT YOU FILL IN
 *   TODO 1: write your own SKILL.md content. It must instruct the agent to
 *     read a `reference.md` file (in the same skill directory) for specific
 *     details it needs, and must NOT restate those details inline. The `name`
 *     field in your frontmatter must exactly match SKILL_NAME below.
 *   TODO 2: write reference.md's content: the specific facts, numbers, or
 *     template your skill's instructions point to and depend on.
 *   TODO 3: write a system prompt and a user question that should activate
 *     your skill.
 *
 * RUN
 *   cd typescript
 *   pnpm tsx ./m3/m3.2_homework.ts
 */

import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { createDeepAgent, FilesystemBackend } from "deepagents";
import { isAIMessage } from "@langchain/core/messages";

import { model } from "../models.js";

// This name becomes the skill's directory name. It must exactly match the
// `name:` field you write in the frontmatter inside buildSkillMd() below.
const SKILL_NAME = "your-skill-name";
const REFERENCE_PATH = `/skills/${SKILL_NAME}/reference.md`;

// ════════════════════════════════════════════════════════════════════════
// TODO 1: Write your own SKILL.md content.
//
// Requirements:
//   - YAML frontmatter with `name` (must equal SKILL_NAME above) and
//     `description` (a specific sentence describing WHEN to use this skill).
//   - Steps that tell the agent to open `reference.md` (in this same skill
//     directory) for the specific details it needs to do the task well.
//   - Do NOT put those details in SKILL.md itself; if the agent could do
//     the task correctly without ever reading reference.md, this doesn't
//     exercise progressive disclosure.
//
// Example shape (delete this and write your own):
//   function buildSkillMd(): string {
//     return `---
//   name: your-skill-name
//   description: Use when the user wants to ...
//   ---
//
//   # Your Skill Title
//
//   **Step 1: ...**: ...
//   **Step 2: ...**: before proceeding, read reference.md in this skill's
//     directory for the exact ... to use. Do not guess these.
//   `;
//   }
// ════════════════════════════════════════════════════════════════════════

function buildSkillMd(): string {
  throw new Error("TODO 1: see the comment block above");
}

// ════════════════════════════════════════════════════════════════════════
// TODO 2: Write reference.md's content.
//
// This should contain the specific facts your SKILL.md pointed to and
// depends on: a rubric, a set of numbers, a template, a checklist. Specific
// enough that an answer produced without reading it would visibly differ
// from one produced with it.
// ════════════════════════════════════════════════════════════════════════

function buildReferenceMd(): string {
  throw new Error("TODO 2: see the comment block above");
}

// Write the skill to a scratch directory so it's discoverable through a
// FilesystemBackend, the same mechanism the lab uses for typescript/m3/skills/.
const tmpRoot = mkdtempSync(join(tmpdir(), "m3_2_homework_"));
const skillDir = join(tmpRoot, "skills", SKILL_NAME);
mkdirSync(skillDir, { recursive: true });
writeFileSync(join(skillDir, "SKILL.md"), buildSkillMd());
writeFileSync(join(skillDir, "reference.md"), buildReferenceMd());

const backend = new FilesystemBackend({ rootDir: tmpRoot, virtualMode: true });
console.log(`Skill files written to: ${skillDir}`);

// ════════════════════════════════════════════════════════════════════════
// TODO 3: Write a system prompt and a triggering question.
//
// SYSTEM_PROMPT: give the agent a persona of your choosing (a name, a
// voice, anything you want).
// USER_QUESTION: a question that should match your skill's `description`
// closely enough that the agent activates it.
// ════════════════════════════════════════════════════════════════════════

const SYSTEM_PROMPT = "TODO 3: replace this with your own system prompt.";
const USER_QUESTION = "TODO 3: replace this with a question that should trigger your skill.";

const agent = createDeepAgent({
  model,
  name: "Homework_Agent",
  backend,
  skills: ["/skills"],
  systemPrompt: SYSTEM_PROMPT,
});

const result = await agent.invoke({
  messages: [{ role: "user", content: USER_QUESTION }],
});

console.log(result.messages.at(-1)?.content);

const readCalls = result.messages
  .filter(isAIMessage)
  .flatMap((msg) => msg.tool_calls ?? [])
  .filter((call) => call.name === "read_file");
const referenceWasRead = readCalls.some((call) => call.args.file_path === REFERENCE_PATH);
console.log(`\n--- Did the agent read ${REFERENCE_PATH}? ${referenceWasRead} ---`);
if (!referenceWasRead) {
  console.log(
    "It didn't. Either SKILL.md isn't clearly telling it to, or the " +
    "task is answerable without the details in reference.md."
  );
}
