// typescript/m3/m3.1_homework.ts
/**
 * M3.1 Homework: Trigger Chained Summarization.
 *
 * THE IDEA
 * In the lesson, you watched SummarizationMiddleware compress a demo
 * conversation ONCE, past the 85% threshold. But summarization doesn't just
 * fire once and stop: on a long enough conversation it fires again, and again
 * each time it re-summarizes the previous summary plus whatever's new since,
 * while the FULL evicted history keeps piling up in a single backend file at
 * /conversation_history/{sessionId}.md (a session ID generated the first time
 * summarization fires on a thread, not the thread_id itself).
 *
 * This homework asks you to build a conversation on a topic you pick that's
 * long enough to trigger summarization AT LEAST TWICE, then confirm two
 * things: the model can still recall a detail from your very first turn
 * (after being compacted multiple times), and the conversation history file
 * on the backend actually accumulated multiple "Summarized at ..." sections
 * instead of losing earlier ones.
 *
 * WHAT YOU FILL IN
 *   TODO 1: write your own list of user turns (at least 8) about a topic YOU
 *     pick. Put an important detail in one of your first two turns, then
 *     keep talking about the topic for several more turns, and end with a
 *     turn that asks the agent to recall that early detail.
 *   TODO 2: choose model.profile.maxInputTokens so summarization fires at
 *     least twice before your last turn, not just once. Tune it by trial
 *     and error, same as the lesson did with 400.
 *
 * RUN
 *   cd typescript
 *   pnpm tsx ./m3/m3.1_homework.ts
 */

import { existsSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { createDeepAgent, FilesystemBackend } from "deepagents";
import { HumanMessage } from "langchain";
import { MemorySaver } from "@langchain/langgraph";

import { model } from "../models.js";

// FilesystemBackend writes to real disk instead of state.files.
const __dirname = dirname(fileURLToPath(import.meta.url));
const historyDir = join(__dirname, "m3.1_history");

// ════════════════════════════════════════════════════════════════════════
// TODO 1: Write your own multi-turn scenario.
//
// Requirements:
//   - At least 8 user turns, all about ONE topic of your choosing.
//   - One of your first two turns should state a concrete detail (a number,
//     a name, a decision).
//   - Your last turn should ask the agent to recall that detail, after
//     several more turns of unrelated follow-up on the same topic.
//
// Example shape (delete this and write your own):
//   function buildTurns(): string[] {
//     return [
//       "I'm planning a two-week trip to ...",
//       "My total budget is ...",
//       ...,
//       ...,
//       ...,
//       "Quick recap: what was my total budget?",
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
// SummarizationMiddleware fire (at 85% of that number) AT LEAST TWICE
// across your conversation from TODO 1, not just once. The lesson used 400
// for a 5-turn demo that fired once; your number depends on how many turns
// you wrote and how long they are. Must use Object.defineProperty, since a
// plain assignment to model.profile won't work.
// ════════════════════════════════════════════════════════════════════════

const MAX_INPUT_TOKENS: number | null = null; // TODO 2: replace null with your chosen threshold

Object.defineProperty(model, "profile", {
  value: { ...model.profile, maxInputTokens: MAX_INPUT_TOKENS },
  configurable: true,
});

const agent = createDeepAgent({
  model,
  backend: new FilesystemBackend({ rootDir: historyDir, virtualMode: true }),
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
  _summarizationSessionId?: string;
}

async function turn(message: string): Promise<unknown> {
  const result = await agent.invoke(
    { messages: [new HumanMessage(message)] },
    THREAD
  );
  return result.messages.at(-1)?.content;
}

async function showState(seenCutoffs: Set<number | string>): Promise<boolean> {
  const state = await (agent.getState as (config: unknown) => Promise<{ values: AgentStateValues }>)(THREAD);
  const messages = state.values.messages ?? [];
  const event = state.values._summarizationEvent;
  console.log(`  stored : ${messages.length} message(s) (raw history, never trimmed)`);
  if (!event) return false;
  const cutoff = event.cutoffIndex ?? "?";
  const isNewEvent = !seenCutoffs.has(cutoff);
  seenCutoffs.add(cutoff);
  const tag = isNewEvent ? "  <-- NEW EVENT" : "";
  console.log(`  model saw : summary + messages[${cutoff}:]  [SUMMARIZED]${tag}`);
  return isNewEvent;
}

async function main(): Promise<void> {
  const turns = buildTurns();
  const seenCutoffs = new Set<number | string>();
  let eventCount = 0;

  for (let i = 0; i < turns.length; i++) {
    const message = turns[i];
    console.log(`\n${"─".repeat(50)}`);
    console.log(`Turn ${i + 1}  User:  ${message}`);
    const response = await turn(message);
    console.log(`Turn ${i + 1}  Agent: ${response}`);
    if (await showState(seenCutoffs)) eventCount++;
  }

  console.log(`\nSummarization fired ${eventCount} time(s) across ${turns.length} turns.`);
  if (eventCount < 2) {
    console.log(
      "That's fewer than 2. Lower MAX_INPUT_TOKENS, or add more turns/detail, " +
      "so it fires again before the conversation ends."
    );
  }

  const state = await (agent.getState as (config: unknown) => Promise<{ values: AgentStateValues }>)(THREAD);
  const sessionId = state.values._summarizationSessionId;
  const historyPath = sessionId ? `/conversation_history/${sessionId}.md` : null;
  const historyFileOnDisk = historyPath ? join(historyDir, historyPath) : null;
  if (historyFileOnDisk && existsSync(historyFileOnDisk)) {
    const content = readFileSync(historyFileOnDisk, "utf8");
    const sections = content.split("## Summarized at").length - 1;
    console.log(`\n--- ${historyPath} (${sections} section(s)) ---`);
    console.log(content);
  } else if (historyPath) {
    console.log(`\nNo offloaded history file found at ${historyFileOnDisk}.`);
  }
}

await main();
