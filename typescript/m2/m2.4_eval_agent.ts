// typescript/m2/m2.4_eval_agent.ts
import { createCodeInterpreterMiddleware } from "@langchain/quickjs";
import { createDeepAgent } from "deepagents";

import { model } from "../models.js";

const agent = createDeepAgent({
  model,
  middleware: [createCodeInterpreterMiddleware()],
});

const result = await agent.invoke({
  messages: [
    {
      role: "user",
      content: "Use the eval tool to compute and return the first 15 Fibonacci numbers.",
    },
  ],
});

console.log(result.messages[result.messages.length - 1].content);
