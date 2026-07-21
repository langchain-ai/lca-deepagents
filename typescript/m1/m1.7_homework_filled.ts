// typescript/m1/m1.7_homework_filled.ts
/**
 * Reference copy of m1.7_homework.ts with TODOs 1 and 2 filled in so you
 * can run it end to end and see what "done" looks like. This is just one
 * possible answer, so yours might be different. Explore!
 */

import { MemorySaver } from "@langchain/langgraph";
import { createDeepAgent } from "deepagents";

import { model } from "../models.js";

const agent = createDeepAgent({
  model,
  checkpointer: new MemorySaver(),
});

// TODO 1 filled in
const threadA = { configurable: { thread_id: "m1-7-homework-thread-a" } };
const threadB = { configurable: { thread_id: "m1-7-homework-thread-b" } };

const FACT_QUESTION = "What's my iguana's name and what does he eat?";

// TODO 2 filled in
async function runScenario() {
  let result = await agent.invoke(
    {
      messages: [
        {
          role: "user",
          content:
            "Remember that my pet iguana is named Steve and only eats dandelion greens.",
        },
      ],
    },
    threadA
  );
  console.log("Thread A, turn 1:");
  console.log(result.messages.at(-1)?.content);

  result = await agent.invoke(
    { messages: [{ role: "user", content: FACT_QUESTION }] },
    threadA
  );
  console.log("\nThread A, turn 2 (same thread, should remember Steve):");
  console.log(result.messages.at(-1)?.content);

  result = await agent.invoke(
    { messages: [{ role: "user", content: FACT_QUESTION }] },
    threadB
  );
  console.log("\nThread B, turn 1 (different thread, should NOT know):");
  console.log(result.messages.at(-1)?.content);

  // A brand-new agent with its own fresh MemorySaver has no history to
  // load, even reused on threadA's exact thread_id.
  const freshAgent = createDeepAgent({ model, checkpointer: new MemorySaver() });
  result = await freshAgent.invoke(
    { messages: [{ role: "user", content: FACT_QUESTION }] },
    threadA
  );
  console.log("\nFresh agent, threadA's thread_id (should NOT know):");
  console.log(result.messages.at(-1)?.content);
  console.log(
    "Same thread_id, but a different MemorySaver instance has no record " +
      "of it: persistence is scoped to the checkpointer, not the thread_id " +
      "string alone."
  );
}

await runScenario();
