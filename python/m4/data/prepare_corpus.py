# python/m4/data/prepare_corpus.py
"""One-time prep script for the Module 4.3 "Corrupted Manuscript" lab.

Downloads three public-domain prose translations from Project Gutenberg,
strips their HTML/boilerplate down to plain text, normalizes each of the 60
book headers to one consistent format, splices in a fixed set of
anachronistic "corrupted" sentences at uneven positions, and writes:

  epic_corpus.txt  — the combined, corrupted corpus students dispatch against
  epic_corpus_key.json — the seeded corruptions and which book each lives in

Sources (all public domain in the US; translators long deceased):
  - The Iliad, tr. Samuel Butler (1898)   — Project Gutenberg #2199
  - The Odyssey, tr. Samuel Butler (1900) — Project Gutenberg #1727
  - The Aeneid, tr. J. W. Mackail (1885)  — Project Gutenberg #22456

This script is not part of the lab itself — the two files above are already
checked into this directory. Re-run it only if you want to regenerate them
(e.g. to change the seeded corruptions).
"""

import json
import re
import urllib.request
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent

SOURCES = {
    "ILIAD": {
        "url": "https://www.gutenberg.org/files/2199/2199-h/2199-h.htm",
        "heading": re.compile(r'<h2><a id="chap(\d+)"></a>BOOK ([IVXLC]+)\.</h2>'),
        "count": 24,
    },
    "ODYSSEY": {
        "url": "https://www.gutenberg.org/files/1727/1727-h/1727-h.htm",
        "heading": re.compile(r'<h2><a name="chap(\d+)"></a>\s*BOOK ([IVXLC]+)</h2>'),
        "count": 24,
    },
    "AENEID": {
        "url": "https://www.gutenberg.org/files/22456/22456-h/22456-h.htm",
        "heading": re.compile(r'<h2><a name="BOOK_\w+" id="BOOK_\w+"></a>BOOK \w+</h2>'),
        "count": 12,
    },
}

# Seeded corruptions: (epic, book_number, sentence, position="middle"/"end").
# Deliberately uneven — several books get two, most get zero.
CORRUPTIONS = [
    ("ILIAD", 2, "A vending machine hummed faintly beside the Scaean gates."),
    ("ILIAD", 9, "Patroclus adjusted his smartwatch before donning the borrowed armor."),
    ("ILIAD", 9, "Achilles paused to check his bronze pager before returning to the battle line."),
    ("ILIAD", 16, "Somewhere beyond the ships, a food truck sold roasted chestnuts to the Myrmidons."),
    ("ILIAD", 23, "Hector paused to refresh his podcast feed before facing Achilles."),
    ("ODYSSEY", 1, "Telemachus updated his status to 'it's complicated' before the suitors arrived."),
    ("ODYSSEY", 5, "Odysseus checked his phone for a signal before addressing the Cyclops."),
    ("ODYSSEY", 12, "The sirens' song briefly buffered (because the free version has ads) before resuming its melody."),
    ("ODYSSEY", 12, "Circe's swine wore tiny name tags that read 'Hello, my name is.'"),
    ("ODYSSEY", 20, "Penelope scrolled through a catalog of suitors on her tablet."),
    ("AENEID", 2, "Dido kept a small espresso machine in the corner of her palace."),
    ("AENEID", 2, "Aeneas glanced at Google Maps of the Mediterranean before setting sail."),
    ("AENEID", 7, "A traffic light blinked uselessly at the gates of Latium."),
    ("AENEID", 11, "Turnus paused to check the weather forecast before the final duel."),
]

TAG_RE = re.compile(r"<[^>]+>")
PG_MARKER_RE = re.compile(r"\*\*\* (START|END) OF THE PROJECT GUTENBERG EBOOK.*?\*\*\*")
PAGE_MARKER_RE = re.compile(r"\[Pg \d+\]")
BLANK_RUN_RE = re.compile(r"\n{3,}")


def fetch(url: str) -> str:
    with urllib.request.urlopen(url, timeout=30) as resp:
        return resp.read().decode("utf-8")


def strip_html(chunk: str) -> str:
    # Force real paragraph breaks at </p> boundaries *before* the generic tag
    # strip below, since surrounding whitespace in the source HTML is too
    # inconsistent to rely on for splitting paragraphs later.
    chunk = re.sub(r"</p\s*>", "\n\n", chunk)
    chunk = re.sub(r"<br\s*/?>", "\n", chunk)
    text = TAG_RE.sub(" ", chunk)
    text = PAGE_MARKER_RE.sub("", text)
    import html as html_module
    text = html_module.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = BLANK_RUN_RE.sub("\n\n", text)
    return text.strip()


def split_books(epic: str, raw: str) -> dict:
    """Return {book_number: plain_text} for one epic's raw HTML."""
    start = PG_MARKER_RE.search(raw)
    body = raw[start.end():] if start else raw
    cfg = SOURCES[epic]
    matches = list(cfg["heading"].finditer(body))
    books = {}
    for i, m in enumerate(matches):
        book_num = i + 1  # headings appear in book order
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        books[book_num] = strip_html(body[m.end():end])
    if len(books) != cfg["count"]:
        raise RuntimeError(f"{epic}: expected {cfg['count']} books, found {len(books)}")
    return books


def splice_corruption(text: str, sentence: str, slot: int, slots_in_book: int) -> str:
    """Insert `sentence` at the end of a paragraph roughly slot/slots_in_book
    of the way through the book, so multiple corruptions in one book land at
    different spots rather than piling up in the same paragraph."""
    paragraphs = [p for p in text.split("\n\n") if p.strip()]
    idx = min(len(paragraphs) - 1, max(0, (len(paragraphs) * slot) // (slots_in_book + 1)))
    paragraphs[idx] = paragraphs[idx].rstrip() + " " + sentence
    return "\n\n".join(paragraphs)


def main():
    all_books = {}
    for epic in SOURCES:
        print(f"Fetching {epic}...")
        raw = fetch(SOURCES[epic]["url"])
        all_books[epic] = split_books(epic, raw)
        print(f"  {len(all_books[epic])} books extracted")

    # Group corruptions by (epic, book) to assign distinct slots within a book.
    slots_used = {}
    key_entries = []
    for epic, book_num, sentence in CORRUPTIONS:
        slot_key = (epic, book_num)
        slots_used[slot_key] = slots_used.get(slot_key, 0) + 1
    slot_counter = {}
    for epic, book_num, sentence in CORRUPTIONS:
        slot_key = (epic, book_num)
        slot_counter[slot_key] = slot_counter.get(slot_key, 0) + 1
        total_slots = slots_used[slot_key]
        all_books[epic][book_num] = splice_corruption(
            all_books[epic][book_num], sentence, slot_counter[slot_key], total_slots
        )
        key_entries.append({"epic": epic, "book": book_num, "sentence": sentence})

    # Assemble the combined corpus in epic order: Iliad, Odyssey, Aeneid.
    parts = []
    for epic in ("ILIAD", "ODYSSEY", "AENEID"):
        for book_num in sorted(all_books[epic]):
            parts.append(f"=== {epic} BOOK {book_num} ===\n\n{all_books[epic][book_num]}")
    corpus = "\n\n".join(parts) + "\n"

    corpus_path = OUT_DIR / "epic_corpus.txt"
    corpus_path.write_text(corpus, encoding="utf-8")
    key_path = OUT_DIR / "epic_corpus_key.json"
    key_path.write_text(json.dumps(key_entries, indent=2), encoding="utf-8")

    print(f"\nWrote {corpus_path} ({len(corpus):,} chars, ~{len(corpus.split()):,} words)")
    print(f"Wrote {key_path} ({len(key_entries)} seeded corruptions)")


if __name__ == "__main__":
    main()
