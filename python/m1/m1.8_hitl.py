from deepagents import create_deep_agent
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from models import model


@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email to a recipient."""
    return f"Email sent to {to} with subject {subject!r}. Body: {body}"


SYSTEM_PROMPT = """You are a helpful assistant that can send emails.

Rules:
- Use send_email when the user asks you to send an email.
- Keep emails concise and professional.
- Do not claim an email was sent until the tool result confirms it.
- When confirming an email was sent, quote the subject and body from the tool result, not the original request.
"""

agent = create_deep_agent(
    model=model,
    tools=[send_email],
    system_prompt=SYSTEM_PROMPT,
    interrupt_on={"send_email": True},
    checkpointer=MemorySaver(),
)

config = {"configurable": {"thread_id": "m1-8-hitl-demo"}}

result = agent.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "Send an email to jane@example.com saying I will be 10 minutes late.",
            }
        ]
    },
    config=config,
)

while result.get("__interrupt__"):
    pending = result["__interrupt__"][0].value
    decisions = []
    for req in pending["action_requests"]:
        print(f"\nApproval required for {req['name']}:")
        print(req["args"])

        choice = input("\nApprove, edit, or reject? (approve/edit/reject): ").strip().lower()
        if choice in ("approve", "yes", "y"):
            decisions.append({"type": "approve"})
        elif choice in ("edit", "e"):
            edited_args = dict(req["args"])
            edited_args["body"] = input("New email body: ")
            decisions.append(
                {
                    "type": "edit",
                    "edited_action": {"name": req["name"], "args": edited_args},
                }
            )
        else:
            decisions.append(
                {"type": "reject", "message": "User rejected this email draft."}
            )

    result = agent.invoke(Command(resume={"decisions": decisions}), config=config)

for msg in result["messages"]:
    if hasattr(msg, "name") and msg.name == "send_email":
        print(msg.content)
        break
