import json
import sqlite3
from pathlib import Path

from deepagents import create_deep_agent
from langchain.tools import tool
from langchain_quickjs import CodeInterpreterMiddleware

from models import model

DB_PATH = Path(__file__).resolve().parent / "chinook.db"


@tool
def query_chinook(sql: str) -> str:
    """Execute a read-only SQL query against the Chinook database. Returns JSON array of rows."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.execute(sql)
        rows = [dict(row) for row in cursor.fetchall()]
        return json.dumps(rows)
    finally:
        conn.close()


agent = create_deep_agent(
    model=model,
    tools=[query_chinook],
    middleware=[CodeInterpreterMiddleware(ptc=["query_chinook"])],
    system_prompt=(
        "You are a sales analyst for Chinook Digital Music Store. "
        "Use the query_chinook tool to query the database and the eval tool "
        "to process results programmatically with JavaScript. "
        "Key tables: Genre(GenreId, Name), Track(TrackId, Name, GenreId), "
        "InvoiceLine(InvoiceLineId, InvoiceId, TrackId, UnitPrice, Quantity). "
        "When joining tables, qualify revenue as InvoiceLine.UnitPrice * InvoiceLine.Quantity."
    ),
)

result = agent.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": (
                    "Use a single eval() call with programmatic tool calling to do this: "
                    "First query the top 5 genres by total revenue. "
                    "Then, for each of those genres, make a second query to find the "
                    "top-selling track in that genre. "
                    "The second set of queries should be driven by the results of the first — "
                    "use Promise.all so they run in parallel. "
                    "Return a formatted list showing each genre, its total revenue, "
                    "and its top track."
                ),
            }
        ]
    },
    config={"configurable": {"thread_id": "lab-m2.4"}},
)

print(result["messages"][-1].content)
