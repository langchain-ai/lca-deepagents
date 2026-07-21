// typescript/m1/m1.7_homework.ts
/**
 * M1.7 Homework: Design Your Own Multi-Thread Scenario.
 *
 * THE IDEA
 * The lab used one topic (favorite colour) across two threads to show that
 * threadA remembers it and threadB doesn't. This homework asks you to
 * design your own multi-turn scenario and prove three things:
 *   1. that state persists within a thread across separate invoke() calls,
 *   2. that a different thread_id starts with no memory of it, and
 *   3. that this persistence lives in the MemorySaver instance rather than
 *      the thread_id string itself, by asking a brand-new agent with its
 *      own fresh MemorySaver the same question on threadA's thread_id.
 *
 * WHAT YOU FILL IN
 *   TODO 1: pick your own topic/fact for the agent to remember, and set up
 *     two or more of your own thread configs (different thread_ids).
 *   TODO 2: run the turns that demonstrate persistence (same thread
 *     remembers), isolation (a different thread doesn't), and checkpointer
 *     scope (a fresh MemorySaver on the same thread_id doesn't either).
 *
 * RUN
 *   cd typescript
 *   pnpm tsx ./m1/m1.7_homework.ts
 */

import { MemorySaver } from "@langchain/langgraph";
import { createDeepAgent } from "deepagents";

import { model } from "../models.js";

const agent = createDeepAgent({
  model,
  checkpointer: new MemorySaver(),
});

// ════════════════════════════════════════════════════════════════════════
// TODO 1: Pick your own topic and set up two or more thread configs.
//
// Requirements:
//   - Use a topic/fact of your own choosing (not favorite colour, the
//     lab's example).
//   - Define at least two thread configs with different thread_ids, e.g.
//     const threadA = { configurable: { thread_id: "my-thread-a" } };
// ════════════════════════════════════════════════════════════════════════

const threadA = null; // TODO 1: replace with your own thread config
const threadB = null; // TODO 1: replace with your own thread config

// ════════════════════════════════════════════════════════════════════════
// TODO 2: Run the turns that demonstrate persistence, isolation, and
// checkpointer scope.
//
// Requirements:
//   - In threadA, send at least two turns: one that gives the agent your
//     fact, and a later one that asks it back. Print both responses.
//   - In threadB (a different thread_id), ask the same follow-up
//     question with no prior context, and print the response. It should
//     NOT know the fact from threadA.
//   - Build a SECOND agent with its own fresh MemorySaver(), and invoke it
//     on threadA's thread_id, asking the same follow-up question. Print
//     the response and a line explaining why it doesn't know the fact
//     even though the thread_id matches: memory lives in the MemorySaver
//     instance, not in the thread_id string alone.
//
// Example shape for the second agent (delete this and write your own):
//   const freshAgent = createDeepAgent({ model, checkpointer: new MemorySaver() });
//   const result = await freshAgent.invoke(
//     { messages: [{ role: "user", content: "..." }] },
//     threadA
//   );
// ════════════════════════════════════════════════════════════════════════

async function runScenario() {
  // TODO 2: run the multi-turn, multi-thread scenario described above.
  throw new Error("TODO 2: see the comment block above");
}

await runScenario();
