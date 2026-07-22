// typescript/m3/m3.1_homework_filled.ts
/**
 * Reference copy of m3.1_homework.ts with TODOs 1 and 2 filled in so you
 * can run it end to end and see what "done" looks like. This is just one
 * possible answer, so yours might be different. Explore!
 */

import { existsSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { createDeepAgent, FilesystemBackend } from "deepagents";
import { HumanMessage } from "langchain";
import { MemorySaver } from "@langchain/langgraph";

import { model } from "../models.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const historyDir = join(__dirname, "m3.1_history");

// TODO 1 filled in
function buildTurns(): string[] {
  return [
    "I'm planning a two-week trip to Japan in April, starting in Tokyo.",
    "My total budget is $4,000 including flights.",
    "What is 2 + 2?",
    "I want to see cherry blossoms and visit at least one hot spring town.",
    "What is the capital of Italy?",
    "For the middle week I'm thinking Kyoto and Osaka by train.",
    "What is 12 times 12?",
    "I booked a JR rail pass already for the Tokyo-Kyoto-Osaka leg.",
    "What is the capital of Germany?",
    "Quick recap: what's my total budget, and what's the very first city I said I'd start in?",
  ];
}

// TODO 2 filled in
const MAX_INPUT_TOKENS = 3000;

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
