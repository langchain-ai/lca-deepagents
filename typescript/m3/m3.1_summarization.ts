// typescript/m3/m3.1_summarization.ts
//
// Demonstrates how the built-in SummarizationMiddleware compresses conversation
// history when the context window fills up.
//
// By default the trigger is 85% of the model's real context window (200k tokens
// for Claude Haiku 4.5), which is impractical to hit in a demo. This example
// overrides model.profile.maxInputTokens to a small value so summarization
// fires after a few turns.
//
// Run:
//     npx tsx m3/m3.1_summarization.ts

import { createDeepAgent } from "deepagents";
import { HumanMessage } from "langchain";
import { MemorySaver } from "@langchain/langgraph";

import { model } from "../models.js";

// Shrink the reported context window so summarization triggers at ~340 tokens
// (85% of 400) instead of the real threshold. Must use model object, not string.

Object.defineProperty(model, "profile", {
  value: { ...model.profile, maxInputTokens: 400 },
  configurable: true,
});

const agent = createDeepAgent({
  model,
  checkpointer: new MemorySaver(),
  systemPrompt: "You are a helpful assistant. Keep every response to one sentence.",
});

const THREAD = { configurable: { thread_id: "demo" } };

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
  const turns = [
    "My name is Alex. I work at Acme Corp.",
    "What is 2 + 2?",
    "I have been building a distributed cache for three months.",
    "What is the capital of France?",
    "What do you remember about me?",
  ];

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
