// typescript/m3/m3.2_homework_filled.ts
/**
 * Reference copy of m3.2_homework.ts with TODOs 1 and 2 filled in so you
 * can run it end to end and see what "done" looks like. This is just one
 * possible answer, so yours might be different. Explore!
 */

import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { createDeepAgent, FilesystemBackend } from "deepagents";

import { model } from "../models.js";

const SKILL_NAME = "plan-a-workout";

// TODO 1 filled in
function buildSkillMd(): string {
  return `---
name: plan-a-workout
description: Use when the user wants a structured workout plan for a specific day or goal.
---

# Plan a Workout

Build a single-session workout plan tailored to the user's goal and available time.

**Step 1: Goal**: Ask what the user is training for today (strength, endurance,
mobility, or general fitness) if it isn't already clear from their message.

**Step 2: Constraints**: Confirm how much time they have and what equipment is
available (bodyweight only, dumbbells, a full gym).

**Step 3: Warm-up**: Always include a 5-minute warm-up appropriate to the goal.

**Step 4: Main block**: Write 4-6 exercises with sets and reps (or time) that fit
the stated goal, time, and equipment.

**Step 5: Cool-down**: End with 2-3 minutes of stretching relevant to the muscles
worked.

## Output

Present the plan as a numbered list: warm-up, main block (with sets/reps), then
cool-down. Keep the whole plan realistic for the time the user gave you.
`;
}

const tmpRoot = mkdtempSync(join(tmpdir(), "m3_2_homework_"));
const skillDir = join(tmpRoot, "skills", SKILL_NAME);
mkdirSync(skillDir, { recursive: true });
writeFileSync(join(skillDir, "SKILL.md"), buildSkillMd());

const backend = new FilesystemBackend({ rootDir: tmpRoot, virtualMode: true });

// TODO 2 filled in
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
