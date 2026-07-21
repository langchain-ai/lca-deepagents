// typescript/m4/m4.2_homework_filled.ts
/**
 * Reference copy of m4.2_homework.ts with TODOs 1 and 2 filled in so you
 * can run it end to end and see what "done" looks like. This is just one
 * possible answer, so yours might be different. Explore!
 */

import { createDeepAgent, type FilesystemPermission, type SubAgent, type FileData } from "deepagents";

import { model, strongModel } from "../models.js";

const SCRATCH_ROOT = "/scratch";

function scratchPath(subagentName: string): string {
  return `${SCRATCH_ROOT}/${subagentName}/notes.md`;
}

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

// TODO 1 filled in
const SUBAGENT_SPECS: SubagentSpec[] = [
  {
    name: "workout-planner",
    description: "Design a single workout session for a stated goal, time budget, and equipment.",
    rolePrompt:
      "You are a strength and conditioning coach. Given a client's goal, " +
      "available time, and equipment, write one session's workout: a " +
      "short warm-up, 4-6 main exercises with sets/reps, and a cool-down. " +
      "Keep it realistic for the time given.",
  },
  {
    name: "nutrition-advisor",
    description: "Suggest meal structure and food swaps that support a stated fitness goal.",
    rolePrompt:
      "You are a sports nutrition advisor. Given a client's goal " +
      "(strength, endurance, weight loss, etc.) and any dietary " +
      "restrictions they mention, suggest a simple daily meal structure " +
      "(not a rigid meal plan) and 2-3 concrete food swaps that support " +
      "that goal.",
  },
];

// TODO 2 filled in
const MAIN_PROMPT = `You are Coach, the lead of a small fitness coaching team.
For any client request, delegate to your specialists using the task tool:
- workout-planner for the actual exercises
- nutrition-advisor for food and meal guidance

Delegate to both if the request touches both areas. Collect their responses
and present one combined, friendly plan to the client.`;

const USER_REQUEST =
  "I'm training for a half marathon in 8 weeks. I run 3 days a week and want " +
  "a strength workout for one of my non-running days, plus advice on what to " +
  "eat on run days versus rest days.";

const team = buildSubagents(SUBAGENT_SPECS);

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
