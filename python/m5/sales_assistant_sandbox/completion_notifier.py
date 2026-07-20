# python/m5/sales_assistant_sandbox/completion_notifier.py
"""Completion notifier middleware for an async subagent graph.

Ported nearly verbatim from the official reference implementation:
https://github.com/langchain-ai/async-deep-agents (graphs/python/src/middleware/completion_notifier.py)

When the subagent it's attached to finishes (success or error), this
middleware sends a message to the parent's thread so it wakes up and can act
on the result without being polled. Generic — used by newsletter-agent (see
`newsletter_agent_graph.py`), the only async subagent graph in this project,
but not specific to it.

`deepagents.AsyncSubAgentMiddleware` does not include a built-in notification
mechanism — by default the parent only learns about completion when it calls
`check_async_task`/`list_async_tasks`. This middleware closes that gap by
pushing a notification from the subagent back to the parent.

`parent_thread_id`/`parent_assistant_id` are supplied at graph-build time by
the subagent graph's own factory, which reads them from `config.configurable`
— values written by our own custom `start_async_task` tool in
`async_research.py`, never from end-user input.
"""

from __future__ import annotations

import logging
from typing import Any

from langchain.agents.middleware.types import AgentMiddleware, Runtime
from langgraph_sdk import get_client

logger = logging.getLogger(__name__)


async def _notify_parent(
    parent_thread_id: str,
    parent_assistant_id: str,
    notification: str,
    subagent_name: str,
) -> None:
    """Send a notification run to the parent's thread.

    Uses `get_client()` with no URL, which resolves to ASGI in-process
    transport since both graphs live in the same deployment.
    """
    try:
        client = get_client()
        await client.runs.create(
            thread_id=parent_thread_id,
            assistant_id=parent_assistant_id,
            input={"messages": [{"role": "user", "content": notification}]},
        )
        logger.info(
            "Notified parent thread %s that subagent '%s' finished",
            parent_thread_id,
            subagent_name,
        )
    except Exception:
        logger.warning("Failed to notify parent thread %s", parent_thread_id, exc_info=True)


class CompletionNotifierMiddleware(AgentMiddleware):
    """Notifies the main agent's thread when this subagent completes or errors.

    Add this as the last middleware in the subagent's stack so it fires after
    all other middleware has run.

    Args:
        parent_thread_id: The main agent's thread ID to notify.
        parent_assistant_id: The main agent's assistant ID (needed to create a run).
        subagent_name: Human-readable name for log messages and notifications.
    """

    def __init__(
        self,
        parent_thread_id: str | None,
        parent_assistant_id: str | None,
        subagent_name: str | None = None,
    ):
        self.parent_thread_id = parent_thread_id
        self.parent_assistant_id = parent_assistant_id
        self.subagent_name = subagent_name or "subagent"
        self._notified = False

    def _should_notify(self) -> bool:
        return not self._notified and bool(self.parent_thread_id) and bool(self.parent_assistant_id)

    async def _send_notification(self, message: str) -> None:
        if not self._should_notify():
            return
        self._notified = True
        await _notify_parent(self.parent_thread_id, self.parent_assistant_id, message, self.subagent_name)

    def _extract_last_message(self, state: dict[str, Any]) -> str:
        """Extract a summary from the subagent's final message."""
        messages = state.get("messages", [])
        if not messages:
            return "(no output)"
        last = messages[-1]
        if hasattr(last, "content"):
            content = last.content
            return content[:500] if isinstance(content, str) else str(content)[:500]
        if isinstance(last, dict):
            return str(last.get("content", ""))[:500]
        return str(last)[:500]

    async def aafter_agent(self, state: dict[str, Any], runtime: Runtime) -> dict[str, Any] | None:
        """After-agent hook: fires when the subagent run completes successfully."""
        summary = self._extract_last_message(state)
        await self._send_notification(f"[Async subagent '{self.subagent_name}' has completed] Result: {summary}")
        return None

    async def awrap_model_call(self, request, handler):
        """Wrap-model-call hook: catches errors and notifies the main agent."""
        try:
            return await handler(request)
        except Exception as e:
            await self._send_notification(f"[Async subagent '{self.subagent_name}' encountered an error] Error: {e!s}")
            raise


def build_completion_notifier(
    parent_thread_id: str | None,
    parent_assistant_id: str | None,
    subagent_name: str | None = None,
) -> CompletionNotifierMiddleware:
    """Build a completion notifier middleware scoped to one run."""
    return CompletionNotifierMiddleware(
        parent_thread_id=parent_thread_id,
        parent_assistant_id=parent_assistant_id,
        subagent_name=subagent_name,
    )
