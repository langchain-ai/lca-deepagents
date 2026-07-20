# python/m4/m4.3_homework_filled.py
"""Reference copy of m4.3_homework.py with TODOs 1 and 2 filled in so you
can run it end to end and see what "done" looks like. This is just one
possible answer, so yours might be different. Explore!"""

from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langchain_quickjs import CodeInterpreterMiddleware

from models import model, strong_model

DATA_DIR = Path(__file__).resolve().parent / "homework_data"
DATA_DIR.mkdir(exist_ok=True)
CORPUS_PATH = DATA_DIR / "my_corpus.txt"


# TODO 1 filled in
def build_corpus() -> str:
    return """\
=== TICKET 1 ===
Customer says the app crashes every time they open the settings page on
Android 14. Includes a screenshot of the error.

=== TICKET 2 ===
Customer was charged twice for their monthly subscription this billing
cycle and wants one of the charges refunded.

=== TICKET 3 ===
Customer is asking how to export their data to a CSV file before they
cancel their account.

=== TICKET 4 ===
Customer's invoice shows a charge for a plan they downgraded from two
months ago; they want the difference refunded.

=== TICKET 5 ===
Customer reports that search results are sorted incorrectly when filtering
by date instead of relevance.

=== TICKET 6 ===
Customer says a promo code was applied but they were still billed the full
price, and they'd like a refund for the discount amount.

=== TICKET 7 ===
Customer wants to know if there's a dark mode planned for the mobile app.
"""


CORPUS_PATH.write_text(build_corpus())


# TODO 2 filled in
def build_prompts() -> tuple[str, str]:
    scanner_prompt = """You are reviewing one customer support ticket for
billing complaints: any mention of being overcharged, charged twice, billed
the wrong amount, or requesting a refund because of an incorrect charge.

You will be given one ticket's label and its full text.

Return ONLY a JSON object: {"is_billing_complaint": true/false, "summary":
"<one sentence, or empty string if false>"}. If the ticket is not about a
billing problem, return is_billing_complaint: false."""

    main_prompt = """You have access to a support ticket log at
/my_corpus.txt: a set of tickets, each starting with a line formatted
exactly as "=== TICKET N ===".

Run a workflow that reads the file, splits it into its individual tickets,
and dispatches one section-scanner subagent call per ticket — never read a
ticket's full text into your own context; let the interpreter hold the
file, and let each subagent hold only its own ticket. Collect every
subagent's findings into one final report listing only the tickets flagged
as billing complaints, with their one-sentence summaries."""

    return scanner_prompt, main_prompt


SCANNER_PROMPT, MAIN_PROMPT = build_prompts()

section_scanner = {
    "name": "section-scanner",
    "description": (
        "Scan one support ticket for billing complaints. Delegate one "
        "ticket per call."
    ),
    "system_prompt": SCANNER_PROMPT,
    "model": model,
}

agent = create_deep_agent(
    model=strong_model,
    middleware=[CodeInterpreterMiddleware()],
    system_prompt=MAIN_PROMPT,
    subagents=[section_scanner],
    backend=FilesystemBackend(root_dir=DATA_DIR, virtual_mode=True),
)

result = agent.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "Run a workflow to scan every section of my_corpus.txt and report what you find.",
            }
        ]
    },
    config={"recursion_limit": 100},
)
print(result["messages"][-1].content)
