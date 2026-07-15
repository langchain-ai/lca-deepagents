# python/m1/homework/judge_card_helpers.py
"""Provided setup for judge_card_homework.py: the quiz, the ASCII card
renderer, persona styling, the "publish" tool, and the invoke/interrupt-
resume loop.

Nothing in here is a TODO. Read render_card()'s docstring if you want to
restyle a card, otherwise you shouldn't need to open this file.
"""

from __future__ import annotations

import os
import re
import textwrap
from pathlib import Path

import questionary
import requests
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from deepagents import create_deep_agent

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

RESET = "\033[0m"
BOLD = "\033[1m"
DEFAULT_COLOR = "\033[92m"  # bright green (unstyled personas, e.g. your own)

DEFAULT_MASCOT = "\n".join([
    " ___",
    "[o_o]",
    "/|_|\\",
    " | |",
])

# The 3 fixed personality axes the quiz scores you on. Each trait score
# (0-100, from score_and_match in judge_card_homework.py) says how far
# toward the *right* label you land.
TRAIT_AXES = [("Chaotic", "Organized"), ("Cautious", "Bold"), ("Solo", "Collaborative")]

# 8 fixed quiz questions. Each choice carries a (chaotic/organized,
# cautious/bold, solo/collaborative) delta applied to a running score that
# starts at 50 per axis.
QUIZ_QUESTIONS = [
    {
        "question": "It's 9am, you have 3 unread pings and one big task due today.",
        "choices": [
            ("Reply to all three immediately, big task can wait", (-2, 0, 2)),
            ("Silence notifications, focus on the big task first", (2, 0, -2)),
            ("Skim them, answer only the urgent one, then dive in", (0, 1, 0)),
        ],
    },
    {
        "question": "You find a bug in code you didn't write. It's not blocking you.",
        "choices": [
            ("Fix it immediately, mid-task", (-1, 2, 0)),
            ("File a ticket, get back to what you were doing", (1, -1, 1)),
            ("Leave a comment, let the original author decide", (0, -2, 1)),
        ],
    },
    {
        "question": "Your project's plan just changed with zero warning.",
        "choices": [
            ("Thrilling. Let's improvise.", (-2, 1, 0)),
            ("Panic quietly, then rebuild the plan from scratch.", (2, -1, 0)),
            ("Ask the team what changed and why before reacting.", (0, 0, 2)),
        ],
    },
    {
        "question": "How do you feel about shipping code you haven't fully tested?",
        "choices": [
            ("Ship it, fix forward.", (-1, 2, 0)),
            ("Absolutely not, I need to be sure.", (1, -2, 0)),
            ("Depends who's watching the deploy.", (0, 0, 1)),
        ],
    },
    {
        "question": "Pick your ideal work session:",
        "choices": [
            ("Solo, headphones on, no meetings.", (0, 0, -2)),
            ("Pair programming, thinking out loud with someone.", (0, 0, 2)),
            ("Whiteboarding with the whole team.", (-1, 1, 2)),
        ],
    },
    {
        "question": "Someone asks you to review their PR right now.",
        "choices": [
            ("Sure, dropping what I'm doing to look now.", (0, -1, 2)),
            ("I'll finish my current task first, then review.", (1, 0, 0)),
            ("Skim it fast, leave a couple comments, move on.", (-1, 0, 1)),
        ],
    },
    {
        "question": "Your build just failed in CI. What's your first move?",
        "choices": [
            ("Re-run it, probably flaky.", (-1, 1, 0)),
            ("Read the full log before touching anything.", (1, -1, 0)),
            ("Ping whoever touched that file last.", (0, 0, 2)),
        ],
    },
    {
        "question": "How do you feel about writing documentation?",
        "choices": [
            ("Write it as I go, future me will thank me.", (1, -1, 0)),
            ("I'll write it eventually. Probably.", (-2, 1, -1)),
            ("Only if someone else is going to read it soon.", (0, 0, 1)),
        ],
    },
]

# One real LangChain product per axis-leaning direction, keyed lowercase.
# (See https://docs.langchain.com for the full product lineup.) This
# lookup is what decides which product you get - TODO 3's MCP call only
# describes whichever product this table already picked, it doesn't
# choose it.
PRODUCT_MATCHES = {
    "chaotic": "Fleet",
    "organized": "Evaluation",
    "cautious": "Observability",
    "bold": "Engine",
    "solo": "Sandboxes",
    "collaborative": "Deployment",
}


def run_quiz() -> list[tuple[int, int, int]]:
    """Ask the 8 fixed quiz questions with arrow-key selection and return
    the chosen (chaotic/organized, cautious/bold, solo/collaborative)
    delta for each answer, in order."""
    answers = []
    for q in QUIZ_QUESTIONS:
        labels = [label for label, _ in q["choices"]]
        picked = questionary.select(q["question"], choices=labels).ask()
        deltas = next(deltas for label, deltas in q["choices"] if label == picked)
        answers.append(deltas)
    return answers


def render_result_card(
    builder_type: str,
    meters: list[tuple[str, str, int]],
    verdict: str,
    judge_name: str,
    mascot: str = DEFAULT_MASCOT,
    color: str = DEFAULT_COLOR,
) -> str:
    """Print a colorized ASCII result card to the terminal and return the
    plain (no-ANSI-codes) text so the caller can also save it to a file.

    meters: up to 3 (left_label, right_label, score_0_to_100) tuples, where
    the score is how far toward the *right* label the result sits.

    mascot/color: optional per-persona styling (see PERSONA_STYLES).
    """
    margin = "  "
    width = max(len(builder_type) + 4, 24)
    title_top = margin + "┌" + "─" * width + "┐"
    title_mid = margin + "│" + builder_type.upper().center(width) + "│"
    title_bot = margin + "└" + "─" * width + "┘"
    box_width = width + 2

    mascot_lines = mascot.split("\n")
    art_width = max(len(line) for line in mascot_lines)
    left_pad = margin + " " * max((box_width - art_width) // 2, 0)
    mascot_block = "\n".join(left_pad + line for line in mascot_lines)

    bar_width = 14
    label_width = max((len(left) for left, _, _ in meters[:3]), default=0)
    bar_lines = []
    for left, right, score in meters[:3]:
        score = max(0, min(100, score))
        filled = round(bar_width * score / 100)
        bar = "█" * filled + "░" * (bar_width - filled)
        bar_lines.append(f"  {left:<{label_width}} [{bar}] {right}")

    sep_width = max((len(line) for line in bar_lines), default=2) - 2
    separator = "  " + "─" * sep_width
    bar_block = []
    for i, line in enumerate(bar_lines):
        bar_block.append(line)
        if i < len(bar_lines) - 1:
            bar_block.append(separator)

    verdict = re.sub(r"\s*—\s*", " - ", verdict)
    wrapped = textwrap.wrap(verdict, width=44) or [""]
    wrapped[0] = f'"{wrapped[0]}'
    wrapped[-1] = f'{wrapped[-1]}"'
    verdict_lines = [f"  {line}" for line in wrapped]

    plain_lines = [
        mascot_block,
        "",
        title_top, title_mid, title_bot,
        "",
        *bar_block,
        "",
        *verdict_lines,
        "",
        f"  judged by {judge_name}",
    ]

    highlighted = {title_top, title_mid, title_bot, *bar_lines}
    for line in plain_lines:
        if line == mascot_block or line in highlighted:
            print(f"{color}{BOLD}{line}{RESET}")
        else:
            print(line)

    return "\n".join(plain_lines)


# Optional per-persona styling passed through to render_result_card, keyed
# by judge_name (the name the persona calls itself, e.g. "Nefer-Ka") since
# that's what render_card receives, not the JUDGE_PERSONAS dict key. Any
# persona not listed here just gets the default look (default mascot, red
# bars). Add an entry for your own persona if you want a distinct theme:
# PERSONA_STYLES["your_persona_name"] = {...}.
PERSONA_STYLES: dict[str, dict] = {
    "Captain Hardcode": {
        "mascot": "\n".join([
            "  ⣠⣶⣿⣿⣶⣄ ",
            " ⣾⣿⣿⣿⣿⣿⣿⣷",
            "⣿⣿⣿⣿⣿⣿⣿⣿⣿",
            " ⢻⡟⠛⠉⠉⠛⢻⡟",
            " ⠈⠻⣦⣤⣤⣶⠟⠁",
            " ⠙⠻⣿⣿⣿⠟⠋ ",
            "   ⠉⠛⠛⠉  ",
            "  ⣠⣶⣿⣶⣄  ",
            "   ⠙⠛⠛⠋  ",
        ]),
        "color": "\033[95m",  # bright magenta/purple
    },
    "Nefer-Ka": {
        "mascot": "\n".join([
            ' .-""""-.',
            "|        |",
            "|▒▒▒▒▒▒▒▒|",
            "| X    X |",
            "|▒▒▒▒▒▒▒▒|",
            "|▒▒▒▒▒▒▒▒|",
            "|        |",
            "       ||",
            "       ||",
            "        '",
        ]),
        "color": "\033[93m",  # bright yellow/gold
    },
    "Vex": {
        "mascot": "\n".join([
            "  ///-\\\\\\",
            "  |^   ^|",
            "  |O   O|",
            "  |  ~ *slap*!",
            "   \\ O /",
            "    | |",
        ]),
        "color": "\033[91m",  # bright red
    },
}


def print_boxed(label: str, text: str, width: int = 56) -> None:
    """Print text in a bordered box under a bold label, instead of letting
    it just hang in the terminal. Splits into one bullet per sentence (with
    a blank line between) so a long reply reads as short lines instead of
    one dense paragraph. Used for the agent's own replies (e.g. the final
    wrap-up, or its follow-up if you reject a card)."""
    text = re.sub(r"\s*—\s*", " - ", text.replace("**", ""))
    sentences = [s for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s]
    body: list[str] = []
    for sentence in sentences:
        if body:
            body.append("")
        wrapped = textwrap.wrap(sentence, width=width - 2) or [""]
        body.append(f"- {wrapped[0]}")
        body.extend(f"  {line}" for line in wrapped[1:])
    lines = [
        f"[{label}]",
        "┌" + "─" * (width + 2) + "┐",
        *(f"│ {line}".ljust(width + 2) + "│" for line in body),
        "└" + "─" * (width + 2) + "┘",
    ]
    print("\n" + "\n".join(lines))


PLATFORM = "X"
HANDLE = "@you"


def render_mock_post(caption: str, *, posted: bool) -> str:
    """Print a small X-styled mock post card: a "Draft" preview (shown at
    the HITL approval prompt, before you've decided) or a "Posted" card
    (shown after post_card actually runs). Returns the plain text too."""
    width = 46
    caption = re.sub(r"\s*—\s*", " - ", caption)
    wrapped = textwrap.wrap(caption, width=width - 2) or [""]
    lines = [
        "┌" + "─" * width + "┐",
        "│" + f" {HANDLE} on {PLATFORM}".ljust(width) + "│",
        "│" + "".ljust(width) + "│",
        *(f"│ {line}".ljust(width + 1) + "│" for line in wrapped),
        "│" + "".ljust(width) + "│",
        "│" + "  ♡ 0    ↻ 0    ⤴ share".ljust(width) + "│",
        "└" + "─" * width + "┘",
        "  ● Posted" if posted else "  ○ Draft, awaiting your approval",
    ]
    text = "\n".join(lines)
    print(text)
    return text


@tool
def render_card(
    builder_type: str,
    judge_name: str,
    verdict: str,
    trait_scores: list[int],
    product: str,
) -> str:
    """Render and save the finished result card. Call this only after
    score_and_match has given you trait_scores and a matched product, and
    you've decided on a builder_type headline and a one-line verdict."""
    meters = [(left, right, score) for (left, right), score in zip(TRAIT_AXES, trait_scores)]
    style = PERSONA_STYLES.get(judge_name, {})
    card_text = render_result_card(builder_type, meters, verdict, judge_name, **style)
    safe_type = re.sub(r"[^a-z0-9]+", "_", builder_type.lower()).strip("_")
    safe_judge = re.sub(r"[^a-z0-9]+", "_", judge_name.lower()).strip("_")
    out_path = OUTPUT_DIR / f"{safe_judge}_{safe_type}.txt"
    out_path.write_text(f"{card_text}\n\n  matched product: {product}\n")
    return f"Card printed above and saved to {out_path}. Matched LangChain product: {product}."


@tool
def post_card(caption: str) -> str:
    """Publish the finished result card as a mock post on X. Posts a real
    tweet instead if X API credentials are set in .env (so this lab is
    safe to run without any credentials). Only call this after render_card
    has produced the card."""
    keys = [os.environ.get(k) for k in ("X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_SECRET")]
    if not all(keys):
        render_mock_post(caption, posted=True)
        print(
            "\n  * Reminder: that's a mock post, nothing left this terminal. "
            "Screenshot your real card and share it on X or LinkedIn, tag "
            "@LangChain, if you want it to count for real!"
        )
        return f"Posted with caption: {caption!r}"
    from requests_oauthlib import OAuth1Session

    session = OAuth1Session(*keys)
    response = session.post("https://api.x.com/2/tweets", json={"text": caption})
    response.raise_for_status()
    tweet_id = response.json()["data"]["id"]
    render_mock_post(caption, posted=True)
    return f"Posted: https://x.com/i/web/status/{tweet_id}"


def run_judge(
    judge_name: str,
    *,
    system_prompt: str,
    user_prompt: str,
    tools: list,
    model,
    interrupt_on: dict | None = None,
    thread_prefix: str = "m1-homework",
) -> None:
    """Build the agent for one judge persona, run the quiz, and walk through
    any human-in-the-loop approval prompts until it's done."""
    agent = create_deep_agent(
        model=model,
        tools=tools,
        system_prompt=system_prompt,
        interrupt_on=interrupt_on,
        checkpointer=MemorySaver(),
    )
    config = {"configurable": {"thread_id": f"{thread_prefix}-{judge_name}"}}

    result = agent.invoke(
        {"messages": [{"role": "user", "content": user_prompt}]},
        config=config,
        version="v2",
    )

    while result.interrupts:
        pending = result.interrupts[0].value
        decisions = []
        for req in pending["action_requests"]:
            print(f"\n[{judge_name}] approval required for {req['name']}:")
            if req["name"] == "post_card":
                render_mock_post(req["args"].get("caption", ""), posted=False)
            else:
                for key, value in req["args"].items():
                    if isinstance(value, str):
                        wrapped = textwrap.wrap(value, width=44) or [""]
                        indent = " " * (len(key) + 4)
                        print(f"  {key}: {wrapped[0]}")
                        for line in wrapped[1:]:
                            print(f"{indent}{line}")
                    else:
                        print(f"  {key}: {value}")
            choice = input("Approve, edit, or reject? (approve/edit/reject): ").strip().lower()
            if choice in ("approve", "accept", "yes", "y"):
                decisions.append({"type": "approve"})
            elif choice in ("edit", "e"):
                edited_args = dict(req["args"])
                edited_args["caption"] = input("New caption: ")
                decisions.append({"type": "edit", "edited_action": {"name": req["name"], "args": edited_args}})
            else:
                decisions.append({"type": "reject", "message": "User rejected this card before it posted."})
        result = agent.invoke(Command(resume={"decisions": decisions}), config=config, version="v2")

    print_boxed(judge_name, result.value["messages"][-1].content)
