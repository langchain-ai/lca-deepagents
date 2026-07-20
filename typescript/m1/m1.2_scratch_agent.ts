import { createDeepAgent } from "deepagents";

import { model } from "../models.js";

const agent = createDeepAgent({ model });

const result = await agent.invoke({
    messages: [{ role: "user", content: "What is an LLM?" }]
});

console.log(result.messages.at(-1)?.content);
