# python/m4/m4_3_manuscript_agent.py
"""Module 4 · Lesson 3 — Dynamic subagents, "The Corrupted Manuscript" lab.

A handful of anachronistic sentences have been spliced into a combined,
public-domain corpus of the Iliad, Odyssey, and Aeneid (data/epic_corpus.txt
— see data/prepare_corpus.py for how it was built). The corpus is far too
large for one context window, so the main agent is given the interpreter and
a `book-scanner` subagent: it writes a workflow that reads the manuscript,
splits it on the normalized "=== EPIC BOOK N ===" headers, and dispatches one
scanner call per book, collecting whatever each one flags.

The corpus never enters the model's own context. Only `book-scanner`'s short,
distilled findings do — the interpreter holds the 2MB file, the model never
sees more than one book's worth of text (inside a subagent call) at a time.
"""

from pathlib import Path

from deepagents import FilesystemPermission, create_deep_agent
from deepagents.backends import FilesystemBackend
from langchain_quickjs import CodeInterpreterMiddleware

from models import model, strong_model

DATA_DIR = Path(__file__).resolve().parent / "data"

# --- The book-scanner subagent ----------------------------------------------
SCANNER_PROMPT = """You are proofreading one book of an ancient Greek or Roman
epic (Iliad, Odyssey, or Aeneid) for anachronistic sentences that a mischievous
editor spliced in — sentences referencing anything that couldn't exist in the
Bronze Age or classical antiquity (phones, vending machines, wristwatches,
espresso machines, and the like).

You will be given the book's label and its full text.

Return ONLY a JSON array of the exact anachronistic sentences you find, quoted
verbatim from the text (no paraphrasing, no partial quotes). Return `[]` if you
find none. Most books have none — don't force a match."""

book_scanner = {
    "name": "book-scanner",
    "description": (
        "Scan one book of the manuscript for anachronistic sentences. "
        "Delegate one book per call, passing that book's label and full text."
    ),
    "system_prompt": SCANNER_PROMPT,
    "model": model,  # cheaper Haiku 4.5 — this is a narrow, repeated task
}


# --- The main agent ----------------------------------------------------------
MANUSCRIPT_PROMPT = """You have access to a manuscript at /epic_corpus.txt: a
combined public-domain translation of the Iliad, Odyssey, and Aeneid. A
mischievous editor spliced a handful of anachronistic sentences into it.

The manuscript is split into 60 books, each starting with a line formatted
exactly as "=== EPIC BOOK N ===" (e.g. "=== ILIAD BOOK 9 ===").

Run a workflow that reads the manuscript, splits it into its 60 books, and
dispatches one book-scanner subagent call per book — never read a book's
full text into your own context; let the interpreter hold the file, and let
each subagent hold only its own book. Collect every subagent's findings into
one final report, grouped by "EPIC BOOK N", listing the anachronistic
sentence(s) found in that book (omit books with no findings)."""

# The scanner only needs read access to the one manuscript file — no writes.
manuscript_permissions = [
    FilesystemPermission(operations=["read"], paths=["/epic_corpus.txt"], mode="allow"),
    FilesystemPermission(operations=["read", "write"], paths=["/**"], mode="deny"),
]

agent = create_deep_agent(
    model=strong_model,
    middleware=[CodeInterpreterMiddleware()],
    system_prompt=MANUSCRIPT_PROMPT,
    subagents=[book_scanner],
    backend=FilesystemBackend(root_dir=DATA_DIR, virtual_mode=True),
    permissions=manuscript_permissions,
)
