import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
from pathlib import Path

from deepagents import create_deep_agent
from langchain_community.utilities import SQLDatabase
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from models import model

DB_PATH = Path(__file__).parent / "chinook.db"
db = SQLDatabase.from_uri(f"sqlite:///{DB_PATH}")

SYSTEM_PROMPT = """You are a SQL analyst with access to the Chinook music store database.

Rules:
- Use read_sql for all SELECT queries.
- Use write_sql for INSERT, UPDATE, DELETE, and ALTER operations.
- Think step-by-step. Read first, then write.
- If a tool returns an error, revise the SQL and try again.
- Show your SQL in your final answer.
"""

@tool
def read_sql(query: str) -> str:
    """Run a read-only SELECT query against the Chinook music store database."""
    try:
        return str(db.run(query))
    except Exception as e:
        return f"Error: {e}"

@tool
def write_sql(query: str) -> str:
    """Execute a write operation (INSERT, UPDATE, DELETE, ALTER) against the Chinook database.
    Requires human approval before executing."""
    try:
        return str(db.run(query))
    except Exception as e:
        return f"Error: {e}"

checkpointer = MemorySaver()

agent = create_deep_agent(
    model=model,
    name="SQL Agent",
    tools=[read_sql, write_sql],
    system_prompt=SYSTEM_PROMPT,
    checkpointer=checkpointer,
    interrupt_on={"write_sql": True},
)

config: RunnableConfig = {"configurable": {"thread_id": "lab3-demo"}}

result = agent.invoke(
    {"messages": [{"role": "user", "content": "What genres are in the database? Then add a new genre called 'Synthwave'."}]},
    config=config,
)

while result.get("__interrupt__"):
    pending = result["__interrupt__"][0].value
    for req in pending["action_requests"]:
        print(f"\nApproval required for {req['name']}:")
        print(f"  {req['args']}")
    approval = input("\nApprove? (yes/no): ").strip().lower()
    decision = "approve" if approval in ("yes", "y") else "reject"
    decisions = [{"type": decision} for _ in pending["action_requests"]]
    result = agent.invoke(Command(resume={"decisions": decisions}), config=config)

print(result["messages"][-1].content)
