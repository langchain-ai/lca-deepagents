// typescript/m3/m3.2_scratch_agent_skills.ts
import { dirname } from "node:path";
import { fileURLToPath } from "node:url";

import { context } from "langchain";
import { createDeepAgent, FilesystemBackend } from "deepagents";

import { model } from "../models.js";

const m3Dir = dirname(fileURLToPath(import.meta.url));
const backend = new FilesystemBackend({ rootDir: m3Dir, virtualMode: true });

const agent = createDeepAgent({
  model,
  name: "Sales_Assistant",
  backend,
  skills: ["/skills"],
  systemPrompt: "You are a sales assistant.",
});

const result = await agent.invoke({
  messages: [
    {
      role: "user",
      content: context`
        Qualify this lead: Acme Corp, 200-person logistics company. I spoke with
        Sarah Chen, VP of Sales: she's the decision maker. They have $45k budgeted
        for CRM this year. Main pain: deals are slipping through the cracks due to
        poor pipeline visibility. They want a solution live by end of Q3.`,
    },
  ],
});

console.log(result.messages.at(-1)?.content);
