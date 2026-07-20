# python/m3/m3.3_homework.py
"""M3.3 Homework: Give Your Agent Its Own Memory.

THE IDEA
The lab used CompositeBackend + StoreBackend to give a coding assistant
long-term memory scoped to a workspace and user, seeded with project
guidelines, then had the agent recall and later update that memory. This
homework asks you to do the same thing for a fact or preference YOU choose,
in a domain that has nothing to do with coding conventions (a hobby, a
household routine, a running project, whatever you're into). There's no
single correct fact to remember here, that's the point. Two students doing
this homework could end up remembering two completely different things.

WHAT YOU FILL IN
  TODO 1: write the seed content for /memories/AGENTS.md, a starting fact
    or set of facts in a domain of your choosing.
  TODO 2: write two things: a question that should be answerable from your
    seeded memory alone, and a "remember this" message that introduces a
    NEW fact the agent should persist by editing memory.

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
demo_context = {"workspace_id": "homework", "user_id": "u_you"}


def namespace_from_context(context):
    return ("memory", context["workspace_id"], context["user_id"])


def memory_namespace(runtime):
    return namespace_from_context(runtime.context)


# ════════════════════════════════════════════════════════════════════════
# TODO 1: Write the seed memory content.
#
# Pick a domain that's genuinely yours (not coding style guidelines): a
# recipe you always tweak the same way, a reading list with your own rating
# system, a plant-watering schedule, a training log, anything with a few
# concrete facts or preferences worth remembering across sessions.
#
# Example shape (delete this and write your own):
#   return """\
#   # <Your Domain> Notes
#
#   ## <Section>
#   - <fact 1>
#   - <fact 2>
#   """
# ════════════════════════════════════════════════════════════════════════

def build_seed_memory() -> str:
    """TODO 1: return the starting content for /memories/AGENTS.md."""
    raise NotImplementedError("TODO 1: see the comment block above")


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


# ════════════════════════════════════════════════════════════════════════
# TODO 2: Write your two prompts.
#
# RECALL_QUESTION should be answerable directly from build_seed_memory().
# REMEMBER_MESSAGE should ask the agent to remember one NEW fact that isn't
# in the seed, and to update its memory.
# ════════════════════════════════════════════════════════════════════════

RECALL_QUESTION = "TODO 2: replace with a question answerable from your seeded memory."
REMEMBER_MESSAGE = "TODO 2: replace with a 'remember this' message introducing a new fact."

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
