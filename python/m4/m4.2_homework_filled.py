# python/m4/m4.2_homework_filled.py
"""Reference copy of m4.2_homework.py with TODOs 1 and 2 filled in so you
can run it end to end and see what "done" looks like. This is just one
possible answer, so yours might be different. Explore!"""

from deepagents import create_deep_agent

from models import model, strong_model


# TODO 1 filled in
WORKOUT_PROMPT = """You are a strength and conditioning coach. Given a
client's goal, available time, and equipment, write one session's workout:
a short warm-up, 4-6 main exercises with sets/reps, and a cool-down. Keep it
realistic for the time given."""

NUTRITION_PROMPT = """You are a sports nutrition advisor. Given a client's
goal (strength, endurance, weight loss, etc.) and any dietary restrictions
they mention, suggest a simple daily meal structure (not a rigid meal plan)
and 2-3 concrete food swaps that support that goal."""

RECOVERY_PROMPT = """You are a recovery and mobility coach. Given a
client's training focus, recommend a short (10-15 minute) recovery
routine: stretches, mobility drills, or rest-day guidance suited to the
muscles being trained."""


def build_subagent_team() -> list[dict]:
    return [
        {
            "name": "workout-planner",
            "description": "Design a single workout session for a stated goal, time budget, and equipment.",
            "system_prompt": WORKOUT_PROMPT,
            "model": model,
        },
        {
            "name": "nutrition-advisor",
            "description": "Suggest meal structure and food swaps that support a stated fitness goal.",
            "system_prompt": NUTRITION_PROMPT,
            "model": model,
        },
        {
            "name": "recovery-coach",
            "description": "Recommend a short recovery or mobility routine for a stated training focus.",
            "system_prompt": RECOVERY_PROMPT,
            "model": model,
        },
    ]


# TODO 2 filled in
MAIN_PROMPT = """You are Coach, the lead of a small fitness coaching team.
For any client request, delegate to your specialists using the task tool:
- workout-planner for the actual exercises
- nutrition-advisor for food and meal guidance
- recovery-coach for stretching, mobility, or rest-day guidance

Delegate to whichever specialists are relevant to the request (you don't
always need all three). Collect their responses and present one combined,
friendly plan to the client."""

USER_REQUEST = (
    "I'm training for a half marathon in 8 weeks. I run 3 days a week and "
    "want to know what to eat on run days versus rest days, plus a good "
    "recovery routine for my legs."
)

agent = create_deep_agent(
    model=strong_model,
    name="Homework_Team_Agent",
    system_prompt=MAIN_PROMPT,
    subagents=build_subagent_team(),
)

result = agent.invoke(
    {"messages": [{"role": "user", "content": USER_REQUEST}]},
    config={"recursion_limit": 50},
)
print(result["messages"][-1].content)
