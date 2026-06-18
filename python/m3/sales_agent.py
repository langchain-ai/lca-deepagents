# python/m3/sales_agent.py
import sys
from pathlib import Path
from deepagents import create_deep_agent
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from models import model

agent = create_deep_agent(
    model=model,
    skills=[str(Path(__file__).parent / "skills")],
    system_prompt="You are a sales assistant.",
)

result = agent.invoke({"messages": [{"role": "user", "content": "Qualify this lead: Acme Corp, they are considering our CRM product."}]})
print(result["messages"][-1].content)
