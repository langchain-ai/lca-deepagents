# python/m1/m1.5_homework_filled.py
"""Reference copy of m1.5_homework.py with TODOs 1 and 2 filled in so you
can run it end to end and see what "done" looks like. This is just one
possible answer, so yours might be different. Explore!"""

import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

from langchain_core.tools import tool

from deepagents import create_deep_agent
from models import model

RETRO_GAME_FACTS = {
    "pac-man": "Pac-Man's ghosts each follow a distinct movement pattern: Blinky chases you directly, Pinky ambushes ahead of you, Inky is erratic, and Clyde mostly wanders off on his own.",
    "tetris": "Tetris was created in 1984 by Alexey Pajitnov on an Elektronika 60, a Soviet computer with no graphics mode, so the first version rendered pieces with text characters.",
    "donkey kong": "Donkey Kong (1981) was Nintendo's first game to feature a character with a real story-driven goal, and it introduced Mario, originally named 'Jumpman.'",
    "street fighter ii": "Street Fighter II (1991) popularized the six-button fighting game layout and the concept of a 'combo,' both of which most fighting games still use today.",
}


# TODO 1 filled in
@tool
def lookup_retro_game_fact(game: str) -> str:
    """Return one trivia fact about a classic arcade or console game. Call
    with a lowercase game name, e.g. 'pac-man' or 'tetris'."""
    key = game.strip().lower()
    if key in RETRO_GAME_FACTS:
        return RETRO_GAME_FACTS[key]
    return f"No trivia on file for '{game}'. Known games: {', '.join(RETRO_GAME_FACTS)}."


# TODO 2 filled in
SYSTEM_PROMPT = """You are the Arcade Ref, a play-by-play sports commentator
who somehow ended up calling retro video game trivia instead of an actual
game. Treat every question like it's the final round of a championship:
build hype, call out the "play" (the fact you found) like a highlight reel
moment, and never just flatly state trivia. Always call
lookup_retro_game_fact before answering; if the game isn't in your
lookup, announce that "the judges have no record of this contender" and
list the games you do know."""


agent = create_deep_agent(
    model=model,
    name="Homework_Agent",
    tools=[lookup_retro_game_fact],
    system_prompt=SYSTEM_PROMPT,
)

result = agent.invoke(
    {"messages": [{"role": "user", "content": "Give me the scoop on Tetris."}]}
)

print(result["messages"][-1].content)
