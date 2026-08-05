// typescript/m5/sales_assistant_sandbox/agent.ts
/**
 * Chinook Sales Assistant.
 *
 * The entire filesystem — skills, memory, and anything the agent writes or
 * runs — lives inside a per-thread LangSmith sandbox. Skills and AGENTS.md
 * are seeded into the sandbox once, when it's created, from local disk.
 * There is no local filesystem route the agent can read from or write to at
 * runtime, so there is nothing for an untrusted execution result to bridge
 * back to.
 *
 * Charts have no dedicated tool: the agent writes a script with write_file
 * and runs it with execute (added automatically because the backend
 * supports sandboxed command execution), the same way it would run any
 * other generated code.
 *
 * Start with:
 *     ./start.sh
 */
import { dirname, join } from "node:path";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

import { MultiServerMCPClient } from "@langchain/mcp-adapters";
import { createCodeInterpreterMiddleware } from "@langchain/quickjs";
import { context } from "langchain";
import type { LangGraphRunnableConfig } from "@langchain/langgraph";
import {
  LangSmithSandbox,
  StateBackend,
  createDeepAgent,
  type AnyBackendProtocol,
} from "deepagents";
import { SandboxClient, type Sandbox } from "langsmith/sandbox";

import { strongModel } from "../../models.js";
import { buildAsyncResearchMiddleware } from "./async-research.js";
import { buildSubagents } from "./subagents.js";
import { markdownToHtml } from "./tools/html.js";

const HERE = dirname(fileURLToPath(import.meta.url));

const SYSTEM_PROMPT = context`
  You are a sales assistant for Jane Peacock, a Sales Support Agent at
  Chinook, an online music distributor. Follow your operating manual (loaded
  from your memory) and use the matching playbook from /skills/ for each task.

  Your entire filesystem — skills, memory, and anything you write — lives
  inside an isolated sandbox; there is no separate local filesystem. To
  produce a chart, write a Python script with write_file and run it with
  execute (e.g. \`pip install matplotlib && python3 <script>\`), saving the
  image under /outputs/.`;

const MAIL_SERVER = { transport: "http" as const, url: "http://127.0.0.1:5002/mcp" };

const enableSearch = Boolean(process.env.TAVILY_API_KEY);
if (!enableSearch) {
  console.log("TAVILY_API_KEY not set — newsletter research subagent disabled.");
}

/** Return an existing thread-scoped sandbox, or create one, by name. */
async function lookupOrCreateSandbox(
  client: SandboxClient,
  name: string
): Promise<{ sandbox: Sandbox; freshlyCreated: boolean }> {
  try {
    const sandbox = await client.getSandbox(name);
    if (sandbox.status === "stopped") {
      console.log(`Restarting stopped sandbox ${name}`);
      return { sandbox: await client.startSandbox(name, { timeout: 15 }), freshlyCreated: false };
    }
    if (sandbox.status !== "ready") {
      console.log(`Waiting for sandbox ${name} (status: ${sandbox.status})`);
      return { sandbox: await client.waitForSandbox(name, { timeout: 15 }), freshlyCreated: false };
    }
    console.log(`Reusing sandbox ${name}`);
    return { sandbox, freshlyCreated: false };
  } catch {
    // idleTtlSeconds bounds compute cost if a student walks away mid-session;
    // deleteAfterStopSeconds bounds it further, since the server default
    // (~14 days) is way more than a classroom needs a stopped sandbox for.
    const sandbox = await client.createSandbox({
      name,
      idleTtlSeconds: 600,
      deleteAfterStopSeconds: 3600,
    });
    console.log(`Created sandbox ${name}`);
    return { sandbox, freshlyCreated: true };
  }
}

/** Upload /skills and /AGENTS.md from local disk into a fresh sandbox. */
async function seedSkillsAndMemory(backend: LangSmithSandbox): Promise<void> {
  // The sandbox is the only filesystem this agent can reach, so anything it
  // reads at runtime has to be pushed in here first. This lesson's directory
  // mirrors the sandbox layout, so each path below is both the local path
  // (under HERE) and the sandbox path. Adding a skill means adding it here.
  //
  // chinook-analyst's own /agents/chinook-analyst/AGENTS.md is deliberately
  // NOT seeded: it starts absent and the analyst writes it itself the first
  // time it introspects the schema, which is the behaviour ANALYST_PROMPT
  // teaches. Seeding a pre-filled copy would skip that lesson.
  const paths = [
    "/AGENTS.md",
    "/skills/rfq-quote/SKILL.md",
    "/skills/territory-report/SKILL.md",
    "/skills/weekly-newsletter/SKILL.md",
  ];
  const files = await Promise.all(
    paths.map(async (filePath): Promise<[string, Uint8Array]> => [
      filePath,
      await readFile(join(HERE, filePath)),
    ])
  );
  const results = await backend.uploadFiles(files);
  results.forEach((result, i) => {
    if (result.error) {
      console.warn(`Failed to seed ${paths[i]} into sandbox: ${result.error}`);
    }
  });
}

/** Look up (or create) this thread's sandbox and seed it if it's new. */
async function sandboxBackendForThread(threadId: string): Promise<LangSmithSandbox> {
  const client = new SandboxClient();
  const { sandbox, freshlyCreated } = await lookupOrCreateSandbox(client, `thread-${threadId}`);
  const backend = new LangSmithSandbox({ sandbox });
  if (freshlyCreated) {
    await seedSkillsAndMemory(backend);
  }
  return backend;
}

// langgraph-api calls this factory on every request that needs the graph,
// including read-only state and history reads, so anything built in the body is
// built per request. The JS MCP client holds a live connection and there's no
// teardown hook here, so one per request leaked a mock-mail socket on every
// chat-UI state poll until the server stopped answering handshakes. (Python's
// adapter opens a session per call, so its copy of this file doesn't leak.)
// Cleared on rejection so a transient failure stays retryable.
//
// Only the MCP client is memoized. The sandbox backend deliberately is NOT:
// LangSmithSandbox captures its Sandbox handle at construction, so a cached
// one can't see a server-side idleTtlSeconds stop and every later call throws
// LangSmithSandboxNotReadyError. Re-resolving per request (as Python does)
// means lookupOrCreateSandbox restarts a stopped sandbox instead.
let mailToolsPromise: ReturnType<MultiServerMCPClient["getTools"]> | undefined;
function mailTools() {
  if (!mailToolsPromise) {
    mailToolsPromise = new MultiServerMCPClient({ "mock-mail": MAIL_SERVER })
      .getTools()
      .catch((err) => {
        mailToolsPromise = undefined;
        throw err;
      });
  }
  return mailToolsPromise;
}

// Thread-scoped sandbox pattern:
// https://docs.langchain.com/langsmith/graph-rebuild#context-manager-factory
//
// `config.configurable?.thread_id` is undefined during LangGraph's
// schema-introspection calls (get_schema, get_graph, assistants.read, …), so
// that's the signal used to skip sandbox setup and fall back to an in-memory
// backend — same graph topology, no sandbox, no real filesystem access at
// all. Real runs get their own thread-scoped sandbox looked up by thread_id.
export async function graph(config: LangGraphRunnableConfig) {
  const threadId = config.configurable?.thread_id as string | undefined;
  const backend: AnyBackendProtocol = threadId
    ? await sandboxBackendForThread(threadId)
    : new StateBackend();

  const tools = await mailTools();

  return createDeepAgent({
    model: strongModel,
    tools: [markdownToHtml, ...tools],
    systemPrompt: SYSTEM_PROMPT,
    subagents: buildSubagents(backend, { mailTools: tools }),
    skills: ["/skills"],
    memory: ["/AGENTS.md"],
    backend,
    middleware: [
      createCodeInterpreterMiddleware({ ptc: ["execute", "write_file"] }),
      ...(enableSearch ? [buildAsyncResearchMiddleware()] : []),
    ],
    name: "chinook-sales-assistant",
  });
}
