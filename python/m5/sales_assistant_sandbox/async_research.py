# python/m5/sales_assistant_sandbox/async_research.py
"""AsyncSubAgentMiddleware wiring for the newsletter-agent async subagent."""

from deepagents.middleware.async_subagents import AsyncSubAgentMiddleware


def build_async_research_middleware() -> AsyncSubAgentMiddleware:
    """`AsyncSubAgentMiddleware`, wired to the co-deployed newsletter-agent
    graph, using the stock `start_async_task` tool unmodified — newsletter-agent
    doesn't need any parent-thread context passed in, so there's nothing to add
    to the launch call."""
    return AsyncSubAgentMiddleware(
        async_subagents=[
            {
                "name": "newsletter-agent",
                "description": (
                    "Research this week's featured music genres and assemble the "
                    "styled HTML newsletter in the background. Launch it once per "
                    "newsletter request and keep working; check back on it later "
                    "with `check_async_task`/`list_async_tasks` to get the finished "
                    "HTML."
                ),
                "graph_id": "newsletter-agent",
            }
        ]
    )
