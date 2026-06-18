import sys
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
from pathlib import Path
from langchain_community.utilities import SQLDatabase
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command
from deepagents import create_deep_agent
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
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
        return db.run(query)
    except Exception as e:
        return f"Error: {e}"

@tool
def write_sql(query: str) -> str:
    """Execute a write operation (INSERT, UPDATE, DELETE, ALTER) against the Chinook database.
    Requires human approval before executing."""
    approval = interrupt({"question": f"Approve this write?\n\n{query}"})
    if str(approval).strip().lower() not in ("yes", "y"):
        return "Write cancelled."
    try:
        return db.run(query)
    except Exception as e:
        return f"Error: {e}"

checkpointer = MemorySaver()

agent = create_deep_agent(
    model=model,
    tools=[read_sql, write_sql],
    system_prompt=SYSTEM_PROMPT,
    checkpointer=checkpointer,
)

config = {"configurable": {"thread_id": "lab3"}}

result = agent.invoke(
    {"messages": [{"role": "user", "content": "What genres are in the database? Then add a new genre called 'Synthwave'."}]},
    config=config,
)

while result.get("__interrupt__"):
    pending = result["__interrupt__"][0].value
    print(f"\nApproval required:\n{pending['question']}")
    approval = input("\nApprove? (yes/no): ").strip()
    result = agent.invoke(Command(resume=approval), config=config)

print(result["messages"][-1].content)
