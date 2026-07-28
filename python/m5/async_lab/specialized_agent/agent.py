# python/m5/async_lab/specialized_agent/agent.py
"""M5.4 Lab: the "specialized" deployment.

THE IDEA
This is a second, independent deployment, not a folder inside the shared
course environment. It has its own pyproject.toml and its own model setup,
so pandas (needed for the analysis tool below) is installed only here,
never in the shared environment every other lab in the course depends on.
Its langgraph.json also declares "dependencies": ["."] instead of the usual
["../.."], which is what makes that isolation real.

RUN
  cd python/m5/async_lab/specialized_agent
  uv run langgraph dev --port 2025
Leave this running, then start ../main_agent in a second terminal. The main
agent reaches this one over HTTP at http://127.0.0.1:2025, exactly like any
other remote deployment.
"""

import time

import pandas as pd
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool

from deepagents import create_deep_agent

SALES = pd.DataFrame(
    {
        "region": ["West", "West", "East", "East", "Central", "Central"],
        "product": ["Widget", "Gadget", "Widget", "Gadget", "Widget", "Gadget"],
        "units_sold": [1200, 850, 980, 1400, 630, 720],
        "revenue": [36000, 42500, 29400, 70000, 18900, 36000],
    }
)


@tool
def analyze_sales(group_by: str = "region") -> str:
    """Run a full sales breakdown, grouped by "region" or by "product", ranked highest revenue first.

    This is a slow, heavyweight analysis job, not something you'd want
    blocking the main agent's own model calls.
    """
    time.sleep(20)  # stands in for a genuinely slow job (a big pandas pipeline, a model call, etc.)
    key = group_by if group_by in ("region", "product") else "region"
    grouped = SALES.groupby(key)[["units_sold", "revenue"]].sum().sort_values("revenue", ascending=False)
    lines = [
        f"{name}: ${int(row['revenue']):,} revenue, {int(row['units_sold']):,} units"
        for name, row in grouped.iterrows()
    ]
    return "\n".join(lines)


model = ChatAnthropic(model="claude-haiku-4-5")

# langgraph.json points at this module-level variable: "./agent.py:graph"
graph = create_deep_agent(model=model, tools=[analyze_sales])
