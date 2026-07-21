// typescript/m2/m2.2_homework_filled.ts
/**
 * Reference copy of m2.2_homework.ts with TODOs 1 and 2 filled in so you
 * can run it end to end and see what "done" looks like. This is just one
 * possible answer, so yours might be different. Explore!
 */

import { dirname, join } from "node:path";
import { mkdirSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import {
  createDeepAgent,
  FilesystemBackend,
  type FilesystemPermission,
} from "deepagents";

import { model } from "../models.js";

const __dirname = dirname(fileURLToPath(import.meta.url));

const recipeDir = join(__dirname, "recipe_box");
mkdirSync(recipeDir, { recursive: true });
writeFileSync(
  join(recipeDir, "grandmas_apple_pie.md"),
  `\
# Grandma's Apple Pie

Ingredients: 6 apples, 1 cup sugar, 2 tbsp cinnamon, double pie crust.
Bake at 375F for 45 minutes.
`
);

// TODO 1 filled in
const backend = new FilesystemBackend({ rootDir: recipeDir, virtualMode: true });

// TODO 2 filled in
const TASK =
  "Read /grandmas_apple_pie.md, then create a new file called " +
  "/weeknight_pasta.md with a simple pasta recipe of your own. Finally, " +
  "try to add a note to /grandmas_apple_pie.md saying 'tested and it's great'.";
const permissions: FilesystemPermission[] = [
  {
    operations: ["write"],
    paths: ["/grandmas_apple_pie.md"],
    mode: "deny",
  },
];

const agent = createDeepAgent({
  model,
  backend,
  permissions,
});

const result = await agent.invoke(
  { messages: [{ role: "user", content: TASK }] },
  { configurable: { thread_id: "homework-m2.2" } }
);

console.log(result.messages.at(-1)?.content);
