import json
import sqlite3
import uuid
from pathlib import Path

from deepagents import create_deep_agent
from langchain.tools import tool
from langchain_quickjs import CodeInterpreterMiddleware

from models import model

DB_PATH = Path(__file__).resolve().parent / "chinook.db"

TASK = (
    "Who is our top-selling artist, what is their best-selling album, "
    "what is the most-purchased track on that album, "
    "and how many distinct customers have bought that track? "
    "Each answer depends on the result of the previous query."
)

SYSTEM = (
    "You are a sales analyst for Chinook Digital Music Store. "
    "Use the query_chinook tool to query the database. "
    "Key tables: Artist(ArtistId, Name), Album(AlbumId, Title, ArtistId), "
    "Track(TrackId, Name, AlbumId), "
    "InvoiceLine(InvoiceLineId, InvoiceId, TrackId, UnitPrice, Quantity). "
    "Revenue is InvoiceLine.UnitPrice * InvoiceLine.Quantity."
)


@tool
def query_chinook(sql: str) -> str:
    """Execute a read-only SQL query against the Chinook database. Returns a JSON-encoded string."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.execute(sql)
        rows = [dict(row) for row in cursor.fetchall()]
        return json.dumps(rows)
    finally:
        conn.close()


# --- Agent with interpreter ---
# Additional information is added to the system prompt to guide the agent to use
# the interpreter as well as some hints on how to use it.

agent_with = create_deep_agent(
    model=model,
    tools=[query_chinook],
    middleware=[CodeInterpreterMiddleware(ptc=["query_chinook"])],
    system_prompt=(
        SYSTEM
        + " The eval tool supports Programmatic Tool Calling (PTC): JavaScript"
        " running inside eval() can call query_chinook via tools.queryChinook()."
        " For dependent queries where each answer requires a result from the"
        " previous, prefer a single eval() call that chains all queries in"
        " JavaScript — intermediate values stay in variables and never return to the model."
    ),
)

result_with = agent_with.invoke(
    {"messages": [{"role": "user", "content": TASK}]},
    config={"configurable": {"thread_id": str(uuid.uuid4())}},
)

print("=== With interpreter ===")
print(result_with["messages"][-1].content)

# --- Agent without interpreter ---

agent_without = create_deep_agent(
    model=model,
    tools=[query_chinook],
    system_prompt=SYSTEM,
)

result_without = agent_without.invoke(
    {"messages": [{"role": "user", "content": TASK}]},
    config={"configurable": {"thread_id": str(uuid.uuid4())}},
)

print("\n=== Without interpreter ===")
print(result_without["messages"][-1].content)
