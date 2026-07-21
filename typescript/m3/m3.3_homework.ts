// typescript/m3/m3.3_homework.ts
/**
 * M3.3 Homework: Prove Memory Isolation Between Users.
 *
 * THE IDEA
 * The lab scoped memory to a single fixed workspace_id/user_id and only ever
 * ran the agent under that one context, so isolation between users was
 * described in the lesson's "Scoping memory" section but never actually shown
 * in code. This homework asks you to run the SAME agent under two different
 * contexts that share a workspace but belong to different users, seed each
 * with different facts, and confirm a detail you tell the agent to remember
 * under context A never leaks into what the agent says or stores under
 * context B.
 *
 * WHAT YOU FILL IN
 *   TODO 1: write two DIFFERENT seed memories, one for CONTEXT_A and one for
 *     CONTEXT_B, in a domain of your choosing (not coding conventions). Both
 *     should be about the same general topic so a leak would be obvious if
 *     it happened, but with different specifics.
 *   TODO 2: write three prompts: a question answerable from A's seed alone, a
 *     "remember this" message that adds a new, distinctive fact under
 *     context A, and the SAME question asked again but under context B (it
 *     should get B's own answer, or no answer, never A's).
 *
 * RUN
 *   cd typescript
 *   pnpm tsx ./m3/m3.3_homework.ts
 */

import {
  createDeepAgent,
  CompositeBackend,
  StateBackend,
  StoreBackend,
  type FileData,
  type StoreBackendContext,
} from "deepagents";
import { InMemoryStore } from "@langchain/langgraph";

import { model } from "../models.js";

// deepagents does not export create_file_data, so build the FileDataV2 shape by hand.
function createFileData(content: string): FileData {
  const now = new Date().toISOString();
  return { content, mimeType: "text/markdown", created_at: now, modified_at: now };
}

const store = new InMemoryStore();
const memoryPath = "/memories/AGENTS.md";
const storeMemoryPath = "/AGENTS.md";

// Same workspace, two different users -- this is the scoping pattern the
// lesson warns can leak private memories between users if done wrong.
const CONTEXT_A = { workspace_id: "homework", user_id: "u_you" };
const CONTEXT_B = { workspace_id: "homework", user_id: "u_teammate" };

function namespaceFromContext(context: { workspace_id: string; user_id: string }): string[] {
  return ["memory", context.workspace_id, context.user_id];
}

// StoreBackend's namespace factory only has access to the runnable config (not the
// LangGraph "context" object directly), so workspace_id/user_id are threaded through
// via `configurable` rather than Python's `runtime.context`.
function memoryNamespace(context: StoreBackendContext): string[] {
  const configurable = (context.config?.configurable ?? {}) as {
    workspace_id: string;
    user_id: string;
  };
  return namespaceFromContext(configurable);
}

// ════════════════════════════════════════════════════════════════════════
// TODO 1: Write two different seed memories.
//
// Pick a domain that's genuinely yours (not coding style guidelines): a
// recipe, a reading list, a plant-watering schedule, a training log. Write
// ONE version for CONTEXT_A (you) and a DIFFERENT version for CONTEXT_B (a
// teammate), same general topic, different specifics.
//
// Example shape (delete this and write your own):
//   function buildSeedMemoryA(): string {
//     return `# <Your Domain> Notes
//     - <fact 1>
//     `;
//   }
//   function buildSeedMemoryB(): string {
//     return `# <Your Domain> Notes (teammate's)
//     - <a different fact>
//     `;
//   }
// ════════════════════════════════════════════════════════════════════════

function buildSeedMemoryA(): string {
  // TODO 1: return CONTEXT_A's starting memory content.
  throw new Error("TODO 1: see the comment block above");
}

function buildSeedMemoryB(): string {
  // TODO 1: return CONTEXT_B's starting memory content.
  throw new Error("TODO 1: see the comment block above");
}

await store.put(
  namespaceFromContext(CONTEXT_A),
  storeMemoryPath,
  createFileData(buildSeedMemoryA())
);
await store.put(
  namespaceFromContext(CONTEXT_B),
  storeMemoryPath,
  createFileData(buildSeedMemoryB())
);

const agent = createDeepAgent({
  model,
  name: "Homework_Memory_Agent",
  backend: new CompositeBackend(new StateBackend(), {
    "/memories/": new StoreBackend({ namespace: memoryNamespace }),
  }),
  store,
  memory: [memoryPath],
  systemPrompt: "You are a helpful personal assistant for this project.",
});

// ════════════════════════════════════════════════════════════════════════
// TODO 2: Write your three prompts.
//
// RECALL_QUESTION: answerable directly from buildSeedMemoryA(), asked
//   under CONTEXT_A.
// REMEMBER_MESSAGE: introduces a NEW, distinctive fact under CONTEXT_A that
//   isn't in either seed (make it specific -- a made-up number or name --
//   so a leak into context B is unmistakable).
// LEAK_CHECK_QUESTION: the SAME question as RECALL_QUESTION, asked again
//   but this time under CONTEXT_B. If isolation holds, the answer should
//   reflect B's own seed, not A's.
// ════════════════════════════════════════════════════════════════════════

const RECALL_QUESTION = "TODO 2: replace with a question answerable from buildSeedMemoryA() alone.";
const REMEMBER_MESSAGE =
  "TODO 2: replace with a 'remember this' message introducing a new, distinctive fact under context A.";
const LEAK_CHECK_QUESTION = "TODO 2: replace with the SAME question as RECALL_QUESTION.";

const configA = { configurable: CONTEXT_A };
const configB = { configurable: CONTEXT_B };

// 1. Context A recalls from its own seed.
const resultA1 = await agent.invoke(
  { messages: [{ role: "user", content: RECALL_QUESTION }] },
  configA
);
console.log("--- Context A, Question 1 ---");
console.log(resultA1.messages.at(-1)?.content);

// 2. Context A learns a new, distinctive fact.
const resultA2 = await agent.invoke(
  { messages: [{ role: "user", content: REMEMBER_MESSAGE }] },
  configA
);
console.log("\n--- Context A, Question 2 (remember) ---");
console.log(resultA2.messages.at(-1)?.content);

// 3. Context B asks the same question. It should NOT see anything from A.
const resultB = await agent.invoke(
  { messages: [{ role: "user", content: LEAK_CHECK_QUESTION }] },
  configB
);
console.log("\n--- Context B, leak-check question ---");
console.log(resultB.messages.at(-1)?.content);

const memoryA = ((await store.get(namespaceFromContext(CONTEXT_A), storeMemoryPath))!
  .value as FileData).content;
const memoryB = ((await store.get(namespaceFromContext(CONTEXT_B), storeMemoryPath))!
  .value as FileData).content;
console.log("\n--- Context A's stored AGENTS.md ---");
console.log(memoryA);
console.log("\n--- Context B's stored AGENTS.md ---");
console.log(memoryB);

if (memoryA === memoryB) {
  console.log("\nISOLATION FAILED: both contexts share identical stored memory.");
} else {
  console.log("\nStored memories differ between contexts, as expected.");
}
