from deepagents import create_deep_agent
from langgraph.checkpoint.memory import MemorySaver

from models import model

agent = create_deep_agent(
    model=model,
    checkpointer=MemorySaver(),
)

thread_a = {"configurable": {"thread_id": "m1-7-thread-a"}}
thread_b = {"configurable": {"thread_id": "m1-7-thread-b"}}

result = agent.invoke(
    {"messages": [{"role": "user", "content": "Remember that my favorite color is blue."}]},
    config=thread_a,
)
print("Thread A, turn 1:")
print(result["messages"][-1].content)

result = agent.invoke(
    {"messages": [{"role": "user", "content": "What is my favorite color?"}]},
    config=thread_a,
)
print("\nThread A, turn 2:")
print(result["messages"][-1].content)

result = agent.invoke(
    {"messages": [{"role": "user", "content": "What is my favorite color?"}]},
    config=thread_b,
)
print("\nThread B, turn 1:")
print(result["messages"][-1].content)
