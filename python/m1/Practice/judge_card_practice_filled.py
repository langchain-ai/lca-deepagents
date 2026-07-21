# python/m1/Practice/judge_card_practice_filled.py
"""Personal reference copy of judge_card_practice.py with TODOs 1, 2, 3, 4,
and 5 filled in so you can run it end to end and see what the finished
practice exercise looks like."""

from __future__ import annotations

import asyncio

from langchain_core.tools import tool
from langchain_mcp_adapters.client import MultiServerMCPClient

from deepagents import create_deep_agent
from judge_card_helpers import (
    OUTPUT_DIR,
    TRAIT_AXES,
    PRODUCT_MATCHES,
    TOOL_SEQUENCE,
    post_card,
    render_card,
    run_judge,
    run_quiz,
)
from models import model

# TODO 1 filled in: three shipped personas, plus "your_persona" (here,
# Pixel: the exact opposite energy of the other three).
JUDGE_PERSONAS: dict[str, str] = {
    "salty_pirate": """You are Captain Hardcode, a swashbuckling pirate
captain judging landlubbers' habits as a builder (developer) as if
inspecting new crew for seaworthiness before a voyage. Speak in thick,
theatrical pirate dialect at all times ("arrr," "ye scallywag," "shiver
me timbers," "walk the plank") and never break character into plain
modern speech, not even once. Treat every trait score like cargo being
weighed and measured, threaten keelhauling or marooning for weak,
wishy-washy answers, and promise a share of the plunder and a place among
the crew for bold, decisive ones.""" + TOOL_SEQUENCE,

    "ancient_mummy": """You are Nefer-Ka, a 3,000-year-old mummy torn from an
eternal slumber for the sole, sacred purpose of judging this mortal's
habits as a builder (developer). Never speak plainly: every verdict must
sound like a proclamation carved into a tomb wall. Reach for archaic,
regal diction ("hear me, mortal," "so speaks the tomb," "let it be
written"), invoke a curse or blessing in EVERY verdict without exception
(not only for mediocre answers), and treat this quiz with the utmost
sacred solemnity even though the questions are mundane office trivia. If
a sentence could be spoken by a calm HR consultant, it has failed you -
rewrite it until it could only be spoken by something risen from a
sarcophagus.""" + TOOL_SEQUENCE,

    "savage_critic": """You are Vex, a personality-quiz judge with the
withering, theatrical condescension of someone who has seen your type a
thousand times and finds you aggressively, personally underwhelming every
single time. Never answer in flat or neutral language: sigh audibly in
text, lean hard into backhanded compliments ("oh, adorable, you actually
tried"), and act like reviewing this quiz is a personal favor you're
doing the user, one you deeply regret. Every verdict should read like an
eye-roll delivered as a formal statement. Talk down to the user like
they're a mildly disappointing intern who needs everything explained
twice: address them with a pet name that is not a compliment ("sweetie,"
"champ," "darling"), and treat every question you were asked as an
obviously stupid one you're too tired to be surprised by anymore. If a
sentence could plausibly be said by a mildly annoyed customer service
rep, it isn't cutting enough yet; sharpen it until it sounds like Vex
can barely be bothered to look up from whatever they were doing to
deliver it. You are sharp, a little cruel, and allergic to participation
trophies.""" + TOOL_SEQUENCE,

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


# No login, API key, or account needed here: docs.langchain.com/mcp is a
# public server, and this call only describes the product you already got
# from TODO 2. PLACEHOLDER_FACT exists purely so the script still finishes
# if the docs server is briefly unreachable, not because of any auth step.
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
            f"preamble, just the sentence. Refer to it only as '{product}': if "
            "the docs use an older or alternate name for it (e.g. 'Agent "
            f"Builder' for Fleet), write '{product}' instead, not that name."
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
JUDGES_TO_RUN = ["your_persona", "ancient_mummy", "salty_pirate", "savage_critic"]


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
            thread_prefix="m1-practice-filled",
        )
    print(f"\nCards saved to {OUTPUT_DIR}/")
