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
    "I'm planning a vegetable garden for my backyard this spring, about 200 square feet.",
    "The plot gets full sun until roughly 2pm, then partial shade the rest of the day.",
    "I want to grow tomatoes, bell peppers, and some kind of leafy green, plus strawberries along the border.",
    "My soil test came back at pH 6.8 with low nitrogen, so I bought a balanced organic fertilizer.",
    "I'm also thinking about adding a small drip irrigation line instead of hand-watering every day.",
    "Quick recap: what did I say I wanted to plant, and what's the soil situation?",
  ];
}

// TODO 2 filled in
const MAX_INPUT_TOKENS = 400;

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
