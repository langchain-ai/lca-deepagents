// typescript/m3/m3.2_homework.ts
/**
 * M3.2 Homework: Write Your Own Skill.
 *
 * THE IDEA
 * The lab gave a sales assistant two skills (qualify-lead and draft-pitch)
 * written as SKILL.md files that it discovers up front and reads on demand.
 * This homework asks you to write your own skill, for a topic or workflow YOU
 * pick (not sales), and demonstrate an agent activating it. There's no single
 * correct skill topic here, that's the point. Two students doing this
 * homework could end up with two completely different skills and agents.
 *
 * WHAT YOU FILL IN
 *   TODO 1: write your own SKILL.md content, frontmatter and all, for a
 *     workflow of your choosing (planning a workout, reviewing a resume,
 *     triaging a bug report, whatever you're into). The `name` field in your
 *     frontmatter must exactly match SKILL_NAME below.
 *   TODO 2: write a system prompt for the agent and a user question that
 *     should activate your skill (matching your skill's `description`).
 *
 * RUN
 *   cd typescript
 *   pnpm tsx ./m3/m3.2_homework.ts
 */

import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { createDeepAgent, FilesystemBackend } from "deepagents";

import { model } from "../models.js";

// This name becomes the skill's directory name. It must exactly match the
// `name:` field you write in the frontmatter inside buildSkillMd() below.
const SKILL_NAME = "your-skill-name";

// ════════════════════════════════════════════════════════════════════════
// TODO 1: Write your own SKILL.md content.
//
// Requirements:
//   - YAML frontmatter with `name` (must equal SKILL_NAME above) and
//     `description` (a specific sentence describing WHEN to use this skill,
//     not what it does internally).
//   - A body with concrete step-by-step instructions the agent should
//     follow once it activates the skill.
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
//   **Step 2: ...**: ...
//   `;
//   }
// ════════════════════════════════════════════════════════════════════════

function buildSkillMd(): string {
  throw new Error("TODO 1: see the comment block above");
}

// Write the skill to a scratch directory so it's discoverable through a
// FilesystemBackend, the same mechanism the lab uses for typescript/m3/skills/.
const tmpRoot = mkdtempSync(join(tmpdir(), "m3_2_homework_"));
const skillDir = join(tmpRoot, "skills", SKILL_NAME);
mkdirSync(skillDir, { recursive: true });
writeFileSync(join(skillDir, "SKILL.md"), buildSkillMd());

const backend = new FilesystemBackend({ rootDir: tmpRoot, virtualMode: true });

// ════════════════════════════════════════════════════════════════════════
// TODO 2: Write a system prompt and a triggering question.
//
// SYSTEM_PROMPT: give the agent a persona of your choosing (a name, a
// voice, anything you want).
// USER_QUESTION: a question that should match your skill's `description`
// closely enough that the agent activates it.
// ════════════════════════════════════════════════════════════════════════

const SYSTEM_PROMPT = "TODO 2: replace this with your own system prompt.";
const USER_QUESTION = "TODO 2: replace this with a question that should trigger your skill.";

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
