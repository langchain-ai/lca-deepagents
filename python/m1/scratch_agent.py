import sys
from pathlib import Path
from langchain_community.utilities import SQLDatabase
from langchain_core.tools import tool
from deepagents import create_deep_agent
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from models import model

DB_PATH = Path(__file__).parent / "chinook.db"
db = SQLDatabase.from_uri(f"sqlite:///{DB_PATH}")

@tool
def execute_sql(query: str) -> str:
    """Execute a SQL query against the Chinook music store database.
    Tables: Album, Artist, Customer, Employee, Genre, Invoice,
    InvoiceLine, MediaType, Playlist, PlaylistTrack, Track.
    Use PRAGMA table_info(<table>) to inspect columns.
    Read-only: SELECT only. No INSERT, UPDATE, DELETE, or DROP."""
    try:
        return db.run(query)
    except Exception as e:
        return f"Error: {e}"

SYSTEM_PROMPT = """You are a careful SQL analyst with access to the Chinook music store database.

Rules:
- Think step-by-step before writing SQL.
- Call execute_sql with one SELECT query at a time.
- Read-only only: no INSERT, UPDATE, DELETE, ALTER, DROP, or CREATE.
- If the tool returns an error, revise the SQL and try again.
- Show your SQL in your final answer.
"""

agent = create_deep_agent(
    model=model,
    tools=[execute_sql],
    system_prompt=SYSTEM_PROMPT,
)

result = agent.invoke({"messages": [{"role": "user", "content": "What are the top 5 best-selling artists by total revenue?"}]})
print(result["messages"][-1].content)
