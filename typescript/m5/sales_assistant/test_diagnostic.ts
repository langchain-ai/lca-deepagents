// typescript/m5/sales_assistant/test_diagnostic.ts
/**
 * Layered diagnostic tests for the Chinook Sales Assistant.
 *
 * Runs all capability layers in order and prints a summary. Start both
 * services first, then run this in a second terminal:
 *
 *     ./start.sh                     # terminal 1
 *     npx tsx test_diagnostic.ts     # terminal 2
 */
import { execFileSync } from "node:child_process";
import { existsSync, statSync, unlinkSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { config } from "dotenv";
import { Client } from "@langchain/langgraph-sdk";

const HERE = dirname(fileURLToPath(import.meta.url));

// Load the same .env that langgraph.json points at.
config({ path: join(HERE, "../../.env") });

// langgraphjs dev binds its loopback listener to ::1 rather than 127.0.0.1;
// "localhost" resolves to whichever loopback address is actually listening.
const API_URL = "http://localhost:2024";
const ASSISTANT_ID = "agent";
const OUTPUTS_DIR = join(HERE, "outputs");

type Status = "PASS" | "FAIL" | "SKIP";

interface Result {
  label: string;
  status: Status;
  detail?: string;
  note?: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

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
  return "";
}

async function askInThread(
  client: Client,
  threadId: string,
  prompt: string
): Promise<[string, Record<string, unknown>[]]> {
  const run = await client.runs.create(threadId, ASSISTANT_ID, {
    input: { messages: [{ role: "user", content: prompt }] },
  });
  // Poll manually so we can print progress dots while waiting.
  while (true) {
    const state = await client.runs.get(threadId, run.run_id);
    if (state.status === "success" || state.status === "error" || state.status === "timeout") {
      break;
    }
    process.stdout.write(".");
    await new Promise((resolve) => setTimeout(resolve, 5000));
  }
  const state = await client.threads.getState(threadId);
  const messages = (state.values as { messages?: Record<string, unknown>[] }).messages ?? [];
  return [lastAiText(messages), messages];
}

async function ask(client: Client, prompt: string): Promise<[string, Record<string, unknown>[]]> {
  const thread = await client.threads.create();
  return askInThread(client, thread.thread_id, prompt);
}

function toolOutputs(messages: Record<string, unknown>[], toolName: string): unknown[] {
  return messages
    .filter((m) => m.type === "tool" && m.name === toolName)
    .map((m) => m.content);
}

function shorten(text: string, width: number): string {
  return text.length > width ? `${text.slice(0, width - 1)}…` : text;
}

function resetInbox(): void {
  try {
    execFileSync("npx", ["tsx", "mcp/send_to_inbox.ts", "--reset"], { cwd: HERE, stdio: "ignore" });
  } catch {
    // best-effort
  }
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

async function testServerReachable(client: Client): Promise<Result> {
  const label = "LangGraph server — reachable at port 2024";
  process.stdout.write(`  Running: ${label}... `);
  try {
    await client.assistants.search();
    console.log("done");
    return { label, status: "PASS" };
  } catch (exc) {
    console.log("done");
    return { label, status: "FAIL", detail: `${exc} — is ./start.sh running?` };
  }
}

async function testHello(client: Client): Promise<Result> {
  const label = "Hello — LLM connectivity";
  process.stdout.write(`  Running: ${label}... `);
  try {
    const [reply] = await ask(client, "Hello! Just say hi back in one sentence.");
    console.log("done");
    if (reply) return { label, status: "PASS", detail: shorten(reply, 80) };
    return { label, status: "FAIL", detail: "(empty reply)" };
  } catch (exc) {
    console.log("done");
    return { label, status: "FAIL", detail: String(exc) };
  }
}

async function testAgentsMd(client: Client): Promise<Result> {
  const label = "AGENTS.md — memory file loaded";
  process.stdout.write(`  Running: ${label}... `);
  try {
    const [reply] = await ask(
      client,
      "Repeat the diagnostic token from your operating manual. " +
        "It appears as italic text near the top of the file."
    );
    const passed = reply.includes("CHINOOK-READY");
    console.log("done");
    return { label, status: passed ? "PASS" : "FAIL", detail: shorten(reply, 80) };
  } catch (exc) {
    console.log("done");
    return { label, status: "FAIL", detail: String(exc) };
  }
}

async function testSkillsLoaded(client: Client): Promise<Result> {
  const label = "skills/ — playbooks readable";
  process.stdout.write(`  Running: ${label}... `);
  try {
    const [reply] = await ask(
      client,
      "What task playbooks or skills do you have available? List their names."
    );
    const keywords = ["rfq", "quote", "newsletter", "territory"];
    const lower = reply.toLowerCase();
    const passed = keywords.some((kw) => lower.includes(kw));
    console.log("done");
    return { label, status: passed ? "PASS" : "FAIL", detail: shorten(reply, 80) };
  } catch (exc) {
    console.log("done");
    return { label, status: "FAIL", detail: String(exc) };
  }
}

async function testChinookAnalyst(client: Client): Promise<Result> {
  const label = "chinook-analyst — database query";
  process.stdout.write(`  Running: ${label}... `);
  try {
    const [reply] = await ask(client, "How many tracks are in the Chinook database?");
    const passed = reply.includes("3503") || reply.includes("3,503");
    console.log("done");
    return { label, status: passed ? "PASS" : "FAIL", detail: shorten(reply, 80) };
  } catch (exc) {
    console.log("done");
    return { label, status: "FAIL", detail: String(exc) };
  }
}

async function testCodeInterpreter(client: Client): Promise<Result> {
  const label = "Code interpreter — exact arithmetic";
  process.stdout.write(`  Running: ${label}... `);
  try {
    const [reply] = await ask(
      client,
      "Use the code interpreter to calculate: 37 tracks at $0.99 each. " +
        "What is the exact total?"
    );
    const passed = reply.includes("36.63");
    console.log("done");
    return { label, status: passed ? "PASS" : "FAIL", detail: shorten(reply, 80) };
  } catch (exc) {
    console.log("done");
    return { label, status: "FAIL", detail: String(exc) };
  }
}

async function testMailToolNames(_client: Client): Promise<Result> {
  const label = "inbox-manager — MCP tool names discovered correctly";
  process.stdout.write(`  Running: ${label}... `);
  try {
    const { MultiServerMCPClient } = await import("@langchain/mcp-adapters");
    const mcpClient = new MultiServerMCPClient({
      "mock-mail": { transport: "http", url: "http://127.0.0.1:5002/mcp" },
    });
    const tools = await mcpClient.getTools();
    const names = new Set(tools.map((t) => t.name));
    const expected = ["mail_list_messages", "mail_read_message", "mail_create_draft"];
    const missing = expected.filter((n) => !names.has(n));
    const passed = missing.length === 0;
    const detail = passed
      ? `found: ${[...names].sort().join(", ")}`
      : `missing: ${missing.join(", ")}`;
    console.log("done");
    return { label, status: passed ? "PASS" : "FAIL", detail };
  } catch (exc) {
    console.log("done");
    return { label, status: "FAIL", detail: String(exc) };
  }
}

async function testInboxManager(client: Client): Promise<Result> {
  const label = "inbox-manager — mail MCP tool call";
  process.stdout.write(`  Running: ${label}... `);
  resetInbox();
  try {
    const [reply] = await ask(client, "Do I have any messages in my inbox?");
    const lower = reply.toLowerCase();
    const passed = lower.includes("morgan") || lower.includes("message");
    console.log("done");
    return { label, status: passed ? "PASS" : "FAIL", detail: shorten(reply, 80) };
  } catch (exc) {
    console.log("done");
    return { label, status: "FAIL", detail: String(exc) };
  }
}

async function testHitlInterrupt(client: Client): Promise<Result> {
  const label = "Human-in-the-loop — draft triggers interrupt";
  process.stdout.write(`  Running: ${label}... `);
  try {
    const thread = await client.threads.create();
    const run = await client.runs.create(thread.thread_id, ASSISTANT_ID, {
      input: {
        messages: [
          {
            role: "user",
            content:
              "Draft a reply to the email from Morgan Vale saying we will get " +
              "back to them within 24 hours. Save the draft.",
          },
        ],
      },
    });
    await client.runs.join(thread.thread_id, run.run_id);
    const state = await client.threads.getState(thread.thread_id);
    const tasks = state.tasks ?? [];
    const interrupted = tasks.some((t) => t.interrupts && t.interrupts.length > 0);
    console.log("done");
    return {
      label,
      status: interrupted ? "PASS" : "FAIL",
      detail: interrupted ? "interrupt fired" : "run completed without interrupt",
    };
  } catch (exc) {
    console.log("done");
    return { label, status: "FAIL", detail: String(exc) };
  }
}

async function testRenderPieChart(client: Client): Promise<Result> {
  const label = "render_pie_chart — genre revenue chart lands in outputs/";
  process.stdout.write(`  Running: ${label}... `);
  const target = join(OUTPUTS_DIR, "diag_genre_revenue.png");
  if (existsSync(target)) unlinkSync(target);
  try {
    const thread = await client.threads.create();
    const [, messages] = await askInThread(
      client,
      thread.thread_id,
      "Query the Chinook database for total revenue by genre (top 5 genres). " +
        "Call render_pie_chart to save a pie chart as diag_genre_revenue.png."
    );
    const toolOuts = toolOutputs(messages, "render_pie_chart");
    const exists = existsSync(target);
    const size = exists ? statSync(target).size : 0;
    const passed = exists && size > 0 && toolOuts.length > 0;
    const detail = exists
      ? `${size.toLocaleString()} bytes`
      : `file missing; render_pie_chart returned: ${JSON.stringify(toolOuts)}`;
    console.log("done");
    return { label, status: passed ? "PASS" : "FAIL", detail };
  } catch (exc) {
    console.log("done");
    return { label, status: "FAIL", detail: String(exc) };
  }
}

// ---------------------------------------------------------------------------
// Runner
// ---------------------------------------------------------------------------

async function main(): Promise<void> {
  const client = new Client({ apiUrl: API_URL });

  console.log(`\nChinook Sales Assistant — Diagnostic\n${"─".repeat(42)}\n`);

  const results: Result[] = [];

  const serverResult = await testServerReachable(client);
  results.push(serverResult);

  if (serverResult.status === "FAIL") {
    console.log("  (server not reachable — skipping remaining tests)");
  } else {
    const rest = [
      testHello,
      testAgentsMd,
      testSkillsLoaded,
      testChinookAnalyst,
      testCodeInterpreter,
      testMailToolNames,
      testInboxManager,
      testHitlInterrupt,
      testRenderPieChart,
    ];
    for (const testFn of rest) {
      results.push(await testFn(client));
    }
  }

  const passed = results.filter((r) => r.status === "PASS").length;
  const failed = results.filter((r) => r.status === "FAIL").length;
  const skipped = results.filter((r) => r.status === "SKIP").length;

  console.log(`\n${"─".repeat(42)}`);
  console.log("Summary\n");
  const icons: Record<Status, string> = { PASS: "✓", FAIL: "✗", SKIP: "–" };
  for (const r of results) {
    console.log(`  ${icons[r.status]}  ${r.label}`);
    if (r.status === "FAIL" && r.detail) {
      console.log(`       ${shorten(r.detail, 72)}`);
    }
    if (r.status === "SKIP" && r.note) {
      console.log(`       (${r.note})`);
    }
  }

  let totals = `${passed} passed`;
  if (failed) totals += `, ${failed} failed`;
  if (skipped) totals += `, ${skipped} skipped`;
  console.log(`\n${totals}`);
  console.log(`${"─".repeat(42)}\n`);
}

await main();
