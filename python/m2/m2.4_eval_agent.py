from deepagents import create_deep_agent
from langchain_quickjs import CodeInterpreterMiddleware

from models import model

agent = create_deep_agent(
    model=model,
    middleware=[CodeInterpreterMiddleware()],
)

result = agent.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "Use the eval tool to compute and return the first 15 Fibonacci numbers.",
            }
        ]
    }
)

print(result["messages"][-1].text)
