# python/m3/m3.2_homework_filled.py
"""Reference copy of m3.2_homework.py with TODOs 1-3 filled in so you can
run it end to end and see what "done" looks like. This is just one
possible answer, so yours might be different. Explore!"""

import tempfile
from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends.filesystem import FilesystemBackend

from models import model

SKILL_NAME = "plan-a-workout"
REFERENCE_PATH = f"/skills/{SKILL_NAME}/reference.md"


# TODO 1 filled in
def build_skill_md() -> str:
    return """---
name: plan-a-workout
description: Use when the user wants a structured workout plan for a specific day or goal.
---

# Plan a Workout

Build a single-session workout plan tailored to the user's goal and available time.

**Step 1: Goal**: Ask what the user is training for today (strength, hypertrophy,
endurance, or mobility) if it isn't already clear from their message.

**Step 2: Constraints**: Confirm how much time they have and what equipment is
available (bodyweight only, dumbbells, a full gym).

**Step 3: Look up the numbers**: Before writing sets and reps, read `reference.md`
in this skill's directory for the exact sets/reps/rest table for the stated
goal. Do not guess these numbers; they vary by goal and this skill's rubric is
specific about them.

**Step 4: Warm-up**: Always include a 5-minute warm-up appropriate to the goal.

**Step 5: Main block**: Write 4-6 exercises using the sets/reps/rest from
reference.md that fit the stated goal, time, and equipment.

**Step 6: Cool-down**: End with 2-3 minutes of stretching relevant to the muscles
worked.

## Output

Present the plan as a numbered list: warm-up, main block (with sets/reps/rest
per reference.md), then cool-down. Keep the whole plan realistic for the time
the user gave you.
"""


# TODO 2 filled in
def build_reference_md() -> str:
    return """# Sets / Reps / Rest Rubric

Use the row matching the user's stated goal. Do not deviate from these
numbers; they're calibrated for a single 20-30 minute session.

| Goal        | Sets | Reps      | Rest between sets |
|-------------|------|-----------|--------------------|
| Strength    | 4-5  | 4-6       | 90-120 seconds     |
| Hypertrophy | 3-4  | 8-12      | 60-90 seconds      |
| Endurance   | 2-3  | 15-20     | 30-45 seconds      |
| Mobility    | 2-3  | 30-60s hold (not reps) | 15-30 seconds |
"""


_tmp_root = Path(tempfile.mkdtemp(prefix="m3_2_homework_"))
_skill_dir = _tmp_root / "skills" / SKILL_NAME
_skill_dir.mkdir(parents=True, exist_ok=True)
(_skill_dir / "SKILL.md").write_text(build_skill_md())
(_skill_dir / "reference.md").write_text(build_reference_md())

backend = FilesystemBackend(root_dir=str(_tmp_root), virtual_mode=True)
print(f"Skill files written to: {_skill_dir}")


# TODO 3 filled in
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

read_calls = [
    call
    for msg in result["messages"]
    for call in getattr(msg, "tool_calls", [])
    if call["name"] == "read_file"
]
reference_was_read = any(call["args"].get("file_path") == REFERENCE_PATH for call in read_calls)
print(f"\n--- Did the agent read {REFERENCE_PATH}? {reference_was_read} ---")
if not reference_was_read:
    print(
        "It didn't. Either SKILL.md isn't clearly telling it to, or the "
        "task is answerable without the details in reference.md."
    )
