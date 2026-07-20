# python/m3/m3.3_homework_filled.py
"""Reference copy of m3.3_homework.py with TODOs 1 and 2 filled in so you
can run it end to end and see what "done" looks like. This is just one
possible answer, so yours might be different. Explore!"""

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from deepagents.backends.utils import create_file_data
from langgraph.store.memory import InMemoryStore

from models import model

store = InMemoryStore()
memory_path = "/memories/AGENTS.md"
store_memory_path = "/AGENTS.md"
demo_context = {"workspace_id": "homework", "user_id": "u_you"}


def namespace_from_context(context):
    return ("memory", context["workspace_id"], context["user_id"])


def memory_namespace(runtime):
    return namespace_from_context(runtime.context)


# TODO 1 filled in
def build_seed_memory() -> str:
    return """\
# Houseplant Notes

## Watering
- The fiddle-leaf fig gets watered every 10 days, not on a fixed weekday;
  check the top inch of soil first.
- The succulents on the windowsill only get watered when the soil is
  completely dry, roughly every 2-3 weeks.

## Light
- The pothos and snake plant tolerate low light and live in the hallway.
- Everything else needs the south-facing window.
"""


store.put(
    namespace_from_context(demo_context),
    store_memory_path,
    create_file_data(build_seed_memory()),
)

agent = create_deep_agent(
    model=model,
    name="Homework_Memory_Agent",
    backend=CompositeBackend(
        default=StateBackend(),
        routes={"/memories/": StoreBackend(namespace=memory_namespace)},
    ),
    store=store,
    memory=[memory_path],
    system_prompt="You are a helpful personal assistant for this project.",
)


# TODO 2 filled in
RECALL_QUESTION = "How often should I water the fiddle-leaf fig, and where does the pothos live?"
REMEMBER_MESSAGE = (
    "Remember: I just repotted the fiddle-leaf fig, so skip watering it for "
    "the next 3 weeks while the roots settle. Update your memory."
)

# First invoke: agent answers using memory content
result = agent.invoke(
    {"messages": [{"role": "user", "content": RECALL_QUESTION}]},
    context=demo_context,
)
print("--- Question 1 ---")
print(result["messages"][-1].content)

# Second invoke: agent writes to memory
result2 = agent.invoke(
    {"messages": [{"role": "user", "content": REMEMBER_MESSAGE}]},
    context=demo_context,
)
print("\n--- Question 2 ---")
print(result2["messages"][-1].content)

print("\n--- AGENTS.md after write ---")
stored_memory = store.get(namespace_from_context(demo_context), store_memory_path)
print(stored_memory.value["content"])
