# python/m5/tools/search.py
"""Web search tool for the genre-researcher subagent (weekly newsletter).

Thin wrapper over Tavily, identical in spirit to the Module 4 lab. Belongs only
to the research subagent. Requires TAVILY_API_KEY in the environment; if it's
absent the tool is simply not registered (see subagents.py), so the rest of the
assistant still runs.
"""

from __future__ import annotations

import os

from langchain_core.tools import tool
from tavily import TavilyClient

_tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])


@tool
def internet_search(query: str, max_results: int = 8) -> dict:
    """Search the web for recent news. Use this to research what's new in a
    music genre — new releases, notable artists, trends, and events."""
    return _tavily.search(query, max_results=max_results, topic="news")
