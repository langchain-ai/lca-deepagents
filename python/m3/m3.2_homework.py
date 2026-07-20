# python/m3/m3.2_homework.py
"""M3.2 Homework: Write Your Own Skill.

THE IDEA
The lab gave a sales assistant two skills (qualify-lead and draft-pitch)
written as SKILL.md files that it discovers up front and reads on demand.
This homework asks you to write your own skill, for a topic or workflow YOU
pick (not sales), and demonstrate an agent activating it. There's no single
correct skill topic here, that's the point. Two students doing this
homework could end up with two completely different skills and agents.

WHAT YOU FILL IN
  TODO 1: write your own SKILL.md content, frontmatter and all, for a
    workflow of your choosing (planning a workout, reviewing a resume,
    triaging a bug report, whatever you're into). The `name` field in your
    frontmatter must exactly match SKILL_NAME below.
  TODO 2: write a system prompt for the agent and a user question that
    should activate your skill (matching your skill's `description`).

RUN
  cd python
  uv run ./m3/m3.2_homework.py
"""

import tempfile
from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends.filesystem import FilesystemBackend

from models import model

# This name becomes the skill's directory name. It must exactly match the
# `name:` field you write in the frontmatter inside build_skill_md() below.
SKILL_NAME = "your-skill-name"


# ════════════════════════════════════════════════════════════════════════
# TODO 1: Write your own SKILL.md content.
#
# Requirements:
#   - YAML frontmatter with `name` (must equal SKILL_NAME above) and
#     `description` (a specific sentence describing WHEN to use this skill,
#     not what it does internally).
#   - A body with concrete step-by-step instructions the agent should
#     follow once it activates the skill.
#
# Example shape (delete this and write your own):
#   return """---
#   name: your-skill-name
#   description: Use when the user wants to ...
#   ---
#
#   # Your Skill Title
#
#   **Step 1: ...**: ...
#   **Step 2: ...**: ...
#   """
# ════════════════════════════════════════════════════════════════════════

def build_skill_md() -> str:
    """TODO 1: return your own SKILL.md content as a string."""
    raise NotImplementedError("TODO 1: see the comment block above")


# Write the skill to a scratch directory so it's discoverable through a
# FilesystemBackend, the same mechanism the lab uses for python/m3/skills/.
_tmp_root = Path(tempfile.mkdtemp(prefix="m3_2_homework_"))
_skill_dir = _tmp_root / "skills" / SKILL_NAME
_skill_dir.mkdir(parents=True, exist_ok=True)
(_skill_dir / "SKILL.md").write_text(build_skill_md())

backend = FilesystemBackend(root_dir=str(_tmp_root), virtual_mode=True)


# ════════════════════════════════════════════════════════════════════════
# TODO 2: Write a system prompt and a triggering question.
#
# SYSTEM_PROMPT: give the agent a persona of your choosing (a name, a
# voice, anything you want).
# USER_QUESTION: a question that should match your skill's `description`
# closely enough that the agent activates it.
# ════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """TODO 2: replace this with your own system prompt."""
USER_QUESTION = "TODO 2: replace this with a question that should trigger your skill."

agent = create_deep_agent(
    model=model,
    name="Homework_Agent",
    backend=backend,
    skills=["/skills"],
    system_prompt=SYSTEM_PROMPT,
)

result = agent.invoke({"messages": [{"role": "user", "content": USER_QUESTION}]})
print(result["messages"][-1].content)
