// typescript/m3/m3.3_memory_agent.ts
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

// createFileData is a helper function to create a FileData object.
function createFileData(content: string): FileData {
  const now = new Date().toISOString();
  return { content, mimeType: "text/markdown", created_at: now, modified_at: now };
}

const store = new InMemoryStore();
const memoryPath = "/memories/AGENTS.md";
const storeMemoryPath = "/AGENTS.md";
const demoContext = { workspace_id: "acme", user_id: "u_alex" };

function namespaceFromContext(context: { workspace_id: string; user_id: string }): string[] {
  return ["memory", context.workspace_id, context.user_id];
}

// StoreBackend's namespace factory only has access to the runnable config (not the
// LangGraph "context" object directly), so workspace_id/user_id are threaded through
// via `configurable`.
function memoryNamespace(context: StoreBackendContext): string[] {
  const configurable = (context.config?.configurable ?? {}) as {
    workspace_id: string;
    user_id: string;
  };
  return namespaceFromContext(configurable);
}

await store.put(
  namespaceFromContext(demoContext),
  storeMemoryPath,
  createFileData(`# Project Guidelines

## Code Style
- All functions must have type annotations
- Use f-strings for string formatting
- Maximum line length is 88 characters
- Use \`pathlib.Path\` for file operations, not \`os.path\`

## Workflow
- Run tests with: \`uv run pytest\`
- The CI pipeline runs on every push to \`main\`
- Open a draft PR early so reviewers can follow along
`)
);

const agent = createDeepAgent({
  model,
  name: "Memory_Agent",
  backend: new CompositeBackend(new StateBackend(), {
    "/memories/": new StoreBackend({ namespace: memoryNamespace }),
  }),
  store,
  memory: [memoryPath],
  systemPrompt: "You are a helpful coding assistant for this project.",
});

const demoConfig = { configurable: demoContext };

// First invoke: agent answers using memory content
const result = await agent.invoke(
  {
    messages: [
      { role: "user", content: "What tool should I use for file paths in this project?" },
    ],
  },
  demoConfig
);
console.log("--- Question 1 ---");
console.log(result.messages.at(-1)?.content);

// Second invoke: agent writes to memory
const result2 = await agent.invoke(
  {
    messages: [
      {
        role: "user",
        content: "Remember: the team switched to ruff for linting. Update your memory.",
      },
    ],
  },
  demoConfig
);
console.log("\n--- Question 2 ---");
console.log(result2.messages[result2.messages.length - 1].content);

console.log("\n--- AGENTS.md after write ---");
const storedMemory = await store.get(namespaceFromContext(demoContext), storeMemoryPath);
console.log((storedMemory!.value as FileData).content);
