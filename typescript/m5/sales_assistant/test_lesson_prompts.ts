// typescript/m5/sales_assistant/test_lesson_prompts.ts
/**
 * End-to-end test for the three lesson prompts from m5.3-the-sales-assistant.md.
 *
 * Run with both services up:
 *     npx tsx test_lesson_prompts.ts
 *
 * Or via start.sh (which launches the mail server + langgraph dev), then in a
 * second terminal:
 *     npx tsx test_lesson_prompts.ts
 */
import { execFileSync } from "node:child_process";
import { dirname } from "node:path";
import { fileURLToPath } from "node:url";

import { Client, type ThreadState } from "@langchain/langgraph-sdk";

const HERE = dirname(fileURLToPath(import.meta.url));
// langgraphjs dev binds its loopback listener to ::1 rather than 127.0.0.1;
// "localhost" resolves to whichever loopback address is actually listening.
const API_URL = "http://localhost:2024";
const ASSISTANT_ID = "agent";

const PROMPTS: [string, string][] = [
  ["Territory report", "How's my book of business looking? Give me a territory report."],
  ["Weekly newsletter", 'Write this week\'s "This Week in Music" newsletter.'],
  ["Process RFQ", "Check the inbox for any quote requests and process them."],
];

function lastAiText(messages: Record<string, unknown>[]): string {
  for (let i = messages.length - 1; i >= 0; i--) {
    const msg = messages[i];
    if (msg.type === "ai") {
      const content = msg.content;
      if (typeof content === "string") return content;
      if (Array.isArray(content)) {
        return content
          .filter((b): b is { type: string; text: string } => typeof b === "object" && b !== null && (b as { type?: string }).type === "text")
          .map((b) => b.text)
          .join("\n");
      }
    }
  }
  return "(no AI message found)";
}

function fill(text: string, width: number, subsequentIndent: string): string {
  const words = text.split(/\s+/);
  const lines: string[] = [];
  let line = "";
  for (const word of words) {
    const candidate = line ? `${line} ${word}` : word;
    if (candidate.length > width && line) {
      lines.push(line);
      line = word;
    } else {
      line = candidate;
    }
  }
  if (line) lines.push(line);
  return lines.map((l, i) => (i === 0 ? l : subsequentIndent + l)).join("\n");
}

async function runPrompt(client: Client, label: string, prompt: string): Promise<void> {
  console.log(`\n${"=".repeat(60)}`);
  console.log(`  ${label}`);
  console.log(`${"=".repeat(60)}`);
  console.log(`Prompt: ${prompt}\n`);

  // Reset the mail store before the RFQ test so there's a message to process.
  if (label === "Process RFQ") {
    try {
      execFileSync("npx", ["tsx", "mcp/send_to_inbox.ts", "--reset"], { cwd: HERE, stdio: "ignore" });
    } catch {
      // best-effort
    }
    console.log("(inbox reset)\n");
  }

  const thread = await client.threads.create();
  let run = await client.runs.create(thread.thread_id, ASSISTANT_ID, {
    input: { messages: [{ role: "user", content: prompt }] },
  });

  // Poll until done, handling interrupts (e.g. draft-approval gate).
  let interruptCount = 0;
  let state: ThreadState;
  while (true) {
    await client.runs.join(thread.thread_id, run.run_id);
    state = await client.threads.getState(thread.thread_id);

    // state.next is non-empty only when the graph is paused at an interrupt.
    const interrupted = state.next.length > 0;

    if (!interrupted || interruptCount >= 3) break;

    // Auto-approve the interrupt (mirrors a student clicking "Approve").
    interruptCount += 1;
    const tasks = state.tasks ?? [];
    const interruptInfo = tasks.flatMap((t) => t.interrupts ?? []);
    const preview = interruptInfo.length > 0 ? String(interruptInfo[0].value ?? "").slice(0, 80) : "?";
    console.log(`  [interrupt #${interruptCount}] auto-approving: ${preview}`);

    run = await client.runs.create(thread.thread_id, ASSISTANT_ID, {
      command: { resume: { decisions: [{ type: "approve" }] } },
    });
  }

  const messages = (state.values as { messages?: Record<string, unknown>[] }).messages ?? [];
  const reply = lastAiText(messages);
  console.log(reply ? fill(reply, 72, "  ") : "(empty)");
  console.log(`\n[${messages.length} messages total, ${interruptCount} interrupt(s) handled]`);
}

async function main(): Promise<void> {
  const client = new Client({ apiUrl: API_URL });

  // Quick health check.
  try {
    await client.assistants.search();
  } catch (exc) {
    console.log(`ERROR: langgraph dev not reachable at ${API_URL} — ${exc}`);
    console.log("Start it first with:  ./start.sh");
    return;
  }

  for (const [label, prompt] of PROMPTS) {
    await runPrompt(client, label, prompt);
  }

  console.log(`\n${"=".repeat(60)}`);
  console.log("  All three prompts complete.");
  console.log(`${"=".repeat(60)}\n`);
}

await main();
