"""M1.5 Homework: Build Your Own Custom Tool.

THE IDEA
The lab wired up one custom tool (read_sql) for one fixed topic (the
Chinook music database). This homework asks you to do the same thing for
a topic YOU pick: something you actually know or care about (a game, a
sport, a show, your favorite band's discography, local trivia, whatever).
There's no single correct topic or persona here, that's the point. Two
students doing this homework could end up with two completely different
tools and agents.

WHAT YOU FILL IN
TODO 1: write your own custom tool with the @tool decorator. Pick any
topic, store a small lookup (a dict is fine, no API needed) of facts
about it, and return one back based on the argument the model passes.
TODO 2: write a system prompt that gives the agent a persona of your
choosing and tells it to use your tool before answering.

RUN
cd python
uv run ./m1/m1.5_homework.py
"""

import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

from langchain_core.tools import tool

from deepagents import create_deep_agent
from models import model
# ════════════════════════════════════════════════════════════════════════

# TODO 1: Define your own custom tool.

@tool
def lookup_virat_kohli_fact(query: str) -> str:
    """Returns a relevant fact about Virat Kohli based on the user's query."""

    facts = {
        "role": "Virat Kohli is a right-handed top-order batter and former captain of the Indian cricket team.",
        "country": "Virat Kohli represents India in international cricket.",
        "ipl": "Virat Kohli has played for Royal Challengers Bengaluru throughout his IPL career.",
        "batting": "Virat Kohli is known for his aggressive batting, consistency, and ability to chase targets.",
        "nickname": "Virat Kohli is popularly known as King Kohli.",
    }

    query = query.lower()

    for key, fact in facts.items():
        if key in query:
            return fact

    return (
        "I could not find a specific fact for that query. "
        "Try asking about Virat Kohli's role, country, IPL career, "
        "batting style, or nickname."
    )

# ════════════════════════════════════════════════════════════════════════

# TODO 2: Write a system prompt for your agent.

SYSTEM_PROMPT = """
You are Virat, a knowledgeable cricket assistant who specializes in
Virat Kohli and his cricket career.

Before answering any question about Virat Kohli, you must use the
lookup_virat_kohli_fact tool to retrieve the relevant information.

Use the information returned by the tool as the basis for your answer.
If the question is unrelated to Virat Kohli, politely explain that you
specialize in Virat Kohli and redirect the user to a question about him.
"""

if "TODO 1" in lookup_virat_kohli_fact.description:
    raise NotImplementedError("TODO 1: see the comment block above")
if "TODO 2" in SYSTEM_PROMPT:
    raise NotImplementedError("TODO 2: see the comment block above")

agent = create_deep_agent(
    model=model,
    name="Homework_Agent",
    tools=[lookup_virat_kohli_fact],
    system_prompt=SYSTEM_PROMPT,
)

result = agent.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "What is Virat Kohli's role in cricket?"
            }
        ]
    }
)

print(result["messages"][-1].content)