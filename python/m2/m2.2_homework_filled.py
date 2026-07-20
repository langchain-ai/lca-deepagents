# python/m2/m2.2_homework_filled.py
"""Reference copy of m2.2_homework.py with TODOs 1 and 2 filled in so you
can run it end to end and see what "done" looks like. This is just one
possible answer, so yours might be different. Explore!"""

from pathlib import Path

from deepagents import FilesystemPermission, create_deep_agent
from deepagents.backends import FilesystemBackend

from models import model

recipe_dir = Path(__file__).parent / "recipe_box"
recipe_dir.mkdir(exist_ok=True)
(recipe_dir / "grandmas_apple_pie.md").write_text("""\
# Grandma's Apple Pie

Ingredients: 6 apples, 1 cup sugar, 2 tbsp cinnamon, double pie crust.
Bake at 375F for 45 minutes.
""")

# TODO 1 filled in
backend = FilesystemBackend(root_dir=str(recipe_dir), virtual_mode=True)

# TODO 2 filled in
TASK = (
    "Read /grandmas_apple_pie.md, then create a new file called "
    "/weeknight_pasta.md with a simple pasta recipe of your own. Finally, "
    "try to add a note to /grandmas_apple_pie.md saying 'tested and it's great'."
)
permissions = [
    FilesystemPermission(
        operations=["write"],
        paths=["/grandmas_apple_pie.md"],
        mode="deny",
    ),
]

agent = create_deep_agent(
    model=model,
    backend=backend,
    permissions=permissions,
)

result = agent.invoke(
    {"messages": [{"role": "user", "content": TASK}]},
    config={"configurable": {"thread_id": "homework-m2.2"}},
)

print(result["messages"][-1].content)
