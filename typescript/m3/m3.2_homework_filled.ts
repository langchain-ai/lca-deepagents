// typescript/m3/m3.2_homework_filled.ts
/**
 * Reference copy of m3.2_homework.ts with TODOs 1-3 filled in so you can
 * run it end to end and see what "done" looks like. This is just one
 * possible answer, so yours might be different. Explore!
 */

import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { createDeepAgent, FilesystemBackend } from "deepagents";
import { isAIMessage } from "@langchain/core/messages";

import { model } from "../models.js";

const SKILL_NAME = "plan-a-workout";
const REFERENCE_PATH = `/skills/${SKILL_NAME}/reference.md`;

// TODO 1 filled in
function buildSkillMd(): string {
  return `---
name: plan-a-workout
description: Use when the user wants a structured workout plan for a specific day or goal.
---

# Plan a Workout

Build a single-session workout plan tailored to the user's goal and available time.

**Step 1: Goal**: Ask what the user is training for today (strength, hypertrophy,
endurance, or mobility) if it isn't already clear from their message.

**Step 2: Constraints**: Confirm how much time they have and what equipment is
available (bodyweight only, dumbbells, a full gym).

**Step 3: Look up the numbers**: Before writing sets and reps, read \`reference.md\`
in this skill's directory for the exact sets/reps/rest table for the stated
goal. Do not guess these numbers; they vary by goal and this skill's rubric is
specific about them.

**Step 4: Warm-up**: Always include a 5-minute warm-up appropriate to the goal.

**Step 5: Main block**: Write 4-6 exercises using the sets/reps/rest from
reference.md that fit the stated goal, time, and equipment.

**Step 6: Cool-down**: End with 2-3 minutes of stretching relevant to the muscles
worked.

## Output

Present the plan as a numbered list: warm-up, main block (with sets/reps/rest
per reference.md), then cool-down. Keep the whole plan realistic for the time
the user gave you.
`;
}

// TODO 2 filled in
function buildReferenceMd(): string {
  return `# Sets / Reps / Rest Rubric

Use the row matching the user's stated goal. Do not deviate from these
numbers; they're calibrated for a single 20-30 minute session.

| Goal        | Sets | Reps      | Rest between sets |
|-------------|------|-----------|--------------------|
| Strength    | 4-5  | 4-6       | 90-120 seconds     |
| Hypertrophy | 3-4  | 8-12      | 60-90 seconds      |
| Endurance   | 2-3  | 15-20     | 30-45 seconds      |
| Mobility    | 2-3  | 30-60s hold (not reps) | 15-30 seconds |
`;
}

const tmpRoot = mkdtempSync(join(tmpdir(), "m3_2_homework_"));
const skillDir = join(tmpRoot, "skills", SKILL_NAME);
mkdirSync(skillDir, { recursive: true });
writeFileSync(join(skillDir, "SKILL.md"), buildSkillMd());
writeFileSync(join(skillDir, "reference.md"), buildReferenceMd());

const backend = new FilesystemBackend({ rootDir: tmpRoot, virtualMode: true });
console.log(`Skill files written to: ${skillDir}`);

// TODO 3 filled in
const SYSTEM_PROMPT = "You are Coach Ren, an upbeat but no-nonsense personal " +
  "trainer. Keep your tone encouraging and practical.";
const USER_QUESTION = "I have 30 minutes and just a pair of dumbbells. Give me a workout focused on strength.";

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
