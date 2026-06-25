from pathlib import Path

from deepagents import create_deep_agent

from models import model

agent = create_deep_agent(
    model=model,
    skills=[str(Path(__file__).parent / "skills")],
    system_prompt="You are a sales assistant.",
)

result = agent.invoke({"messages": [{"role": "user", "content": "Write a cold outreach message for a prospect at a mid-size logistics company."}]})
print(result["messages"][-1].content)
