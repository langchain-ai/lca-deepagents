# python/m5/hello/agent.py
"""A minimal deep agent, exposed as a graph for `langgraph dev`.

This is the whole agent: a model, nothing else. The point of this lab is the
*deployment*, not the agent — so we keep the agent as small as it gets and let
`langgraph dev` serve it over HTTP.
"""

from deepagents import create_deep_agent

# `langgraph.json` points at this module-level variable: "./agent.py:graph".
graph = create_deep_agent(model="claude-sonnet-4-6")
