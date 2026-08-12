from deepagents import create_deep_agent

from models import model
from dotenv import load_dotenv

load_dotenv()

agent = create_deep_agent(model=model)

result = agent.invoke({"messages": [{"role": "user", "content": "What is an LLM?"}]})

print(result["messages"][-1].content)
