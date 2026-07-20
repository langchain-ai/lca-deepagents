# python/m4/m4.3_homework.py
"""M4.3 Homework: Write Your Own Dynamic Subagent Workflow.

THE IDEA
The lab gave the main agent a 2MB manuscript split into labeled books and
had it write a "workflow" that dispatched one book-scanner subagent per
book, so the full corpus never entered the main model's own context. This
homework asks you to do the same shape of thing on a scenario YOU pick: a
synthetic "corpus" of your own, split into your own labeled sections, and a
subagent that scans each section for something OTHER than anachronisms (a
support-ticket log scanning for a specific complaint type, meeting notes
scanning for action items, a stack of reviews scanning for a recurring
complaint, whatever you're into). There's no single correct scenario here,
that's the point.

WHAT YOU FILL IN
  TODO 1: write your own corpus, a single string split into at least 5
    labeled sections using a consistent header format (like the lab's
    "=== EPIC BOOK N ===").
  TODO 2: write the section-scanner's system prompt (what should it flag in
    one section?) and the main agent's system prompt (telling it to run a
    workflow that splits your corpus and dispatches one scanner call per
    section).

RUN
  cd python
  uv run ./m4/m4.3_homework.py

NOTE
  This uses the code interpreter (langchain_quickjs), same as the lab. Make
  sure you've run `uv sync` from python/ so it's installed.
"""

from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langchain_quickjs import CodeInterpreterMiddleware

from models import model, strong_model

DATA_DIR = Path(__file__).resolve().parent / "homework_data"
DATA_DIR.mkdir(exist_ok=True)
CORPUS_PATH = DATA_DIR / "my_corpus.txt"


# ════════════════════════════════════════════════════════════════════════
# TODO 1: Write your own corpus.
#
# Requirements:
#   - A single string with at least 5 labeled sections.
#   - Pick a consistent header format, e.g. "=== SECTION N ===" or
#     "=== TICKET N ===", and stick to it exactly: the main agent's prompt
#     (TODO 2) needs to describe the same format so it can split on it.
#   - Plant something worth finding in a few of the sections (an off-topic
#     sentence, a specific keyword, whatever your scanner in TODO 2 is
#     looking for) so there's something for the workflow to actually
#     surface.
#
# Example shape (delete this and write your own):
#   return """\
#   === SECTION 1 ===
#   ...
#
#   === SECTION 2 ===
#   ...
#   """
# ════════════════════════════════════════════════════════════════════════

def build_corpus() -> str:
    """TODO 1: return your own corpus string with at least 5 sections."""
    raise NotImplementedError("TODO 1: see the comment block above")


CORPUS_PATH.write_text(build_corpus())


# ════════════════════════════════════════════════════════════════════════
# TODO 2: Write the scanner and main agent prompts.
#
# Return (scanner_prompt, main_prompt):
#   - scanner_prompt: what the section-scanner subagent should look for in
#     ONE section it's handed, and what it should return.
#   - main_prompt: tells the main agent about the corpus file, the header
#     format from TODO 1, and to run a WORKFLOW that splits the corpus and
#     dispatches one scanner call per section (the word "workflow" is what
#     triggers code-based dispatch, see the lesson).
# ════════════════════════════════════════════════════════════════════════

def build_prompts() -> tuple[str, str]:
    """TODO 2: return (scanner_prompt, main_prompt)."""
    raise NotImplementedError("TODO 2: see the comment block above")


SCANNER_PROMPT, MAIN_PROMPT = build_prompts()

section_scanner = {
    "name": "section-scanner",
    "description": (
        "Scan one section of the corpus for whatever the scanner prompt "
        "asks for. Delegate one section per call."
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
