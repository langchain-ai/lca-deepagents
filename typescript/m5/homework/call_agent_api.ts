// typescript/m5/homework/call_agent_api.ts
/**
 * M5.2 Homework, part 2: Talk to Your Deployed Agent Over the Agent
 * Server API.
 *
 * THE IDEA
 * So far you've only ever reached your deployed agent through Studio's
 * chat panel. This script reaches it the way any other client would: over
 * the same Agent Server API this lesson covers (Threads, Runs), using the
 * LangGraph SDK instead of a browser. The harness below creates a thread
 * and starts a run for you; you just supply the question to ask.
 *
 * BEFORE YOU RUN THIS
 *   In one terminal, leave this running:
 *     cd typescript/m5/homework
 *     pnpm exec langgraphjs dev
 *   Then, in a second terminal:
 *     cd typescript
 *     pnpm tsx ./m5/homework/call_agent_api.ts
 *
 * WHAT YOU FILL IN
 *   TODO 3: write a QUESTION that should make your agent (from agent.ts)
 *     call the tool you wrote for TODO 1.
 */

import { Client } from "@langchain/langgraph-sdk";

// langgraphjs dev binds its loopback listener to ::1 rather than 127.0.0.1;
// "localhost" resolves to whichever loopback address is actually listening.
const API_URL = "http://localhost:2024";
const ASSISTANT_ID = "agent"; // matches the "agent" key in langgraph.json's "graphs"

// TODO 3: replace this with a question that should trigger your tool.
const QUESTION = "TODO 3: replace this with a question for your deployed agent.";

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

  // Create a thread over the API -- the same POST /threads endpoint the
  // lesson's "Threads" section describes.
  const thread = await client.threads.create();
  console.log(`Created thread ${thread.thread_id} via POST /threads`);

  // Start a run and wait for it to finish -- POST /threads/{id}/runs/wait.
  const result = await client.runs.wait(thread.thread_id, ASSISTANT_ID, {
    input: { messages: [{ role: "user", content: QUESTION }] },
  });

  console.log("\n--- Agent response (received over HTTP, not agent.invoke()) ---");
  const messages = (result as { messages?: Record<string, unknown>[] }).messages ?? [];
  console.log(lastAiText(messages));
}

if (QUESTION.startsWith("TODO 3")) {
  throw new Error("TODO 3: see the comment block above");
}

await main();
