import questionary
from deepagents import create_deep_agent
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from models import model


@tool
def ask_user(question: str, choices: list[str]) -> str:
    """Ask the user a clarifying question with a fixed set of choices."""
    return f"[No response recorded for: {question}]"


@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email to a recipient."""
    return f"Email sent to {to} with subject {subject!r}. Body: {body}"


SYSTEM_PROMPT = """You are a helpful assistant that can send emails.

Rules:
- If the user's request depends on a choice only they can make, call ask_user
  with the question and the list of choices before drafting anything.
- Use the ask_user response to decide what the email should say.
- Use send_email when you are ready to send.
- Keep emails concise and professional.
- Do not claim an email was sent until the tool result confirms it.
- When confirming an email was sent, quote the subject and body from the tool result, not the original request.
"""

agent = create_deep_agent(
    model=model,
    tools=[ask_user, send_email],
    system_prompt=SYSTEM_PROMPT,
    interrupt_on={
        "ask_user": {"allowed_decisions": ["respond"]},
        "send_email": {"allowed_decisions": ["approve", "edit", "reject"]},
    },
    checkpointer=MemorySaver(),
)

config = {"configurable": {"thread_id": "m1-8-hitl-respond-demo"}}

result = agent.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": (
                    "Email professor.chen@university.edu that I'll be late, but first "
                    "check whether I should just apologize or ask for a short extension."
                ),
            }
        ]
    },
    config=config,
    version="v2",
)

while result.interrupts:
    pending = result.interrupts[0].value
    decisions = []
    for req in pending["action_requests"]:
        if req["name"] == "ask_user":
            selected = questionary.select(
                req["args"]["question"],
                choices=req["args"]["choices"],
            ).ask()
            decisions.append({"type": "respond", "message": selected})

        elif req["name"] == "send_email":
            print(f"\nApproval required for {req['name']}:")
            print(req["args"])

            action = questionary.select(
                "How do you want to handle this email?",
                choices=["approve", "edit", "reject"],
            ).ask()

            if action == "approve":
                decisions.append({"type": "approve"})
            elif action == "edit":
                edited_args = dict(req["args"])
                edited_args["body"] = questionary.text("New email body:").ask()
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

    result = agent.invoke(Command(resume={"decisions": decisions}), config=config, version="v2")

for msg in result.value["messages"]:
    if hasattr(msg, "name") and msg.name == "send_email":
        print(msg.content)
        break
