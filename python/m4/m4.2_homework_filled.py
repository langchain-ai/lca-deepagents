# python/m4/m4.2_homework_filled.py
"""Reference copy of m4.2_homework.py with TODOs 1 and 2 filled in so you
can run it end to end and see what "done" looks like. This is just one
possible answer, so yours might be different. Explore!"""

from deepagents import FilesystemPermission, create_deep_agent

from models import model, strong_model

SCRATCH_ROOT = "/scratch"


def scratch_path(subagent_name: str) -> str:
    return f"{SCRATCH_ROOT}/{subagent_name}/notes.md"


def scratch_permissions(subagent_name: str) -> list:
    return [
        FilesystemPermission(operations=["read", "write"], paths=[f"{SCRATCH_ROOT}/{subagent_name}/**"], mode="allow"),
        FilesystemPermission(operations=["write"], paths=["/**"], mode="deny"),
    ]


def scratch_instruction(subagent_name: str) -> str:
    return (
        f'Before you answer, call write_file on "{scratch_path(subagent_name)}" '
        "with your raw notes or reasoning. Then give your final answer using "
        "only the polished result -- do not repeat those raw notes in your reply."
    )


def build_subagents(specs: list[dict]) -> list[dict]:
    team = []
    for spec in specs:
        name = spec["name"]
        team.append(
            {
                "name": name,
                "description": spec["description"],
                "system_prompt": spec["role_prompt"] + "\n\n" + scratch_instruction(name),
                "permissions": scratch_permissions(name),
            }
        )
    return team


# TODO 1 filled in
SUBAGENT_SPECS = [
    {
        "name": "workout-planner",
        "description": "Design a single workout session for a stated goal, time budget, and equipment.",
        "role_prompt": (
            "You are a strength and conditioning coach. Given a client's goal, "
            "available time, and equipment, write one session's workout: a "
            "short warm-up, 4-6 main exercises with sets/reps, and a cool-down. "
            "Keep it realistic for the time given."
        ),
    },
    {
        "name": "nutrition-advisor",
        "description": "Suggest meal structure and food swaps that support a stated fitness goal.",
        "role_prompt": (
            "You are a sports nutrition advisor. Given a client's goal "
            "(strength, endurance, weight loss, etc.) and any dietary "
            "restrictions they mention, suggest a simple daily meal structure "
            "(not a rigid meal plan) and 2-3 concrete food swaps that support "
            "that goal."
        ),
    },
]


# TODO 2 filled in
MAIN_PROMPT = """You are Coach, the lead of a small fitness coaching team.
For any client request, delegate to your specialists using the task tool:
- workout-planner for the actual exercises
- nutrition-advisor for food and meal guidance

Delegate to both if the request touches both areas. Collect their responses
and present one combined, friendly plan to the client."""

USER_REQUEST = (
    "I'm training for a half marathon in 8 weeks. I run 3 days a week and want "
    "a strength workout for one of my non-running days, plus advice on what to "
    "eat on run days versus rest days."
)

for _spec in SUBAGENT_SPECS:
    if _spec["name"].startswith("TODO-1"):
        raise NotImplementedError("TODO 1: see the comment block above")
if MAIN_PROMPT.startswith("TODO 2") or USER_REQUEST.startswith("TODO 2"):
    raise NotImplementedError("TODO 2: see the comment block above")

_team = build_subagents(SUBAGENT_SPECS)

MAIN_PERMISSIONS = [
    FilesystemPermission(operations=["write"], paths=[f"{SCRATCH_ROOT}/**"], mode="deny"),
]

agent = create_deep_agent(
    model=strong_model,
    name="Homework_Team_Agent",
    system_prompt=MAIN_PROMPT,
    subagents=_team,
    permissions=MAIN_PERMISSIONS,
)

result = agent.invoke(
    {"messages": [{"role": "user", "content": USER_REQUEST}]},
    config={"recursion_limit": 50},
)
print(result["messages"][-1].content)

files = result.get("files", {})
print("\n--- Scratch folder isolation check ---")
for spec in SUBAGENT_SPECS:
    path = scratch_path(spec["name"])
    print(f"  {path}: {'found' if path in files else 'not written (subagent may not have been called)'}")

scratch_files = [p for p in files if p.startswith(SCRATCH_ROOT + "/")]
expected = {scratch_path(spec["name"]) for spec in SUBAGENT_SPECS}
stray = [p for p in scratch_files if p not in expected]
if stray:
    print(f"  Unexpected scratch files (isolation may have failed): {stray}")
else:
    print("  No stray scratch files -- each subagent wrote only to its own folder.")
