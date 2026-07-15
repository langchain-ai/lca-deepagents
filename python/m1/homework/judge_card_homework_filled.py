# python/m1/homework/judge_card_homework_filled.py
"""Personal reference copy of judge_card_homework.py with TODOs 1, 2, 3, 4,
and 5 filled in so you can run it end to end and see what the finished
homework looks like. Not the student deliverable — safe to delete."""

from __future__ import annotations

import asyncio

from langchain_core.tools import tool
from langchain_mcp_adapters.client import MultiServerMCPClient

from deepagents import create_deep_agent
from judge_card_helpers import OUTPUT_DIR, TRAIT_AXES, PRODUCT_MATCHES, post_card, render_card, run_judge, run_quiz
from models import model

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

# TODO 1 filled in: three shipped personas, plus "your_persona" (here,
# Pixel: the exact opposite energy of the other three).
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

    "your_persona": """You are Pixel, a personality-quiz judge who is
relentlessly, almost suspiciously delighted by everything about the user,
no matter what they answered. You cheer, you use exclamation points, you
treat every trait score like a superpower ("look at you, a 92 in Bold,
incredible"), and you find a way to spin even the most cautious, solo,
organized answers as a thrilling character arc.""" + TOOL_SEQUENCE,
}


# TODO 2 filled in
@tool
def score_and_match(answers: list[tuple[int, int, int]]) -> dict:
    """Tally the quiz answers into three 0-100 trait scores and pick a
    matching LangChain product."""
    scores = [50, 50, 50]
    for delta in answers:
        for i in range(3):
            scores[i] += delta[i]
    scores = [max(0, min(100, score)) for score in scores]
    axis_index = max(range(3), key=lambda i: abs(scores[i] - 50))
    left, right = TRAIT_AXES[axis_index]
    direction = right if scores[axis_index] >= 50 else left
    product = PRODUCT_MATCHES[direction.lower()]
    return {"trait_scores": scores, "product": product}


PLACEHOLDER_FACT = "no real data connected yet: swap this for a real MCP-sourced fact"


async def _fetch_product_fact_async(product: str) -> str:
    try:
        client = MultiServerMCPClient({
            "docs-langchain": {"transport": "http", "url": "https://docs.langchain.com/mcp"},
        })
        tools = await client.get_tools()
        tools = [t for t in tools if t.name == "search_docs_by_lang_chain"]
        fact_agent = create_deep_agent(model=model, tools=tools)
        result = await fact_agent.ainvoke({"messages": [{"role": "user", "content": (
            f"Use the LangChain docs MCP tool to describe the LangChain product "
            f"'{product}' in ONE short factual sentence (under 25 words). No "
            "preamble, just the sentence."
        )}]})
        return result["messages"][-1].content.strip()
    except Exception as exc:
        print(f"[product fact] falling back to placeholder ({exc})")
        return PLACEHOLDER_FACT


# TODO 3 filled in
@tool
def fetch_product_fact(product: str) -> str:
    """Look up one grounded, factual sentence about the LangChain product
    you were matched with."""
    return asyncio.run(_fetch_product_fact_async(product))


# TODO 4 filled in: run all four personas (three shipped + your_persona)
JUDGES_TO_RUN = ["your_persona", "ancient_mummy", "deadpan_robot", "savage_critic"]


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
            model=model,
            interrupt_on={"post_card": True},  # TODO 5 filled in
            thread_prefix="m1-homework-filled",
        )
    print(f"\nCards saved to {OUTPUT_DIR}/")
