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

CONTEXT_A = {"workspace_id": "homework", "user_id": "u_you"}
CONTEXT_B = {"workspace_id": "homework", "user_id": "u_teammate"}


def namespace_from_context(context):
    return ("memory", context["workspace_id"], context["user_id"])


def memory_namespace(runtime):
    return namespace_from_context(runtime.context)


# TODO 1 filled in
def build_seed_memory_a() -> str:
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


def build_seed_memory_b() -> str:
    return """\
# Herb Garden Notes

## Watering
- Basil and mint want consistently moist soil; check daily in summer.
- Rosemary is drought-tolerant; only water when the top two inches are dry.

## Light
- All three herbs live on the kitchen windowsill, which gets morning sun.
"""


store.put(namespace_from_context(CONTEXT_A), store_memory_path, create_file_data(build_seed_memory_a()))
store.put(namespace_from_context(CONTEXT_B), store_memory_path, create_file_data(build_seed_memory_b()))

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
LEAK_CHECK_QUESTION = "How often should I water the fiddle-leaf fig, and where does the pothos live?"

# 1. Context A recalls from its own seed.
result_a1 = agent.invoke({"messages": [{"role": "user", "content": RECALL_QUESTION}]}, context=CONTEXT_A)
print("--- Context A, Question 1 ---")
print(result_a1["messages"][-1].content)

# 2. Context A learns a new, distinctive fact.
result_a2 = agent.invoke({"messages": [{"role": "user", "content": REMEMBER_MESSAGE}]}, context=CONTEXT_A)
print("\n--- Context A, Question 2 (remember) ---")
print(result_a2["messages"][-1].content)

# 3. Context B asks the same question. It should NOT see anything from A.
result_b = agent.invoke({"messages": [{"role": "user", "content": LEAK_CHECK_QUESTION}]}, context=CONTEXT_B)
print("\n--- Context B, leak-check question ---")
print(result_b["messages"][-1].content)

memory_a = store.get(namespace_from_context(CONTEXT_A), store_memory_path).value["content"]
memory_b = store.get(namespace_from_context(CONTEXT_B), store_memory_path).value["content"]
print("\n--- Context A's stored AGENTS.md ---")
print(memory_a)
print("\n--- Context B's stored AGENTS.md ---")
print(memory_b)

if memory_a == memory_b:
    print("\nISOLATION FAILED: both contexts share identical stored memory.")
else:
    print("\nStored memories differ between contexts, as expected.")
