// typescript/m2/m2.2_agent.ts
import { dirname, join } from "node:path";
import { mkdirSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { context } from "langchain";
import {
  CompositeBackend,
  FilesystemBackend,
  StateBackend,
  createDeepAgent,
  type FilesystemPermission,
} from "deepagents";

import { model } from "../models.js";

const __dirname = dirname(fileURLToPath(import.meta.url));

// Set up a read-only reference directory the agent can consult but not modify.
const referenceDir = join(__dirname, "reference");
mkdirSync(referenceDir, { recursive: true });
writeFileSync(
  join(referenceDir, "chinook-sales.md"),
  `\
# Chinook Sales Reference

You are a sales representative for Chinook Digital Music Store.

Responsibilities:
- Look up customer accounts and purchase history
- Recommend music based on genre and artist preferences
- Answer questions about artists, albums, tracks, and invoices
`
);

const agent = createDeepAgent({
  model,
  backend: new CompositeBackend(new StateBackend(), {
    "/reference/": new FilesystemBackend({
      rootDir: referenceDir,
      virtualMode: true,
    }),
  }),
  permissions: [
    {
      operations: ["write"],
      paths: ["/reference/**"],
      mode: "deny",
    } satisfies FilesystemPermission,
  ],
});

const result = await agent.invoke(
  {
    messages: [
      {
        role: "user",
        content: context`
          Read /reference/chinook-sales.md, then add this note to it:
          'Current promotion: 20% off all Jazz albums through end of month.'`,
      },
    ],
  },
  { configurable: { thread_id: "lab-m2.2" } }
);
console.log(result.messages.at(-1)?.text);
