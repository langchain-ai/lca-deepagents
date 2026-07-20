# python/m3/m3.2_homework_filled.py
"""Reference copy of m3.2_homework.py with TODOs 1 and 2 filled in so you
can run it end to end and see what "done" looks like. This is just one
possible answer, so yours might be different. Explore!"""

import tempfile
from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends.filesystem import FilesystemBackend

from models import model

SKILL_NAME = "plan-a-workout"


# TODO 1 filled in
def build_skill_md() -> str:
    return """---
name: plan-a-workout
description: Use when the user wants a structured workout plan for a specific day or goal.
---

# Plan a Workout

Build a single-session workout plan tailored to the user's goal and available time.

**Step 1: Goal**: Ask what the user is training for today (strength, endurance,
mobility, or general fitness) if it isn't already clear from their message.

**Step 2: Constraints**: Confirm how much time they have and what equipment is
available (bodyweight only, dumbbells, a full gym).

**Step 3: Warm-up**: Always include a 5-minute warm-up appropriate to the goal.

**Step 4: Main block**: Write 4-6 exercises with sets and reps (or time) that fit
the stated goal, time, and equipment.

**Step 5: Cool-down**: End with 2-3 minutes of stretching relevant to the muscles
worked.

## Output

Present the plan as a numbered list: warm-up, main block (with sets/reps), then
cool-down. Keep the whole plan realistic for the time the user gave you.
"""


_tmp_root = Path(tempfile.mkdtemp(prefix="m3_2_homework_"))
_skill_dir = _tmp_root / "skills" / SKILL_NAME
_skill_dir.mkdir(parents=True, exist_ok=True)
(_skill_dir / "SKILL.md").write_text(build_skill_md())

backend = FilesystemBackend(root_dir=str(_tmp_root), virtual_mode=True)


# TODO 2 filled in
SYSTEM_PROMPT = """You are Coach Ren, an upbeat but no-nonsense personal
trainer. Keep your tone encouraging and practical."""
USER_QUESTION = "I have 30 minutes and just a pair of dumbbells. Give me a workout focused on strength."

agent = create_deep_agent(
    model=model,
    name="Homework_Agent",
    backend=backend,
    skills=["/skills"],
    system_prompt=SYSTEM_PROMPT,
)

result = agent.invoke({"messages": [{"role": "user", "content": USER_QUESTION}]})
print(result["messages"][-1].content)
