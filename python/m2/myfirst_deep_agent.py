# python/m2/myfirst_deep_agent.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from models import model
from deepagents import create_deep_agent

agent = create_deep_agent(model=model)

result = agent.invoke(
    {"messages": [{"role": "user", "content": "What is an LLM?"}]},
    config={"configurable": {"thread_id": "lab-myfirst"}},
)

print(result["messages"][-1].content)
