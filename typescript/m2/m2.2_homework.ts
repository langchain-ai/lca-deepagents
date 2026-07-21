// typescript/m2/m2.2_homework.ts
/**
 * M2.2 Homework: Configure Your Own Filesystem Backend.
 *
 * THE IDEA
 * The lab wired up one fixed setup: a CompositeBackend routing a single
 * reference file to local disk with a permission rule denying all writes
 * to it. This homework asks you to pick your own small file-based task
 * and configure a backend for it however you like: StateBackend,
 * FilesystemBackend, or a CompositeBackend mixing both. There's no
 * single right backend or topic here, that's the point. Two students
 * doing this homework could end up with completely different setups.
 *
 * WHAT YOU FILL IN
 *   TODO 1: pick a topic for a small text file (a packing list, a
 *     journal, a recipe box, meeting notes, whatever), seed it with some
 *     starting content the same way the lab pre-populates
 *     reference/chinook-sales.md, and configure ANY backend you like for
 *     the agent to use.
 *   TODO 2: write a task message that has the agent read your file and
 *     then write or edit it in some way, and (optionally) add one or
 *     more FilesystemPermission rules that change what the agent is
 *     allowed to do to it.
 *
 * RUN
 *   cd typescript
 *   pnpm tsx ./m2/m2.2_homework.ts
 */

import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import {
  createDeepAgent,
  type AnyBackendProtocol,
  type FilesystemPermission,
} from "deepagents";

import { model } from "../models.js";

const __dirname = dirname(fileURLToPath(import.meta.url));

// ════════════════════════════════════════════════════════════════════════
// TODO 1: Configure a backend for a topic of your choosing.
//
// Requirements:
//   - Pick a small file-based task: a packing list, a journal, a recipe
//     box, meeting notes, whatever fits your topic.
//   - Create a seed file (or files) with some starting content, the same
//     way the lab pre-populates reference/chinook-sales.md.
//   - Configure ANY backend you like: new StateBackend(),
//     new FilesystemBackend(...), or a new CompositeBackend(...) routing
//     between them. It does not need to match the lab's setup.
//
// Example shape (delete this and write your own):
//   const myDir = join(__dirname, "my_files");
//   mkdirSync(myDir, { recursive: true });
//   writeFileSync(join(myDir, "notes.md"), "...");
//   const backend = new FilesystemBackend({ rootDir: myDir, virtualMode: true });
// ════════════════════════════════════════════════════════════════════════

const backend: AnyBackendProtocol | null = null; // TODO 1: replace with a StateBackend, FilesystemBackend, or CompositeBackend

// ════════════════════════════════════════════════════════════════════════
// TODO 2: Write the task, and optionally a permission rule.
//
// Write a user message that has the agent read your file, then write or
// edit it. If you want to demonstrate permissions, add one or more
// FilesystemPermission rules to the permissions array below. Leaving it
// empty and skipping permissions entirely is also a valid choice.
// ════════════════════════════════════════════════════════════════════════

const TASK: string | null = null; // TODO 2: replace with your own task message
const permissions: FilesystemPermission[] = []; // TODO 2 (optional): add rules here

if (backend === null) {
  throw new Error("TODO 1: see the comment block above");
}
if (TASK === null) {
  throw new Error("TODO 2: see the comment block above");
}

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
