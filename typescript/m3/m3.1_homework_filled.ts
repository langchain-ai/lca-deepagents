// typescript/m3/m3.1_homework_filled.ts
/**
 * Reference copy of m3.1_homework.ts with TODOs 1 and 2 filled in so you
 * can run it end to end and see what "done" looks like. This is just one
 * possible answer, so yours might be different. Explore!
 */

import { createDeepAgent } from "deepagents";
import { HumanMessage } from "langchain";
import { MemorySaver } from "@langchain/langgraph";

import { model } from "../models.js";

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
  checkpointer: new MemorySaver(),
  systemPrompt: "You are a helpful assistant. Keep every response to one sentence.",
});

const THREAD = { configurable: { thread_id: "homework" } };

interface SummarizationEvent {
  cutoffIndex?: number;
}

interface FileData {
  content?: string | string[];
}

interface AgentStateValues {
  messages?: unknown[];
  _summarizationEvent?: SummarizationEvent;
  _summarizationSessionId?: string;
  files?: Record<string, FileData | string>;
}

function fileContentToString(file: FileData | string): string {
  const content = typeof file === "string" ? file : file.content;
  if (Array.isArray(content)) return content.join("\n");
  return content ?? "";
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
  const historyFile = historyPath ? state.values.files?.[historyPath] : undefined;
  if (historyFile) {
    const content = fileContentToString(historyFile);
    const sections = content.split("## Summarized at").length - 1;
    console.log(`\n--- ${historyPath} (${sections} section(s)) ---`);
    console.log(content);
  } else if (historyPath) {
    // Some deepagents versions don't yet surface the summarization
    // middleware's backend offload in state.files for the default
    // StateBackend; that's a package limitation, not a bug in this script.
    console.log(
      `\nNo offloaded history file found at ${historyPath} in state.files ` +
      "(this is a known gap in some deepagents versions, not a bug in your code)."
    );
  }
}

await main();
