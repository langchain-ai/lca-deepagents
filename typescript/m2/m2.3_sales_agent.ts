// typescript/m2/m2.3_sales_agent.ts
import { randomUUID } from "node:crypto";
import { dirname, join } from "node:path";
import { writeFileSync } from "node:fs";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

import { context } from "langchain";
import { LangSmithSandbox, createDeepAgent } from "deepagents";
import { SandboxClient } from "langsmith/sandbox";

import { model } from "../models.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const DB_PATH = join(__dirname, "chinook.db");

const client = new SandboxClient();
const ls_sandbox = await client.createSandbox({
  name: `lca-deepagents-lab-${randomUUID().slice(0, 8)}`,
});
console.log(`Sandbox: ${ls_sandbox.name}  (id: ${ls_sandbox.id})`);

const backend = new LangSmithSandbox({ sandbox: ls_sandbox });

// Upload the Chinook database into the sandbox.
const dbBytes = await readFile(DB_PATH);
const uploadResults = await backend.uploadFiles([["/chinook.db", dbBytes]]);

for (const result of uploadResults) {
  if (result.error) {
    throw new Error(`Failed to upload ${result.path}: ${result.error}`);
  }
}

const agent = createDeepAgent({
  model,
  backend,
  systemPrompt: context`
    You are a sales data analyst with access to the Chinook music store database
    at /chinook.db. Use sqlite3 and matplotlib to answer questions with charts.
    Install any packages you need with pip before importing them.
    When asked to produce a chart, write a Python script, execute it, and confirm
    the output file was created.`,
});

try {
  const result = await agent.invoke({
    messages: [
      {
        role: "user",
        content: context`
          Query the Chinook database at /chinook.db to get total revenue
          by genre. Create a clean donut chart showing each genre's share
          of total sales revenue. Group any genres that individually
          account for less than 3% of total revenue into a single 'Other'
          slice. Label each slice with the genre name and percentage.
          Use a visually distinct color palette, leave a white center hole,
          and make sure no labels overlap with each other or with the title.
          Add enough top padding so the title is fully visible.
          Save the chart to /genre_revenue.png.`,
      },
    ],
  });
  console.log(result.messages.at(-1)?.content);

  const pngBytes = await ls_sandbox.read("/genre_revenue.png");
  const outPath = join(__dirname, "genre_revenue.png");
  writeFileSync(outPath, pngBytes);
  console.log(`Chart saved to ${outPath}`);
} finally {
  await client.deleteSandbox(ls_sandbox.name);
}
