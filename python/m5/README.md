# Module 5 — Capstone: The Chinook Sales Assistant

A deep agent that helps **Jane Peacock**, a Chinook sales rep, work her book of
business. It ties together the whole course: a **todo list** for long tasks,
**skills** + **`AGENTS.md`** memory, the **filesystem**, the **code
interpreter**, **subagents** (including parallel fan-out), an **optional
sandbox**, and **human-in-the-loop** approvals — over two real integrations:
**Gmail** (via MCP) and the **Chinook SQL database**.

The assistant is served as a **graph** with `langgraph dev` and driven from the
**agent-chat-ui** in your browser.

---

## What it does

Three task sequences show off the features:

| Task | Ask it… | Shows off |
|------|---------|-----------|
| **Process an RFQ** | "Check my inbox for quote requests and process the first one." | inbox read → DB lookup → **new-customer add (approval)** → **exact quote math (interpreter)** → **quote-reviewer subagent** → **draft reply (approval)** → ledger file · todo list |
| **Weekly newsletter** | "Write this week's newsletter." | **parallel genre-researcher subagents** · web search · newsletter **skill** · HTML to `/outputs/` |
| **Territory report** | "How is my book of business doing?" | DB metrics · report file · **optional sandbox** chart |

Two actions pause for your approval and render as cards in agent-chat-ui:
saving a **Gmail draft** and **adding a new customer**.

## Architecture in one breath

`agent.py` exposes an async factory `make_graph` (pointed at by
`langgraph.json`). At startup it asks the Gmail MCP server for its tools, then
builds the agent around them. If Gmail is down, the agent still comes up without
those tools — a missing MCP server never sinks it.

The two **writes** live only on gated specialist subagents — `gmail_create_draft`
on **inbox-manager**, `add_customer` on **chinook-analyst** — each behind a
human-approval gate. The main agent holds no write tools, so the always-present
general-purpose subagent (which inherits the main agent's tools) can never reach
a write ungated. **chinook-analyst** also self-bootstraps: on first use it
introspects the schema and writes it into its *own* `AGENTS.md`.

```
agent.py            the main agent + async make_graph factory
subagents.py        chinook-analyst · inbox-manager · quote-reviewer · genre-researcher
tools/              sql.py (read-only + gated add_customer) · search.py · html.py · chart.py
mcp/                mock_gmail_server.py (offline Gmail) · mail_store.py · send_to_inbox.py
AGENTS.md           the assistant's operating manual (loaded as memory)
agents/…/AGENTS.md  chinook-analyst's own memory (schema self-written here)
skills/             rfq-quote · weekly-newsletter · territory-report
langgraph.json      serves the graph for `langgraph dev`
```

---

## Setup

From the repo's `python/` directory, you've already run `uv sync` and filled in
`.env` (see the root README). Module 5 needs:

- `ANTHROPIC_API_KEY` (or your provider) and `LANGSMITH_API_KEY` — as usual.
- `TAVILY_API_KEY` — only for the newsletter task. Without it, that subagent is
  simply not loaded.

### Choose your Gmail backend

Set `GMAIL_BACKEND` in `python/.env` (defaults to `mock`):

- `mock` *(default, zero setup)* — a small local MCP server we ship
  (`mcp/mock_gmail_server.py`). No OAuth, works offline. Same three tools as the
  real thing: `gmail_list_messages`, `gmail_read_message`, `gmail_create_draft`.
- `real` — a hosted Gmail MCP server + OAuth (see `mcp_real.json`). This path is
  not yet verified; if it can't connect, the agent still starts without Gmail.
- `none` — skip Gmail entirely.

### Seed the mock inbox

```bash
cd python/m5
uv run python mcp/send_to_inbox.py            # loads the bundled RFQ fixture
uv run python mcp/send_to_inbox.py --reset    # clear + re-seed
```

---

## Run it

**1. Serve the agent** (from `python/m5`):

```bash
cd python/m5
uv run langgraph dev --allow-blocking
```

`--allow-blocking` is needed because discovering the MCP server's tools at
startup does a little synchronous I/O, which `langgraph dev` otherwise flags.

**2. Open the chat UI.** The agent is driven from
[agent-chat-ui](https://github.com/langchain-ai/agent-chat-ui), a Next.js app you
run locally (Node + [pnpm](https://pnpm.io/installation)). Leave the agent server
from step 1 running, then in a **second terminal**:

```bash
# Clone it once (anywhere outside this repo)
git clone https://github.com/langchain-ai/agent-chat-ui.git
cd agent-chat-ui

# Configure it to talk to your local agent
cp .env.example .env
```

Edit the new `.env` so it points at the local LangGraph server:

```bash
# agent-chat-ui/.env
NEXT_PUBLIC_API_URL=http://localhost:2024
NEXT_PUBLIC_ASSISTANT_ID=agent
```

Then install and start it:

```bash
cd agent-chat-ui
pnpm install
pnpm dev
```

Open the UI at **http://localhost:3000**. (If you skip the `.env`, the app shows a
connection form instead — fill in Deployment URL `http://localhost:2024` and
Assistant / Graph ID `agent`.)

Then try one of the asks from the table above. When an approval card appears
(draft or new customer), approve / edit / reject it right in the chat.

### Optional: the sandbox chart

The territory report draws a chart only if a sandbox is available. Enable it
with `ENABLE_SANDBOX=1` (requires `langsmith[sandbox]` access). Without it, the
report is numbers-only — everything else still works.

---

## Notes

- **Served as a graph, not a `main()`.** Earlier modules ran agents as scripts;
  here `langgraph dev` loads the graph from `langgraph.json`.
- **Tools are discovered before the agent is built.** The model can only call
  tools it's been told about, and an MCP server's tool list comes from an async
  call — so discovery happens up front, tolerating a server being down.
- `FilesystemBackend` gives the agent real disk access scoped to this folder —
  fine for local dev, not for a shared server.
- Generated/runtime files (`mcp/mail_store.json`, `/outputs/`, the temp MCP
  config) are gitignored.
