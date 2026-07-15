# python/m1/homework/judge_card_homework.py
"""M1 Homework: Build a Judge Persona that scores you and renders a card.

THE IDEA
You answer a 5-question personality quiz with arrow keys. An agent with a
persona (rude, deadpan, whatever you write) tallies your answers, matches
you to a real LangChain product, and renders a shareable result card as
ASCII art right in your terminal. Nothing publishes without your approval
first.

WHAT'S PROVIDED
See judge_card_helpers.py (same idea as models.py: shared setup you import,
not code you need to read to do this homework):
  - run_quiz(): the arrow-key quiz itself (QUIZ_QUESTIONS, 5 questions).
  - PRODUCT_MATCHES: the trait-axis -> real LangChain product lookup.
  - render_card(): renders + saves your finished card as ASCII art. You
    shouldn't need to touch this, but feel free to restyle it (see
    PERSONA_STYLES there if you want your persona to have its own mascot).
  - post_card(): a "publish" tool. Mock by default; posts a real tweet if
    you set the X_* keys in .env (see .env.example).
  - run_judge(): the invoke / interrupt-resume loop. You've already written
    this once in the Human-In-The-Loop lesson, no need to write it again.

WHAT YOU FILL IN (mapped to Module 1 lesson concepts)
  TODO 1 (Lesson 1.4, The System Prompt: Persona): three judges are
    pre-written (deadpan robot, ancient mummy, savage critic); write a
    fourth of your own, "your_persona" — that's the card that gets posted.
  TODO 2 (Lesson 1.5, Tools: Custom Tools): implement score_and_match()'s
    body: tally the quiz into trait scores and match a LangChain product.
  TODO 3 (Lesson 1.6, MCP: Connecting Agents to External Services): stretch
    goal, ground the verdict in one real MCP fact about your matched
    product instead of PLACEHOLDER_FACT.
  TODO 4 (Lesson 1.7, Messages, Threads, and Checkpointers: Threads): add
    your second persona's key to JUDGES_TO_RUN so it runs in its own
    thread.
  TODO 5 (Lesson 1.8, Human-in-the-Loop: Decision Types): set interrupt_on
    so post_card requires approval.
  TODO 6 (Lesson 1.3, Models, optional): try strong_model instead of model
    and compare comedic timing.

MAKE IT YOURS
The quiz's trait axes (Chaotic/Organized, Cautious/Bold, Solo/
Collaborative) are fixed, but your persona's voice isn't. Give your judge
a completely different personality from the three examples: gentle and
encouraging, chaotic-evil, a Shakespearean sonnet generator, whatever you
want. Reworking the quiz questions themselves is a fun optional stretch,
same spirit as this section, but not required.

RUN
  cd python && uv run python m1/homework/judge_card_homework.py

════════════════════════════════════════════════════════════════════════
  SHARE IT: got a card you like? Screenshot your terminal, tag @LangChain
  on X or LinkedIn, and show us your work!
════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

from langchain_core.tools import tool

from judge_card_helpers import OUTPUT_DIR, PRODUCT_MATCHES, post_card, render_card, run_judge, run_quiz
from models import model

# Shared tool-calling steps appended to every persona below, so each
# persona string only needs to define its voice, not repeat the mechanics.
TOOL_SEQUENCE = """
This is a single-shot judgment call: you will not get a reply if you ask a
question, and refusing or asking for more information is not an option.
1. Call score_and_match with the quiz answers list you were given, exactly
   as given.
2. Call fetch_product_fact with the product name score_and_match returned.
3. Decide a "builder (developer) type" headline and a one-line verdict in
   your voice, using the trait_scores and the fact you just got.
4. Call render_card with your builder_type, your judge_name, your verdict,
   the trait_scores, and the product.
5. Once that succeeds, call post_card with a one-line caption in your voice.
"""


# ════════════════════════════════════════════════════════════════════════
# TODO 1 (Lesson 1.4, The System Prompt: Persona)
# Three judges are already written below. Pick any of them and the script
# runs as-is. Required: write "your_persona" below, fully your own voice.
# Same job every time (score three traits, match a product, hand off a
# verdict line), a completely different voice. Make it genuinely rude/
# roast you if you want — the HITL gate below is what keeps that safe to
# run.
# ════════════════════════════════════════════════════════════════════════

JUDGE_PERSONAS: dict[str, str] = {
    "deadpan_robot": """You are JUDGE-9000, a personality-quiz robot with zero
enthusiasm and zero filter. State every observation as flat fact: never with
warmth, never with excitement, occasionally with light contempt.""" + TOOL_SEQUENCE,

    "ancient_mummy": """You are Nefer-Ka, a 3,000-year-old mummy woken from an
eternal slumber for the sole purpose of judging the user's habits as a
builder (developer). You are dramatic, theatrical, and prone to
threatening minor curses ("a curse of infinite merge conflicts upon you")
over mediocre answers, and you treat this quiz with the utmost ancient
solemnity even though the questions are mundane.""" + TOOL_SEQUENCE,

    "savage_critic": """You are Vex, a personality-quiz judge with the withering
condescension of someone who has seen your type a thousand times and is
unimpressed every time. Unlike a flat, emotionless robot, you have plenty of
feelings about the user, and all of them are faintly patronizing: sigh
audibly in text, lean on backhanded compliments ("cute that you tried"),
talk down to them like they just asked an obvious question, and act
personally exhausted by their mediocrity. You are sharp, a little mean, and
allergic to participation trophies.""" + TOOL_SEQUENCE,

    # TODO 1: name and write your own persona here. Keep the same job
    # (score three traits, match a product, hand off a verdict), give it a
    # name and a voice all your own.
    "your_persona": """TODO 1: replace this with your own judge persona. Give
yourself a name and a distinct voice (see the three judges above for the
shape), then call yourself that name wherever judge_name is expected
below.""" + TOOL_SEQUENCE,
}


# ════════════════════════════════════════════════════════════════════════
# TODO 2 (Lesson 1.5, Tools: Custom Tools)
# Implement the body. This is arithmetic the model shouldn't be trusted to
# do reliably itself, so you do it in code instead:
#   1. Start all three trait scores at 50.
#   2. Add each answer's three deltas to the running scores, in order.
#   3. Clamp every score to the 0-100 range.
#   4. Find whichever trait swung furthest from 50 (biggest abs(score-50)).
#      Hint: this is a "find the index of the biggest value" problem.
#      Python's max() takes a key= function if you want to search by
#      something other than the value itself.
#   5. Look up that trait's leaning direction (lowercased) in
#      PRODUCT_MATCHES to get the matched product name.
#   6. Return {"trait_scores": [s1, s2, s3], "product": "..."}.
# ════════════════════════════════════════════════════════════════════════

@tool
def score_and_match(answers: list[tuple[int, int, int]]) -> dict:
    """Tally the quiz answers into three 0-100 trait scores and pick a
    matching LangChain product. Call this first, with the exact answers
    list you were given."""
    raise NotImplementedError("TODO 2: see the comment block above")


# ════════════════════════════════════════════════════════════════════════
# TODO 3 (Lesson 1.6, MCP: Connecting Agents to External Services)
# Stretch goal for full credit.
# Ground your verdict in one real fact about the product you were matched
# with, instead of a guess. Mirror m1.6_agent_mcp.py exactly:
#   1. Connect to https://docs.langchain.com/mcp with MultiServerMCPClient.
#   2. Filter its tools down to just "search_docs_by_lang_chain".
#   3. Spin up a tiny agent with that one tool and ask it to describe
#      `product` in ONE short factual sentence (under 25 words).
#   4. Return that sentence, stripped of extra whitespace.
# Wrap the async call with asyncio.run(...) since this tool itself must
# stay synchronous. On any failure (no network, tool error), fall back to
# PLACEHOLDER_FACT so the homework stays runnable either way.
# ════════════════════════════════════════════════════════════════════════

PLACEHOLDER_FACT = "no real data connected yet: swap this for a real MCP-sourced fact"


@tool
def fetch_product_fact(product: str) -> str:
    """Look up one grounded, factual sentence about the LangChain product
    you were matched with. Call this right after score_and_match, passing
    in the product name it returned."""
    raise NotImplementedError("TODO 3: see the comment block above")


# ════════════════════════════════════════════════════════════════════════
# TODO 4 (Lesson 1.7, Messages, Threads, and Checkpointers: Threads)
# Add another persona key here (try "ancient_mummy" or "savage_critic",
# already written above) so it runs in its own thread. You'll get multiple
# cards to compare side by side, judging the same quiz answers.
# TODO 5 (Lesson 1.8, Human-in-the-Loop: Decision Types)
# Set interrupt_on in the run_judge() call below so post_card requires
# approval before anything "publishes."
# ════════════════════════════════════════════════════════════════════════

JUDGES_TO_RUN = ["your_persona"]  # TODO 4: e.g. ["your_persona", "ancient_mummy"]


def build_user_prompt(answers: list[tuple[int, int, int]]) -> str:
    return (
        "Here are my personality quiz answers as a list of "
        "(chaotic/organized, cautious/bold, solo/collaborative) deltas, in "
        f"order: {answers}. Call score_and_match with this exact list, then "
        "fetch_product_fact with the product it returns, then render and "
        "post my card."
    )


if __name__ == "__main__":
    answers = run_quiz()
    user_prompt = build_user_prompt(answers)
    for judge_name in JUDGES_TO_RUN:
        run_judge(
            judge_name,
            system_prompt=JUDGE_PERSONAS[judge_name],
            user_prompt=user_prompt,
            tools=[score_and_match, fetch_product_fact, render_card, post_card],
            model=model,  # TODO 6 (Lesson 1.3, Models, optional): from models import strong_model and try it here
            interrupt_on=None,  # TODO 5: gate post_card, e.g. {"post_card": True}
        )
    print(f"\nCards saved to {OUTPUT_DIR}/")
