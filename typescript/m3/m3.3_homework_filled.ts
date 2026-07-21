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
const demoContext = { workspace_id: "homework", user_id: "u_you" };

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
function buildSeedMemory(): string {
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

await store.put(
  namespaceFromContext(demoContext),
  storeMemoryPath,
  createFileData(buildSeedMemory())
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

const demoConfig = { configurable: demoContext };

// First invoke: agent answers using memory content
const result = await agent.invoke(
  { messages: [{ role: "user", content: RECALL_QUESTION }] },
  demoConfig
);
console.log("--- Question 1 ---");
console.log(result.messages.at(-1)?.content);

// Second invoke: agent writes to memory
const result2 = await agent.invoke(
  { messages: [{ role: "user", content: REMEMBER_MESSAGE }] },
  demoConfig
);
console.log("\n--- Question 2 ---");
console.log(result2.messages[result2.messages.length - 1].content);

console.log("\n--- AGENTS.md after write ---");
const storedMemory = await store.get(namespaceFromContext(demoContext), storeMemoryPath);
console.log((storedMemory!.value as FileData).content);
