# python/m2/agent.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from models import model
from deepagents import create_deep_agent, FilesystemPermission
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from deepagents.backends.utils import create_file_data
from langgraph.store.memory import InMemoryStore

store = InMemoryStore()

# Seed the Chinook sales skill
store.put(
    ("student",),
    "/skills/chinook-sales/SKILL.md",
    create_file_data("""\
---
name: chinook-sales
description: Act as a Chinook sales rep — answer questions about customers, invoices, and the music catalog.
---

You are a sales representative for Chinook Digital Music Store.

**Your responsibilities:**
- Look up customer accounts and purchase history
- Recommend music based on a customer's genre and artist preferences
- Answer questions about the catalog (artists, albums, tracks, pricing)
- Summarize invoice history for a customer

**Chinook schema (key tables):**
- `Customer` — CustomerId, FirstName, LastName, Email, SupportRepId
- `Employee` — EmployeeId, Title (e.g. "Sales Support Agent")
- `Invoice` — InvoiceId, CustomerId, InvoiceDate, Total
- `InvoiceLine` — InvoiceId, TrackId, UnitPrice, Quantity
- `Track` — TrackId, Name, AlbumId, GenreId, UnitPrice
- `Album` — AlbumId, Title, ArtistId
- `Artist` — ArtistId, Name
- `Genre` — GenreId, Name
"""),
)

agent = create_deep_agent(
    model=model,
    backend=CompositeBackend(
        default=StateBackend(),
        routes={
            "/memories/": StoreBackend(namespace=lambda _rt: ("student",)),
            "/skills/": StoreBackend(namespace=lambda _rt: ("student",)),
        },
    ),
    store=store,
    permissions=[
        FilesystemPermission(
            operations=["write"],
            paths=["/skills/**"],
            mode="deny",
        ),
    ],
)

result = agent.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": (
                    "Read the chinook-sales skill file, then add this note to it: "
                    "'Current promotion: 20% off all Jazz albums through end of month.'"
                ),
            }
        ]
    },
    config={"configurable": {"thread_id": "lab-m2.2"}},
)

print(result["messages"][-1].content)
