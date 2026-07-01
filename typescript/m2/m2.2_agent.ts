// typescript/m2/m2.2_agent.ts
import { dirname, join } from "node:path";
import { mkdirSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

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

// Note: in Python deepagents, permission errors are returned to the LLM as tool
// messages so it can respond gracefully. In TypeScript deepagents, they surface
// as a thrown MiddlewareError (a langchainjs ReactAgent bug — ToolNode is not
// constructed with handleToolErrors:true). Wrapping here until that is fixed.
try {
  const result = await agent.invoke(
    {
      messages: [
        {
          role: "user",
          content:
            "Read /reference/chinook-sales.md, then add this note to it: " +
            "'Current promotion: 20% off all Jazz albums through end of month.'",
        },
      ],
    },
    { configurable: { thread_id: "lab-m2.2" } }
  );
  console.log(result.messages[result.messages.length - 1].content);
} catch (e: any) {
  console.log("Permission enforced:", e.cause?.message ?? e.message);
}
