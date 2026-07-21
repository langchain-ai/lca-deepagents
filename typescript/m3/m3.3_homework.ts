// typescript/m3/m3.3_homework.ts
/**
 * M3.3 Homework: Give Your Agent Its Own Memory.
 *
 * THE IDEA
 * The lab used CompositeBackend + StoreBackend to give a coding assistant
 * long-term memory scoped to a workspace and user, seeded with project
 * guidelines, then had the agent recall and later update that memory. This
 * homework asks you to do the same thing for a fact or preference YOU choose,
 * in a domain that has nothing to do with coding conventions (a hobby, a
 * household routine, a running project, whatever you're into). There's no
 * single correct fact to remember here, that's the point. Two students doing
 * this homework could end up remembering two completely different things.
 *
 * WHAT YOU FILL IN
 *   TODO 1: write the seed content for /memories/AGENTS.md, a starting fact
 *     or set of facts in a domain of your choosing.
 *   TODO 2: write two things: a question that should be answerable from your
 *     seeded memory alone, and a "remember this" message that introduces a
 *     NEW fact the agent should persist by editing memory.
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
const demoContext = { workspace_id: "homework", user_id: "u_you" };

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
// TODO 1: Write the seed memory content.
//
// Pick a domain that's genuinely yours (not coding style guidelines): a
// recipe you always tweak the same way, a reading list with your own rating
// system, a plant-watering schedule, a training log, anything with a few
// concrete facts or preferences worth remembering across sessions.
//
// Example shape (delete this and write your own):
//   return `# <Your Domain> Notes
//
//   ## <Section>
//   - <fact 1>
//   - <fact 2>
//   `;
// ════════════════════════════════════════════════════════════════════════

function buildSeedMemory(): string {
  // TODO 1: return the starting content for /memories/AGENTS.md.
  throw new Error("TODO 1: see the comment block above");
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

// ════════════════════════════════════════════════════════════════════════
// TODO 2: Write your two prompts.
//
// RECALL_QUESTION should be answerable directly from buildSeedMemory().
// REMEMBER_MESSAGE should ask the agent to remember one NEW fact that isn't
// in the seed, and to update its memory.
// ════════════════════════════════════════════════════════════════════════

const RECALL_QUESTION = "TODO 2: replace with a question answerable from your seeded memory.";
const REMEMBER_MESSAGE = "TODO 2: replace with a 'remember this' message introducing a new fact.";

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
