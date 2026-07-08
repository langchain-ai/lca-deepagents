// typescript/m5/sales_assistant/mcp/mock_mail_server.ts
/**
 * A local, offline mock mail MCP server.
 *
 * Exposes three tools over HTTP (streamable-http transport) on port 5002:
 *
 *   mail_list_messages(query)            -> summaries of inbox mail
 *   mail_read_message(messageId)         -> the full body of one message
 *   mail_create_draft(to, subject, body) -> save a reply to the drafts folder
 *
 * State is a small JSON file managed by mail_store.ts. Started by start.sh
 * before langgraph dev so agent.ts can discover the tools at startup.
 */
import { createServer } from "node:http";

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { z } from "zod";

import { loadStore, nextId, saveStore } from "./mail_store.js";

// Stateless mode requires a fresh McpServer + transport per request — the
// protocol state machine only supports one client lifecycle per instance, so
// reusing a single instance across independent HTTP connections breaks after
// the first handshake (see the SDK's own simpleStatelessStreamableHttp example).
function buildServer(): McpServer {
  const mcp = new McpServer({ name: "mock-mail", version: "1.0.0" });

  mcp.registerTool(
    "mail_list_messages",
    {
      description:
        "List messages in the inbox. Returns a summary (id, from, subject, " +
        "date, snippet) for each message — not the full body. Use " +
        "mail_read_message to open one. The optional query is a " +
        "case-insensitive substring matched against the subject and sender, " +
        "mostly to mirror Gmail's search box; leave it empty to list everything.",
      inputSchema: { query: z.string().default("") },
    },
    async ({ query }) => {
      const store = loadStore();
      const q = query.trim().toLowerCase();
      const out = store.inbox
        .filter((m) => !q || `${m.subject ?? ""} ${m.from ?? ""}`.toLowerCase().includes(q))
        .map((m) => ({
          id: m.id,
          from: m.from,
          subject: m.subject,
          date: m.date,
          snippet: (m.body ?? "").slice(0, 140) + ((m.body ?? "").length > 140 ? "…" : ""),
        }));
      return { content: [{ type: "text" as const, text: JSON.stringify(out) }] };
    }
  );

  mcp.registerTool(
    "mail_read_message",
    {
      description: "Return the full message (sender, subject, date, complete body) by id.",
      inputSchema: { messageId: z.string() },
    },
    async ({ messageId }) => {
      const store = loadStore();
      const message = store.inbox.find((m) => m.id === messageId);
      const result = message ?? { error: `No message with id ${JSON.stringify(messageId)}.` };
      return { content: [{ type: "text" as const, text: JSON.stringify(result) }] };
    }
  );

  mcp.registerTool(
    "mail_create_draft",
    {
      description:
        "Save a reply to the drafts folder. Does NOT send. Mirrors a real " +
        "Gmail \"create draft\" call: the message is staged for the human to " +
        "review and send later. In this course a human-in-the-loop gate runs " +
        "before this tool, so a draft is only written after explicit approval.",
      inputSchema: { to: z.string(), subject: z.string(), body: z.string() },
    },
    async ({ to, subject, body }) => {
      const store = loadStore();
      const draft = { id: nextId(store.drafts, "draft"), to, subject, body };
      store.drafts.push(draft);
      saveStore(store);
      const result = { status: "draft_saved", draft_id: draft.id, to, subject };
      return { content: [{ type: "text" as const, text: JSON.stringify(result) }] };
    }
  );

  return mcp;
}

const httpServer = createServer((req, res) => {
  if (req.url !== "/mcp") {
    res.writeHead(404).end();
    return;
  }
  void (async () => {
    const mcp = buildServer();
    const transport = new StreamableHTTPServerTransport({ sessionIdGenerator: undefined });
    res.on("close", () => {
      transport.close();
      mcp.close();
    });
    await mcp.connect(transport);
    await transport.handleRequest(req, res);
  })().catch((error: unknown) => {
    console.error("Error handling MCP request:", error);
    if (!res.headersSent) {
      res.writeHead(500).end();
    }
  });
});

httpServer.listen(5002, "127.0.0.1", () => {
  console.log("Mock mail MCP server listening on http://127.0.0.1:5002/mcp");
});
