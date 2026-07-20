# python/m1/m1.4_homework.py
"""M1.4 Homework: Write Your Own Persona.

THE IDEA
Lab 1 had you swap between a handful of premade personas (pirate, cowboy,
Shakespeare) layered on top of the butler system prompt already in that
file. This homework asks you to write an entirely new persona from
scratch, for a domain of your own choosing: a sports coach, a noir
detective, a kindergarten teacher, a support bot for a made-up company,
whatever you like. There's no single correct persona here, that's the
point. Two students doing this homework could end up with two completely
different agents.

WHAT YOU FILL IN
  TODO 1: write your own SYSTEM_PROMPT string that gives the agent a
    persona AND a domain of your choosing (not a butler, not pirate,
    cowboy, or Shakespeare from Lab 1's examples).
  TODO 2: invoke the agent with at least two different test prompts and
    print both responses, so you can see the persona hold up across more
    than one question.

RUN
  cd python
  uv run ./m1/m1.4_homework.py
"""

import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

from deepagents import create_deep_agent
from models import model


# ════════════════════════════════════════════════════════════════════════
# TODO 1: Write your own persona system prompt.
#
# Requirements:
#   - Give the agent a persona AND a domain (a role it plays, a voice it
#     speaks in, a subject it's an expert in).
#   - Make it specific enough that the persona clearly shows up in the
#     agent's replies, the way the butler's "indeed" and "quite" did.
#
# Example shape (delete this and write your own):
#   SYSTEM_PROMPT = (
#       "You are a ... . You always ... . You never ... ."
#   )
# ════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = "TODO 1: replace this with your own persona system prompt."


agent = create_deep_agent(
    model=model,
    system_prompt=SYSTEM_PROMPT,
    name="Homework_Agent",
)


# ════════════════════════════════════════════════════════════════════════
# TODO 2: Run at least two different test prompts through the agent and
# print both responses, so the persona's voice shows up more than once.
# ════════════════════════════════════════════════════════════════════════

def run_test_prompts():
    """TODO 2: invoke `agent` with at least two different test prompts
    and print each response."""
    raise NotImplementedError("TODO 2: see the comment block above")


run_test_prompts()
