import { MemorySaver } from "@langchain/langgraph";
import { createDeepAgent } from "deepagents";

import { model } from "../models.js";

const agent = createDeepAgent({
  model,
  checkpointer: new MemorySaver(),
});

const threadA = { configurable: { thread_id: "m1-7-thread-a" } };
const threadB = { configurable: { thread_id: "m1-7-thread-b" } };

let result = await agent.invoke(
  { messages: [{ role: "user", content: "Remember that my favorite color is blue." }] },
  threadA
);
console.log("Thread A, turn 1:");
console.log(result.messages[result.messages.length - 1].content);

result = await agent.invoke(
  { messages: [{ role: "user", content: "What is my favorite color?" }] },
  threadA
);
console.log("\nThread A, turn 2:");
console.log(result.messages[result.messages.length - 1].content);

result = await agent.invoke(
  { messages: [{ role: "user", content: "What is my favorite color?" }] },
  threadB
);
console.log("\nThread B, turn 1:");
console.log(result.messages[result.messages.length - 1].content);
