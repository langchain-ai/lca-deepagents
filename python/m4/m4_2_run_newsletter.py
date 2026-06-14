# python/m4/m4_2_run_newsletter.py
"""Run the editor agent and save everything it produces.

Note on file handling: Deep Agents *can* be given real local disk access (via a
FilesystemBackend), but we deliberately don't. This agent runs on the default
StateBackend, so its writes land in agent state, not on your machine. Letting an
agent write to your filesystem is a permission you grant — and shouldn't, when
the agent is acting on untrusted web-search content. Instead, this trusted host
code reads the files out of agent state (the "files" channel) after invoke and
mirrors them to OUT_DIR: the finished newsletter plus each researcher's raw
/research/<genre>/ archive, so you can inspect what was quarantined there.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from m4_2_newsletter_agent import agent

OUT_DIR = Path(__file__).resolve().parent / "output"
OUT_DIR.mkdir(exist_ok=True)

result = agent.invoke(
    {"messages": [{"role": "user", "content": "Put together this week's newsletter."}]},
    config={"recursion_limit": 50},
)

# The editor's final reply (coordination summary).
print(result["messages"][-1].content)

# Everything the agent produced lives in agent state (not on your disk — it ran
# on a sandboxed StateBackend). Pull it all out and mirror it to OUT_DIR: the
# editor's newsletter AND each researcher's raw /research/<genre>/ archive.
files = result.get("files", {})
if "/output/newsletter.html" not in files:
    raise SystemExit("Agent did not write /output/newsletter.html")


def _content(fd) -> str:
    # FileData entries are dicts keyed by "content" (string, or legacy list).
    body = fd["content"] if isinstance(fd, dict) else fd
    return "\n".join(body) if isinstance(body, list) else body


out_root = OUT_DIR.resolve()
print("\nWriting agent files to disk:")
for path in sorted(files):
    # Map the in-state layout onto OUT_DIR: /output/* lands at the root,
    # /research/<genre>/* keeps its folder structure.
    rel = path[len("/output/"):] if path.startswith("/output/") else path.lstrip("/")
    dest = (OUT_DIR / rel).resolve()

    # The file contents are UNTRUSTED web-search text, and the path came from
    # the agent — so verify the destination stays inside OUT_DIR before writing
    # (reject any ../ traversal), and only ever write plain text.
    if dest != out_root and out_root not in dest.parents:
        print(f"  SKIPPED (escapes output dir): {path}")
        continue

    dest.parent.mkdir(parents=True, exist_ok=True)
    body = _content(files[path])
    dest.write_text(body, encoding="utf-8")
    print(f"  {path}  ->  {dest.relative_to(out_root)}  ({len(body):,} chars)")

print(f"\nOpen {OUT_DIR / 'newsletter.html'} in your browser to read this week's issue.")
