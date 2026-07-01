// typescript/m2/m2.4_MessageHistory.ts
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
//     npx tsx m2/m2.4_MessageHistory.ts

import { createDeepAgent } from "deepagents";
import { MemorySaver } from "@langchain/langgraph";
import { HumanMessage } from "@langchain/core/messages";
import { initChatModel } from "langchain";

// Shrink the reported context window so summarization triggers at ~1700 tokens
// (85% of 2000) instead of the real 170,000-token threshold.
const MODEL = "anthropic:claude-haiku-4-5";
const model = await initChatModel(MODEL);

Object.defineProperty(model, "profile", {
  value: { ...model.profile, maxInputTokens: 700 },
  configurable: true,
});

const agent = createDeepAgent({
  model,
  checkpointer: new MemorySaver(),
  systemPrompt: "You are a helpful assistant. Keep every response to one sentence.",
});

const THREAD = { configurable: { thread_id: "demo" } };

async function turn(message: string): Promise<unknown> {
  const result = await agent.invoke(
    { messages: [new HumanMessage(message)] },
    THREAD
  );
  return result.messages[result.messages.length - 1].content;
}

async function showState(): Promise<void> {
  const state = await (agent.getState as (config: unknown) => Promise<{ values: Record<string, any> }>)(THREAD);
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
