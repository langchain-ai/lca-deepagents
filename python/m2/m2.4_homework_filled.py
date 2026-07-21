# python/m2/m2.4_homework_filled.py
"""Reference copy of m2.4_homework.py with TODOs 1 and 2 filled in so you
can run it end to end and see what "done" looks like. This is just one
possible answer, so yours might be different. Explore!"""

import json
import sqlite3
import uuid
from pathlib import Path

from deepagents import create_deep_agent
from langchain.tools import tool
from langchain_quickjs import CodeInterpreterMiddleware

from models import model

DB_PATH = Path(__file__).resolve().parent / "chinook.db"

SYSTEM = (
    "You are a sales analyst for Chinook Digital Music Store. "
    "Use the query_chinook tool to query the database. "
    "Key tables: Artist(ArtistId, Name), Album(AlbumId, Title, ArtistId), "
    "Track(TrackId, Name, AlbumId, GenreId), Genre(GenreId, Name), "
    "Customer(CustomerId, FirstName, LastName, Country), "
    "Invoice(InvoiceId, CustomerId), "
    "InvoiceLine(InvoiceLineId, InvoiceId, TrackId, UnitPrice, Quantity). "
    "Revenue is InvoiceLine.UnitPrice * InvoiceLine.Quantity. "
    "The eval tool supports Programmatic Tool Calling (PTC): JavaScript "
    "running inside eval() can call query_chinook via tools.queryChinook()."
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


# TODO 1 filled in
TASK = (
    "Which country's customers generated the most total revenue, and what "
    "is the single best-selling track (by revenue) among customers from "
    "that country? Each answer depends on the previous one."
)


# TODO 2 filled in
def eval_answer(answer_text: str) -> None:
    """Independently compute the expected top country and top track, then
    check whether both show up in the agent's answer."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        top_country = conn.execute(
            """
            SELECT Customer.Country, SUM(InvoiceLine.UnitPrice * InvoiceLine.Quantity) AS rev
            FROM InvoiceLine
            JOIN Invoice USING(InvoiceId)
            JOIN Customer USING(CustomerId)
            GROUP BY Customer.Country
            ORDER BY rev DESC
            LIMIT 1
            """
        ).fetchone()
        top_track = conn.execute(
            """
            SELECT Track.Name, SUM(InvoiceLine.UnitPrice * InvoiceLine.Quantity) AS rev
            FROM InvoiceLine
            JOIN Invoice USING(InvoiceId)
            JOIN Customer USING(CustomerId)
            JOIN Track USING(TrackId)
            WHERE Customer.Country = ?
            GROUP BY Track.TrackId
            ORDER BY rev DESC
            LIMIT 1
            """,
            (top_country["Country"],),
        ).fetchone()
    finally:
        conn.close()

    print("\n--- Eval check ---")
    print(f"Expected top country: {top_country['Country']}")
    print(f"Expected top track: {top_track['Name']}")

    checks = {
        "mentions expected country": top_country["Country"].lower() in answer_text.lower(),
        "mentions expected track": top_track["Name"].lower() in answer_text.lower(),
    }
    for label, passed in checks.items():
        print(f"  [{'PASS' if passed else 'FAIL'}] {label}")


agent = create_deep_agent(
    model=model,
    tools=[query_chinook],
    middleware=[CodeInterpreterMiddleware(ptc=["query_chinook"])],
    system_prompt=SYSTEM,
)

result = agent.invoke(
    {"messages": [{"role": "user", "content": TASK}]},
    config={"configurable": {"thread_id": str(uuid.uuid4())}},
)

answer = result["messages"][-1].content
print(answer)
eval_answer(answer)
