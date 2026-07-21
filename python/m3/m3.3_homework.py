# python/m3/m3.3_homework.py
"""M3.3 Homework: Prove Memory Isolation Between Users.

THE IDEA
The lab scoped memory to a single fixed workspace_id/user_id and only ever
ran the agent under that one context, so isolation between users was
described in the lesson's "Scoping memory" section but never actually shown
in code. This homework asks you to run the SAME agent under two different
contexts that share a workspace but belong to different users, seed each
with different facts, and confirm a detail you tell the agent to remember
under context A never leaks into what the agent says or stores under
context B.

WHAT YOU FILL IN
  TODO 1: write two DIFFERENT seed memories, one for CONTEXT_A and one for
    CONTEXT_B, in a domain of your choosing (not coding conventions). Both
    should be about the same general topic so a leak would be obvious if
    it happened, but with different specifics.
  TODO 2: write three prompts: a question answerable from A's seed alone, a
    "remember this" message that adds a new, distinctive fact under
    context A, and the SAME question asked again but under context B (it
    should get B's own answer, or no answer, never A's).

RUN
  cd python
  uv run ./m3/m3.3_homework.py
"""

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from deepagents.backends.utils import create_file_data
from langgraph.store.memory import InMemoryStore

from models import model

store = InMemoryStore()
memory_path = "/memories/AGENTS.md"
store_memory_path = "/AGENTS.md"

# Same workspace, two different users -- this is the scoping pattern the
# lesson warns can leak private memories between users if done wrong.
CONTEXT_A = {"workspace_id": "homework", "user_id": "u_you"}
CONTEXT_B = {"workspace_id": "homework", "user_id": "u_teammate"}


def namespace_from_context(context):
    return ("memory", context["workspace_id"], context["user_id"])


def memory_namespace(runtime):
    return namespace_from_context(runtime.context)


# ════════════════════════════════════════════════════════════════════════
# TODO 1: Write two different seed memories.
#
# Pick a domain that's genuinely yours (not coding style guidelines): a
# recipe, a reading list, a plant-watering schedule, a training log. Write
# ONE version for CONTEXT_A (you) and a DIFFERENT version for CONTEXT_B (a
# teammate), same general topic, different specifics.
#
# Example shape (delete this and write your own):
#   def build_seed_memory_a() -> str:
#       return """\
#       # <Your Domain> Notes
#       - <fact 1>
#       """
#   def build_seed_memory_b() -> str:
#       return """\
#       # <Your Domain> Notes (teammate's)
#       - <a different fact>
#       """
# ════════════════════════════════════════════════════════════════════════

def build_seed_memory_a() -> str:
    """TODO 1: return CONTEXT_A's starting memory content."""
    raise NotImplementedError("TODO 1: see the comment block above")


def build_seed_memory_b() -> str:
    """TODO 1: return CONTEXT_B's starting memory content."""
    raise NotImplementedError("TODO 1: see the comment block above")


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


# ════════════════════════════════════════════════════════════════════════
# TODO 2: Write your three prompts.
#
# RECALL_QUESTION: answerable directly from build_seed_memory_a(), asked
#   under CONTEXT_A.
# REMEMBER_MESSAGE: introduces a NEW, distinctive fact under CONTEXT_A that
#   isn't in either seed (make it specific -- a made-up number or name --
#   so a leak into context B is unmistakable).
# LEAK_CHECK_QUESTION: the SAME question as RECALL_QUESTION, asked again
#   but this time under CONTEXT_B. If isolation holds, the answer should
#   reflect B's own seed, not A's.
# ════════════════════════════════════════════════════════════════════════

RECALL_QUESTION = "TODO 2: replace with a question answerable from build_seed_memory_a() alone."
REMEMBER_MESSAGE = "TODO 2: replace with a 'remember this' message introducing a new, distinctive fact under context A."
LEAK_CHECK_QUESTION = "TODO 2: replace with the SAME question as RECALL_QUESTION."

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
