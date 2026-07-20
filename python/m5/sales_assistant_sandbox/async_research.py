# python/m5/sales_assistant_sandbox/async_research.py
"""AsyncSubAgentMiddleware wiring for the newsletter-agent async subagent.

Deliberately has no `from __future__ import annotations`: LangChain detects
which tool parameters to inject (like `ToolRuntime`) by reading the *raw*
`inspect.signature()` annotation on the tool's function
(`StructuredTool._injected_args_keys`), not `typing.get_type_hints()`. Under
`from __future__ import annotations` (used in agent.py), that annotation is
just the string `"ToolRuntime"`, which fails the injection check silently —
the tool then gets called without `runtime` and raises a `TypeError`. Kept
in a separate, future-import-free module rather than disabling the import in
agent.py, to avoid changing behavior for everything else already defined there.
"""

from datetime import UTC, datetime

from deepagents.middleware.async_subagents import (
    AsyncSubAgentMiddleware,
    AsyncTask,
    StartAsyncTaskSchema,
)
from langchain.tools import ToolRuntime
from langchain_core.messages import ToolMessage
from langchain_core.tools import StructuredTool
from langgraph.types import Command
from langgraph_sdk import get_client


def _build_notifying_start_tool(tool_description: str) -> StructuredTool:
    """Same as the stock `start_async_task` tool, but also tells
    newsletter-agent which main-agent thread to notify when it finishes.

    The stock tool (`deepagents.middleware.async_subagents`) has no field for
    the parent-thread callback — deliberately, since how a deployment passes
    parent context is deployment-specific. This adds exactly one thing: pass
    our own thread_id (and this graph's own fixed name in langgraph.json,
    "agent") as `config.configurable` on the launch call, so newsletter-agent's
    `CompletionNotifierMiddleware` knows where to call back.

    Only the async variant does real work: newsletter-agent runs in this same
    deployment (no `url`), and the SDK's sync client raises for `url=None`
    specs ("ASGI transport requires async invocation") — the sync `func` is
    unreachable here but required by `StructuredTool.from_function`.
    """

    async def astart_async_task(
        description: str,
        subagent_type: str,
        runtime: ToolRuntime,
    ) -> str | Command:
        if subagent_type != "newsletter-agent":
            return f"Unknown async subagent type `{subagent_type}`. Available types: `newsletter-agent`"
        client = get_client()
        thread = await client.threads.create()
        run = await client.runs.create(
            thread_id=thread["thread_id"],
            assistant_id="newsletter-agent",
            input={"messages": [{"role": "user", "content": description}]},
            config={
                "configurable": {
                    "parent_thread_id": runtime.config["configurable"]["thread_id"],
                    "parent_assistant_id": "agent",
                }
            },
        )
        task_id = thread["thread_id"]
        now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        task: AsyncTask = {
            "task_id": task_id,
            "agent_name": subagent_type,
            "thread_id": task_id,
            "run_id": run["run_id"],
            "status": "running",
            "created_at": now,
            "last_checked_at": now,
            "last_updated_at": now,
        }
        msg = f"Launched async subagent. task_id: {task_id}"
        return Command(
            update={
                "messages": [ToolMessage(msg, tool_call_id=runtime.tool_call_id)],
                "async_tasks": {task_id: task},
            }
        )

    def start_async_task(description: str, subagent_type: str, runtime: ToolRuntime) -> str:
        msg = "newsletter-agent only supports async invocation in this deployment."
        raise NotImplementedError(msg)

    return StructuredTool.from_function(
        name="start_async_task",
        func=start_async_task,
        coroutine=astart_async_task,
        description=tool_description,
        infer_schema=False,
        args_schema=StartAsyncTaskSchema,
    )


def build_async_research_middleware() -> AsyncSubAgentMiddleware:
    """`AsyncSubAgentMiddleware`, wired to the co-deployed newsletter-agent
    graph, with the stock `start_async_task` tool swapped for one that also
    passes our own thread_id (see `_build_notifying_start_tool`)."""
    middleware = AsyncSubAgentMiddleware(
        async_subagents=[
            {
                "name": "newsletter-agent",
                "description": (
                    "Research this week's featured music genres and assemble the "
                    "styled HTML newsletter in the background. Launch it once per "
                    "newsletter request and keep working; it reports back with the "
                    "finished HTML when done."
                ),
                "graph_id": "newsletter-agent",
            }
        ]
    )
    middleware.tools = [
        _build_notifying_start_tool(t.description) if t.name == "start_async_task" else t
        for t in middleware.tools
    ]
    return middleware
