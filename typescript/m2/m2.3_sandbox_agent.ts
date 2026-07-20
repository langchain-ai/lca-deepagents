// typescript/m2/m2.3_sandbox_agent.ts
import { randomUUID } from "node:crypto";

import { context } from "langchain";
import { LangSmithSandbox, createDeepAgent } from "deepagents";
import { SandboxClient } from "langsmith/sandbox";

import { model } from "../models.js";

const client = new SandboxClient();
const ls_sandbox = await client.createSandbox({
  name: `lca-deepagents-lab-${randomUUID().slice(0, 8)}`,
});
console.log(`Sandbox: ${ls_sandbox.name}  (id: ${ls_sandbox.id})`);
const backend = new LangSmithSandbox({ sandbox: ls_sandbox });

const agent = createDeepAgent({
  model,
  backend,
  systemPrompt: context`
    You are a coding assistant. When asked to run code, write the script
    to a file first, then execute it. Show the output in your final answer.`,
});

try {
  const result = await agent.invoke({
    messages: [
      {
        role: "user",
        content: context`
          Write a Python script that prints the first 15 Fibonacci numbers,
          save it to fib.py, and run it.`,
      },
    ],
  });
  console.log(result.messages.at(-1)?.content);
} finally {
  await client.deleteSandbox(ls_sandbox.name);
}
