import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from models import model
from deepagents import create_deep_agent
from deepagents.backends.filesystem import FilesystemBackend

m3_dir = Path(__file__).parent

# Create memories directory and initial AGENTS.md if they don't exist
memories_dir = m3_dir / "memories"
agents_md = memories_dir / "AGENTS.md"
memories_dir.mkdir(exist_ok=True)
if not agents_md.exists():
    agents_md.write_text("""\
# Project Guidelines

## Code Style
- All functions must have type annotations
- Use f-strings for string formatting
- Maximum line length is 88 characters
- Use `pathlib.Path` for file operations, not `os.path`

## Workflow
- Run tests with: `uv run pytest`
- The CI pipeline runs on every push to `main`
- Open a draft PR early so reviewers can follow along
""")

backend = FilesystemBackend(root_dir=str(m3_dir), virtual_mode=True)

agent = create_deep_agent(
    model=model,
    backend=backend,
    memory=["memories/AGENTS.md"],
    system_prompt="You are a helpful coding assistant for this project.",
)

# First invoke: agent answers using memory content
result = agent.invoke({
    "messages": [{"role": "user", "content": "What tool should I use for file paths in this project?"}]
})
print("--- Question 1 ---")
print(result["messages"][-1].content)

# Second invoke: agent writes to memory
result2 = agent.invoke({
    "messages": [{"role": "user", "content": "Remember: the team switched to ruff for linting. Update your memory."}]
})
print("\n--- Question 2 ---")
print(result2["messages"][-1].content)

print("\n--- AGENTS.md after write ---")
print(agents_md.read_text())
