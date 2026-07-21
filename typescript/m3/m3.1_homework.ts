// typescript/m3/m3.1_homework.ts
/**
 * M3.1 Homework: Summarize Your Own Long-Running Conversation.
 *
 * THE IDEA
 * The lab watched SummarizationMiddleware compress a short demo conversation
 * (a name, a math question, a project note, and so on) once the context
 * window filled past 85%. This homework asks you to do the same thing on a
 * SCENARIO YOU pick: something with enough substance that talking about it
 * for several turns would plausibly build up real context (planning a trip,
 * outlining a story, debugging a project, prepping for an interview, whatever
 * you're into). There's no single correct topic or turn count here, that's
 * the point. Two students doing this homework could end up with completely
 * different conversations and completely different summarization timing.
 *
 * WHAT YOU FILL IN
 *   TODO 1: write your own list of user turns (at least 5) about a topic YOU
 *     pick. Each turn should read like something a real person would type
 *     across a multi-turn conversation on that topic, with earlier turns
 *     containing details a later turn asks the agent to recall.
 *   TODO 2: choose model.profile.maxInputTokens so that summarization fires
 *     partway through your conversation, not on turn 1 and not so late it
 *     never fires by your last turn. Tune it by trial and error, same as
 *     the lab did with 400.
 *
 * RUN
 *   cd typescript
 *   pnpm tsx ./m3/m3.1_homework.ts
 */

import { createDeepAgent } from "deepagents";
import { HumanMessage } from "langchain";
import { MemorySaver } from "@langchain/langgraph";

import { model } from "../models.js";

// ════════════════════════════════════════════════════════════════════════
// TODO 1: Write your own multi-turn scenario.
//
// Requirements:
//   - At least 5 user turns, all about ONE topic of your choosing (not the
//     lab's "new coworker" chit-chat).
//   - The topic should have enough substance that a real conversation about
//     it would build up context over several turns: earlier turns should
//     contain details that a later turn asks the agent to recall.
//
// Example shape (delete this and write your own):
//   function buildTurns(): string[] {
//     return [
//       "I'm planning a two-week trip to ...",
//       "My budget is ...",
//       ...
//       "Quick recap: what did I say my budget was?",
//     ];
//   }
// ════════════════════════════════════════════════════════════════════════

function buildTurns(): string[] {
  throw new Error("TODO 1: see the comment block above");
}

// ════════════════════════════════════════════════════════════════════════
// TODO 2: Choose the summarization threshold.
//
// Lower model.profile.maxInputTokens to a value that makes
// SummarizationMiddleware fire (at 85% of that number) somewhere in the
// MIDDLE of your conversation from TODO 1, not immediately and not never.
// The lab used 400 for its 5-turn demo; your number depends on how long
// your own turns are. Must use Object.defineProperty, since a plain
// assignment to model.profile won't work.
// ════════════════════════════════════════════════════════════════════════

const MAX_INPUT_TOKENS = null; // TODO 2: replace null with your chosen number threshold

Object.defineProperty(model, "profile", {
  value: { ...model.profile, maxInputTokens: MAX_INPUT_TOKENS },
  configurable: true,
});

const agent = createDeepAgent({
  model,
  checkpointer: new MemorySaver(),
  systemPrompt: "You are a helpful assistant. Keep every response to one sentence.",
});

const THREAD = { configurable: { thread_id: "homework" } };

interface SummarizationEvent {
  cutoffIndex?: number;
}

interface AgentStateValues {
  messages?: unknown[];
  _summarizationEvent?: SummarizationEvent;
}

async function turn(message: string): Promise<unknown> {
  const result = await agent.invoke(
    { messages: [new HumanMessage(message)] },
    THREAD
  );
  return result.messages.at(-1)?.content;
}

async function showState(): Promise<void> {
  const state = await (agent.getState as (config: unknown) => Promise<{ values: AgentStateValues }>)(THREAD);
  const messages = state.values.messages ?? [];
  const event = state.values._summarizationEvent;
  console.log(`  stored : ${messages.length} message(s) (raw history, never trimmed)`);
  if (event) {
    const cutoff = event.cutoffIndex ?? "?";
    console.log(`  model saw : summary + messages[${cutoff}:]  [SUMMARIZED]`);
  }
}

async function main(): Promise<void> {
  const turns = buildTurns();
  for (let i = 0; i < turns.length; i++) {
    const message = turns[i];
    console.log(`\n${"─".repeat(50)}`);
    console.log(`Turn ${i + 1}  User:  ${message}`);
    const response = await turn(message);
    console.log(`Turn ${i + 1}  Agent: ${response}`);
    await showState();
  }
}

await main();
