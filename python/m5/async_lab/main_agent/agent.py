# python/m5/async_lab/main_agent/agent.py
"""M5.4 Lab: the main agent, delegating to a separate, specialized deployment.

THE IDEA
This agent stays light: it pulls the shared model from the course's
models.py and depends on the same shared environment every other lab in
the course uses. It delegates all sales analysis to an async
subagent, "analyst", running as its OWN deployment on port 2025 (see
../specialized_agent). That deployment carries a heavier dependency
(pandas) this agent never needs to install.

RUN
  Start ../specialized_agent first (see its own docstring), then:
    cd python/m5/async_lab/main_agent
    uv run langgraph dev
Chat with it in the Studio window that opens. Ask it to run two analyses
at once (e.g. by region and by product), then keep chatting, it should
report two task_ids right away. From there you can update one task with
new instructions, cancel the other, and check on what's left.
"""

from deepagents import AsyncSubAgent, create_deep_agent
from models import model

async_subagents = [
    AsyncSubAgent(
        name="analyst",
        description=(
            "Runs sales analysis grouped by region or by product, returning total "
            "revenue and units sold per group, ranked by revenue - that's all the "
            "data available, so don't ask it for anything else (e.g. average "
            "transaction value, transaction counts, or growth metrics). Slow (it's "
            "a heavyweight pandas job), so it lives on its own deployment instead "
            "of running in-process here. Launch one task per grouping if you need "
            "both."
        ),
        graph_id="agent",
        url="http://127.0.0.1:2025",
    ),
]

# langgraph.json points at this module-level variable: "./agent.py:graph"
graph = create_deep_agent(model=model, subagents=async_subagents)
