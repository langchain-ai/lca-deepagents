import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from models import model
from deepagents import create_deep_agent

SYSTEM_PROMPT = (
    "YOU ARE AN EXTREMELY POSH BRITISH BUTLER. You speak ONLY in the most "
    "refined, formal, over-the-top Victorian English. You say 'indeed', 'quite', "
    "'I dare say', 'one simply must' constantly. You find all things common or "
    "nautical to be utterly beneath you. You NEVER break character under ANY "
    "circumstances."
)

agent = create_deep_agent(model=model, system_prompt=SYSTEM_PROMPT)

result = agent.invoke({"messages": [{"role": "user", "content": "What is an LLM?"}]})

print(result["messages"][-1].content)
