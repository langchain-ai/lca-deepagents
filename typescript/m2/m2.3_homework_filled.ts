// typescript/m2/m2.3_homework_filled.ts
/**
 * Reference copy of m2.3_homework.ts with TODOs 1-3 filled in so you
 * can run it end to end and see what "done" looks like. This is just one
 * possible answer, so yours might be different. Explore!
 */

import { randomUUID } from "node:crypto";
import { dirname, join } from "node:path";
import { writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { LangSmithSandbox, createDeepAgent } from "deepagents";
import { SandboxClient } from "langsmith/sandbox";

import { model } from "../models.js";

const __dirname = dirname(fileURLToPath(import.meta.url));

// TODO 1 filled in
const SYSTEM_PROMPT =
  "You are a data visualization assistant. When asked to run code, " +
  "write the script to a file first, then execute it. Install any " +
  "packages you need with pip before importing them. When asked for " +
  "a chart, use matplotlib and save it as a .png file.";

// TODO 2 filled in
const TASK_ONE =
  "Generate 12 months of made-up monthly rainfall totals (in mm) for " +
  "a fictional city, save them to rainfall.json, and print them.";
const TASK_TWO =
  "Read rainfall.json (don't regenerate the numbers) and create a bar " +
  "chart of monthly rainfall. Save it to /chart.png.";

// TODO 3 filled in
const CHART_PATH = "/chart.png";

const client = new SandboxClient();
const ls_sandbox = await client.createSandbox({
  name: `lca-deepagents-homework-${randomUUID().slice(0, 8)}`,
});
console.log(`Sandbox: ${ls_sandbox.name}  (id: ${ls_sandbox.id})`);
const backend = new LangSmithSandbox({ sandbox: ls_sandbox });

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

  const chartBytes = await ls_sandbox.read(CHART_PATH);
  const outPath = join(__dirname, "homework_chart.png");
  writeFileSync(outPath, chartBytes);
  console.log(`Chart saved to ${outPath}`);
} finally {
  await client.deleteSandbox(ls_sandbox.name);
}
