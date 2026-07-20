# python/m1/m1.7_homework_filled.py
"""Reference copy of m1.7_homework.py with TODOs 1 and 2 filled in so you
can run it end to end and see what "done" looks like. This is just one
possible answer, so yours might be different. Explore!"""

import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

from deepagents import create_deep_agent
from langgraph.checkpoint.memory import MemorySaver

from models import model

agent = create_deep_agent(
    model=model,
    checkpointer=MemorySaver(),
)

# TODO 1 filled in
thread_a = {"configurable": {"thread_id": "m1-7-homework-thread-a"}}
thread_b = {"configurable": {"thread_id": "m1-7-homework-thread-b"}}


# TODO 2 filled in
def run_scenario():
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "Remember that my pet iguana is named Steve and only eats dandelion greens."}]},
        config=thread_a,
    )
    print("Thread A, turn 1:")
    print(result["messages"][-1].content)

    result = agent.invoke(
        {"messages": [{"role": "user", "content": "What's my iguana's name and what does he eat?"}]},
        config=thread_a,
    )
    print("\nThread A, turn 2 (same thread, should remember Steve):")
    print(result["messages"][-1].content)

    result = agent.invoke(
        {"messages": [{"role": "user", "content": "What's my iguana's name and what does he eat?"}]},
        config=thread_b,
    )
    print("\nThread B, turn 1 (different thread, should NOT know):")
    print(result["messages"][-1].content)


run_scenario()
