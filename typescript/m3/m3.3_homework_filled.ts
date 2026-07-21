// typescript/m3/m3.3_homework_filled.ts
/**
 * Reference copy of m3.3_homework.ts with TODOs 1 and 2 filled in so you
 * can run it end to end and see what "done" looks like. This is just one
 * possible answer, so yours might be different. Explore!
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

const CONTEXT_A = { workspace_id: "homework", user_id: "u_you" };
const CONTEXT_B = { workspace_id: "homework", user_id: "u_teammate" };

function namespaceFromContext(context: { workspace_id: string; user_id: string }): string[] {
  return ["memory", context.workspace_id, context.user_id];
}

function memoryNamespace(context: StoreBackendContext): string[] {
  const configurable = (context.config?.configurable ?? {}) as {
    workspace_id: string;
    user_id: string;
  };
  return namespaceFromContext(configurable);
}

// TODO 1 filled in
function buildSeedMemoryA(): string {
  return `# Houseplant Notes

## Watering
- The fiddle-leaf fig gets watered every 10 days, not on a fixed weekday;
  check the top inch of soil first.
- The succulents on the windowsill only get watered when the soil is
  completely dry, roughly every 2-3 weeks.

## Light
- The pothos and snake plant tolerate low light and live in the hallway.
- Everything else needs the south-facing window.
`;
}

function buildSeedMemoryB(): string {
  return `# Herb Garden Notes

## Watering
- Basil and mint want consistently moist soil; check daily in summer.
- Rosemary is drought-tolerant; only water when the top two inches are dry.

## Light
- All three herbs live on the kitchen windowsill, which gets morning sun.
`;
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

// TODO 2 filled in
const RECALL_QUESTION =
  "How often should I water the fiddle-leaf fig, and where does the pothos live?";
const REMEMBER_MESSAGE =
  "Remember: I just repotted the fiddle-leaf fig, so skip watering it for " +
  "the next 3 weeks while the roots settle. Update your memory.";
const LEAK_CHECK_QUESTION =
  "How often should I water the fiddle-leaf fig, and where does the pothos live?";

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
