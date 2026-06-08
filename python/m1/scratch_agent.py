import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from models import model

from deepagents import create_deep_agent

SYSTEM_PROMPT = (
    "You are a salty pirate captain with decades at sea. Talk in 'arr' and nautical slang. "
    "Call the user 'matey' and frame your answers as if charting a course."
)

agent = create_deep_agent(model=model, system_prompt=SYSTEM_PROMPT)
result = agent.invoke({"messages": [{"role": "user", "content": "What is an LLM?"}]})
print(result["messages"][-1].content)
