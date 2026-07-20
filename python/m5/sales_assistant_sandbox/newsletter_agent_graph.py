# python/m5/sales_assistant_sandbox/newsletter_agent_graph.py
"""newsletter-agent: a standalone graph, launched as an async subagent.

Registered as its own entry in langgraph.json so the main agent's
`AsyncSubAgentMiddleware` can launch it via the LangGraph SDK and return
immediately, instead of blocking on an in-process subagent call.

Unlike the earlier design (see git history: genre_researcher_graph.py), this
graph does the FULL newsletter job itself — researching every genre and
assembling the finished HTML — rather than being one of four parallel async
launches the main agent has to fan back in. Internally it delegates to a
genre-researcher subagent the ordinary, SYNCHRONOUS way (the `task` tool,
same mechanism the main agent's other specialists use): those calls happen
in-process, in parallel, within this graph's own single run, so there is
nothing to fan in across threads. Only ONE async boundary exists per
newsletter request — the main agent's single `start_async_task` launch of
*this* graph — so only one completion notification ever fires per request.

The graph is an async factory rather than a single object built once: each
run needs its own `CompletionNotifierMiddleware`, scoped to whichever main-
agent thread launched it. `parent_thread_id`/`parent_assistant_id` come from
`config.configurable`, written by the main agent's custom `start_async_task`
tool (see async_research.py) — not from end-user input.

Storage: a `StoreBackend` namespaced by this run's own thread_id. Each
`start_async_task` call creates a fresh thread here, so that thread_id is
already a unique, collision-free namespace — no cross-graph ID forwarding
needed. Omitting `store=` resolves to `get_store()` at runtime, which is the
same store instance the main graph uses (both graphs share one deployment).
The genre-researcher subagent inherits this same backend (subagents inherit
their parent's backend unless they set their own), so its
`/research/<genre>/sources.md` dumps land in this run's own namespace too.
"""

from __future__ import annotations

import contextlib

from completion_notifier import build_completion_notifier
from deepagents import create_deep_agent
from deepagents.backends.store import StoreBackend
from langchain_core.runnables import RunnableConfig
from subagents import GENRE_PROMPT
from tools.html import markdown_to_html

from models import model, strong_model

NEWSLETTER_AGENT_PROMPT = """You assemble Chinook's weekly "This Week in \
Music" customer newsletter. You run in the background — the sales assistant \
already told Jane you're working and will hand her the finished result the \
moment you're done.

You will be given a list of genres to cover. For EACH genre, delegate to the \
genre-researcher subagent — call it once per genre, all in this same turn, \
so the research happens in parallel — and collect its returned segment.

Once every genre-researcher call has returned:
1. Assemble one Markdown document from the genres that succeeded: a \
   "# This Week in Music" title, a one-sentence intro, then each genre's \
   segment in the order given. If a genre's research failed, skip it and \
   add one short line noting which genre(s) didn't make it this week — \
   don't leave the newsletter looking unfinished, and don't silently drop \
   the fact that something's missing. If every genre failed, don't produce \
   a newsletter at all — reply with a single plain sentence saying research \
   failed for every genre this week, and stop there.
2. Call `markdown_to_html` on the assembled Markdown.

Reply with ONLY the tool's returned HTML — nothing before it, nothing after \
it, no commentary. Your reply is written directly to a file verbatim; any \
extra sentence you add around the HTML ends up inside that file too."""


@contextlib.asynccontextmanager
async def graph(config: RunnableConfig):
    # Imported here, not at module load: tools.search instantiates a Tavily
    # client from TAVILY_API_KEY at import time, and this graph is always
    # registered in langgraph.json regardless of whether that key is set —
    # deferring the import keeps a missing key from breaking deployment
    # startup, matching this project's existing "search is optional" design
    # (see tools/search.py, agent.py's `_enable_search` guard).
    from tools.search import internet_search

    configurable = config.get("configurable", {})
    notifier = build_completion_notifier(
        parent_thread_id=configurable.get("parent_thread_id"),
        parent_assistant_id=configurable.get("parent_assistant_id"),
        subagent_name="newsletter-agent",
    )
    # `Runtime` (passed to namespace factories) has no `.config` attribute —
    # close over this run's own thread_id instead, captured from the graph
    # factory's own `config` (already available here, and this graph is
    # rebuilt fresh per run, so the closure is correctly scoped to one run).
    thread_id = configurable.get("thread_id")
    backend = StoreBackend(namespace=lambda rt: (thread_id, "research"))

    genre_researcher = {
        "name": "genre-researcher",
        "description": (
            "Research one music genre and write a newsletter segment about "
            "what's new in it. Call once per genre, in parallel."
        ),
        "system_prompt": GENRE_PROMPT,
        "tools": [internet_search],
        "model": model,
    }

    yield create_deep_agent(
        model=strong_model,
        tools=[markdown_to_html],
        system_prompt=NEWSLETTER_AGENT_PROMPT,
        subagents=[genre_researcher],
        backend=backend,
        middleware=[notifier],
        name="newsletter-agent",
    )
