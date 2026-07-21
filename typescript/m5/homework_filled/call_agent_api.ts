// typescript/m5/homework_filled/call_agent_api.ts
/**
 * Reference copy: talks to the deployed storm-chaser agent over the
 * Agent Server API instead of Studio's chat panel. This is just one
 * possible answer, so yours might be different. Explore!
 */

import { Client } from "@langchain/langgraph-sdk";

const API_URL = "http://localhost:2024";
const ASSISTANT_ID = "agent"; // matches the "agent" key in langgraph.json's "graphs"

// TODO 3 filled in
const QUESTION = "What's the windiest wind speed ever recorded?";

function lastAiText(messages: Record<string, unknown>[]): string {
  for (let i = messages.length - 1; i >= 0; i--) {
    const msg = messages[i];
    if (msg.type !== "ai") continue;
    const content = msg.content;
    if (typeof content === "string") return content;
    if (Array.isArray(content)) {
      return content
        .filter((b): b is { type: string; text: string } => typeof b === "object" && b !== null && (b as { type?: string }).type === "text")
        .map((b) => b.text)
        .join("\n");
    }
  }
  return "";
}

async function main(): Promise<void> {
  const client = new Client({ apiUrl: API_URL });

  const thread = await client.threads.create();
  console.log(`Created thread ${thread.thread_id} via POST /threads`);

  const result = await client.runs.wait(thread.thread_id, ASSISTANT_ID, {
    input: { messages: [{ role: "user", content: QUESTION }] },
  });

  console.log("\n--- Agent response (received over HTTP, not agent.invoke()) ---");
  const messages = (result as { messages?: Record<string, unknown>[] }).messages ?? [];
  console.log(lastAiText(messages));
}

await main();
