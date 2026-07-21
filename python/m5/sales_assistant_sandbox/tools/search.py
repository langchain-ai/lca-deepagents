# python/m5/tools/search.py
"""Web search tool for the genre-researcher subagent (weekly newsletter).

Thin wrapper over Tavily, identical in spirit to the Module 4 lab. Belongs only
to the research subagent. Requires TAVILY_API_KEY in the environment; if it's
absent the tool is simply not registered (see subagents.py), so the rest of the
assistant still runs.
"""

from __future__ import annotations

import os
import time

from langchain_core.tools import tool
from requests.exceptions import ConnectionError as RequestsConnectionError
from tavily import TavilyClient

_MAX_ATTEMPTS = 3
_RETRY_DELAY_SECONDS = 2


@tool
def internet_search(query: str, max_results: int = 8) -> dict:
    """Search the web for recent news. Use this to research what's new in a
    music genre — new releases, notable artists, trends, and events."""
    # A fresh client per call, not a shared module-level singleton — the
    # newsletter-agent's genre research fires several of these concurrently
    # in one turn (LangGraph's ToolNode gathers tool calls in parallel
    # threads), and a shared TavilyClient's connection pool was getting
    # handed pooled keep-alive sockets the remote had already closed,
    # surfacing as ConnectionResetError. Retrying covers any remaining
    # one-off resets.
    client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
    last_error: RequestsConnectionError | None = None
    for attempt in range(_MAX_ATTEMPTS):
        try:
            return client.search(query, max_results=max_results, topic="news")
        except RequestsConnectionError as e:
            last_error = e
            if attempt < _MAX_ATTEMPTS - 1:
                time.sleep(_RETRY_DELAY_SECONDS)
    raise last_error
