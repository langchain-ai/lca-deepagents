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
nothing to fan in across threads.

No completion-notification middleware here (see git history:
completion_notifier.py) — the main agent finds out this task is done the
ordinary way, by checking `check_async_task`/`list_async_tasks` the next time
it's asked, rather than being woken by a cross-thread run. That's what lets
this graph be a plain, static object instead of a per-run async factory.

Storage: a `StoreBackend` namespaced by this run's own thread_id, resolved
lazily via `get_config()` inside the namespace lambda — called only when the
backend actually does a store operation during a real run, not at graph
construction time, so no factory/`config` param is needed to build this
graph. Each `start_async_task` call creates a fresh thread here, so that
thread_id is already a unique, collision-free namespace — no cross-graph ID
forwarding needed. Omitting `store=` resolves to `get_store()` at runtime,
which is the same store instance the main graph uses (both graphs share one
deployment). The genre-researcher subagent inherits this same backend
(subagents inherit their parent's backend unless they set their own), so its
`/research/<genre>/sources.md` dumps land in this run's own namespace too.
"""

from __future__ import annotations

import os

from deepagents import create_deep_agent
from deepagents.backends.store import StoreBackend
from langgraph.config import get_config
from subagents import GENRE_PROMPT
from tools.html import markdown_to_html

from models import model, strong_model

# This module is always imported by the langgraph platform (it's a
# registered graph in langgraph.json) regardless of whether the main agent
# ever exposes the launch tool for it — so importing tools.search (which
# instantiates a Tavily client from TAVILY_API_KEY at import time) has to
# stay conditional here too, matching agent.py's own `_enable_search` guard,
# even though there's no factory body left to defer the import inside.
_enable_search = bool(os.environ.get("TAVILY_API_KEY"))
if _enable_search:
    from tools.search import internet_search

    _genre_researcher_tools = [internet_search]
else:
    _genre_researcher_tools = []

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

_genre_researcher = {
    "name": "genre-researcher",
    "description": (
        "Research one music genre and write a newsletter segment about "
        "what's new in it. Call once per genre, in parallel."
    ),
    "system_prompt": GENRE_PROMPT,
    "tools": _genre_researcher_tools,
    "model": model,
}

_backend = StoreBackend(
    namespace=lambda rt: (get_config()["configurable"]["thread_id"], "research")
)

graph = create_deep_agent(
    model=strong_model,
    tools=[markdown_to_html],
    system_prompt=NEWSLETTER_AGENT_PROMPT,
    subagents=[_genre_researcher],
    backend=_backend,
    name="newsletter-agent",
)
