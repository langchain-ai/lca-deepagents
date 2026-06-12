import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from models import model
from deepagents import create_deep_agent
from deepagents.backends.langsmith import LangSmithSandbox
from langsmith.sandbox import SandboxClient

DB_PATH = Path(__file__).resolve().parent.parent / "m1" / "chinook.db"

client = SandboxClient()
ls_sandbox = client.create_sandbox(name="lca-deepagents-lab")
print(f"Sandbox: {ls_sandbox.name}  (id: {ls_sandbox.id})")

backend = LangSmithSandbox(sandbox=ls_sandbox)

with open(DB_PATH, "rb") as f:
    backend.upload_files([("/chinook.db", f.read())])

agent = create_deep_agent(
    model=model,
    backend=backend,
    system_prompt=(
        "You are a sales data analyst with access to the Chinook music store database "
        "at /chinook.db. Use sqlite3 and matplotlib to answer questions with charts. "
        "Install any packages you need with pip before importing them. "
        "When asked to produce a chart, write a Python script, execute it, and confirm "
        "the output file was created."
    ),
)

try:
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Query the Chinook database at /chinook.db to get total revenue "
                        "by genre. Create a clean donut chart showing each genre's share "
                        "of total sales revenue. Group any genres that individually "
                        "account for less than 3% of total revenue into a single 'Other' "
                        "slice. Label each slice with the genre name and percentage. "
                        "Use a visually distinct color palette, leave a white center hole, "
                        "and make sure no labels overlap with each other or with the title. "
                        "Add enough top padding so the title is fully visible. "
                        "Save the chart to /genre_revenue.png."
                    ),
                }
            ]
        }
    )
    print(result["messages"][-1].content)

    png_bytes = ls_sandbox.read("/genre_revenue.png")
    out_path = Path(__file__).parent / "genre_revenue.png"
    out_path.write_bytes(png_bytes)
    print(f"Chart saved to {out_path}")

finally:
    client.delete_sandbox(ls_sandbox.name)
