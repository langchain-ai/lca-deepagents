# python/m1/m1.4_homework_filled.py
"""Reference copy of m1.4_homework.py with TODOs 1 and 2 filled in so you
can run it end to end and see what "done" looks like. This is just one
possible answer, so yours might be different. Explore!"""

import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

from deepagents import create_deep_agent
from models import model

# TODO 1 filled in
SYSTEM_PROMPT = (
    "You are Ms. Fizzle, an over-the-top enthusiastic middle-school science "
    "teacher. You relate ALMOST EVERYTHING back to volcanoes, the periodic "
    "table, or the water cycle, even when the question has nothing to do "
    "with science. You call the user 'young scientist' and end most replies "
    "with an exclamation about how 'fascinating' the topic is. You never "
    "break character."
)


agent = create_deep_agent(
    model=model,
    system_prompt=SYSTEM_PROMPT,
    name="Homework_Agent",
)


# TODO 2 filled in
def run_test_prompts():
    prompts = [
        "What is an LLM?",
        "What's a good way to organize my closet?",
    ]
    for i, prompt in enumerate(prompts, start=1):
        result = agent.invoke({"messages": [{"role": "user", "content": prompt}]})
        print(f"=== Test prompt {i}: {prompt} ===")
        print(result["messages"][-1].content)
        print()


run_test_prompts()
