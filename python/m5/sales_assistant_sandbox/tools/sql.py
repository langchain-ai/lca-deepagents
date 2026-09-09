# python/m5/tools/sql.py
"""SQL tools for the chinook-analyst subagent.

Three tools, with the database's trust boundary baked in:

* ``query_chinook``    — read-only SELECTs. The connection is opened in SQLite
  read-only URI mode AND the statement is checked to be a single SELECT, so a
  model-generated query can never mutate or drop anything.
* ``introspect_schema`` — returns the full DDL so the analyst can learn (and
  then memorize) the schema on first use.
* ``add_customer``     — the one write path: a parameterized INSERT into
  Customer only, scoped to the logged-in rep. It is gated by a human-in-the-loop
  approval (configured where the subagent is built), so no row is added without
  an explicit yes.

Model-generated SQL is treated as untrusted input throughout.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from langchain.tools import tool

# The database ships with the agent under data/. Read path uses a read-only URI
# so even a creative SELECT (e.g. a sqlite PRAGMA write) cannot change the file.
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "chinook.db"
_RO_URI = f"file:{DB_PATH}?mode=ro"

# The persona: Jane Peacock, Sales Support Agent. "My customers" = SupportRepId.
REP_EMPLOYEE_ID = 3

# Statements that may not appear in a read-only query, as defense in depth on
# top of the read-only connection.
_FORBIDDEN = (
    "insert", "update", "delete", "drop", "alter", "create",
    "replace", "truncate", "attach", "detach", "pragma", "vacuum",
)


def _read_only_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(_RO_URI, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


@tool
def query_chinook(sql: str) -> str:
    """Run a read-only SQL SELECT against the Chinook database.

    Returns a JSON array of row objects. Only a single SELECT statement is
    allowed — any attempt to modify the database is rejected. Use this for all
    lookups: catalogue prices, a customer's purchase history, territory
    metrics, and so on.
    """
    stripped = sql.strip().rstrip(";").strip()
    lowered = stripped.lower()

    if not lowered.startswith(("select", "with")):
        return json.dumps({"error": "Only SELECT queries are allowed."})
    if ";" in stripped:
        return json.dumps({"error": "Only a single statement is allowed."})
    if any(f" {word} " in f" {lowered} " for word in _FORBIDDEN):
        return json.dumps({"error": "Query contains a forbidden (write) keyword."})

    conn = _read_only_connection()
    try:
        rows = [dict(r) for r in conn.execute(stripped).fetchall()]
        return json.dumps(rows, default=str)
    except sqlite3.Error as exc:
        return json.dumps({"error": f"SQL error: {exc}"})
    finally:
        conn.close()


@tool
def introspect_schema() -> str:
    """Return the full database schema (CREATE statements for every table).

    Call this once to learn the schema, then record it in your memory so you
    don't have to rediscover it on every task.
    """
    conn = _read_only_connection()
    try:
        rows = conn.execute(
            "SELECT name, sql FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
        return "\n\n".join(r["sql"] for r in rows if r["sql"])
    finally:
        conn.close()


@tool
def add_customer(
    first_name: str,
    last_name: str,
    email: str,
    company: str = "",
    city: str = "",
    state: str = "",
    country: str = "",
    phone: str = "",
) -> str:
    """Add a NEW customer to the database, assigned to the current sales rep.

    Use this only after confirming the customer is not already in the system
    (search by email or name first). A human approves this write before it
    runs. Returns the new CustomerId on success.
    """
    if not email or "@" not in email:
        return json.dumps({"error": "A valid email is required."})

    # Parameterized insert into Customer only. No other table is reachable and
    # the rep assignment is forced server-side, not taken from the model.
    conn = sqlite3.connect(DB_PATH)
    try:
        # Guard against duplicates on email.
        existing = conn.execute(
            "SELECT CustomerId FROM Customer WHERE lower(Email) = lower(?)", (email,)
        ).fetchone()
        if existing:
            return json.dumps(
                {"error": f"Customer with email {email} already exists "
                          f"(CustomerId {existing[0]})."}
            )

        cursor = conn.execute(
            """
            INSERT INTO Customer
                (FirstName, LastName, Company, City, State, Country, Phone,
                 Email, SupportRepId)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                first_name,
                last_name,
                company or None,
                city or None,
                state or None,
                country or None,
                phone or None,
                email,
                REP_EMPLOYEE_ID,
            ),
        )
        conn.commit()
        return json.dumps(
            {"status": "created", "customer_id": cursor.lastrowid,
             "name": f"{first_name} {last_name}", "email": email}
        )
    except sqlite3.Error as exc:
        return json.dumps({"error": f"SQL error: {exc}"})
    finally:
        conn.close()
