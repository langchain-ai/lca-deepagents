// typescript/m2/m2.3_homework_filled.ts
/**
 * Reference copy of m2.3_homework.ts with TODOs 1 and 2 filled in so you
 * can run it end to end and see what "done" looks like. This is just one
 * possible answer, so yours might be different. Explore!
 */

import { randomUUID } from "node:crypto";

import { LangSmithSandbox, createDeepAgent } from "deepagents";
import { SandboxClient } from "langsmith/sandbox";

import { model } from "../models.js";

const client = new SandboxClient();
const ls_sandbox = await client.createSandbox({
  name: `lca-deepagents-homework-${randomUUID().slice(0, 8)}`,
});
console.log(`Sandbox: ${ls_sandbox.name}  (id: ${ls_sandbox.id})`);
const backend = new LangSmithSandbox({ sandbox: ls_sandbox });

// TODO 1 filled in
const SYSTEM_PROMPT =
  "You are a curious lab assistant who loves quick experiments. When " +
  "asked to run code, write the script to a file first, then execute " +
  "it, and explain what the result means in plain language.";

// TODO 2 filled in
const TASK_ONE =
  "Write a Python script that generates 20 random integers between 1 " +
  "and 100, saves them to numbers.json, and prints the list.";
const TASK_TWO =
  "Read numbers.json (don't regenerate the numbers) and write a second " +
  "script that loads it and prints the mean and max of those numbers.";

const agent = createDeepAgent({
  model,
  backend,
  systemPrompt: SYSTEM_PROMPT,
});

try {
  let result = await agent.invoke({ messages: [{ role: "user", content: TASK_ONE }] });
  console.log("--- Task 1 ---");
  console.log(result.messages.at(-1)?.content);

  result = await agent.invoke({ messages: [{ role: "user", content: TASK_TWO }] });
  console.log("\n--- Task 2 (same sandbox, should see Task 1's file) ---");
  console.log(result.messages.at(-1)?.content);
} finally {
  await client.deleteSandbox(ls_sandbox.name);
}
