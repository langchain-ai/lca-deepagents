from deepagents import create_deep_agent

from models import model

SYSTEM_PROMPT = (
    "You are a drawling cowboy from the Old West. Speak only in cowboy slang, partner. "
    "Pepper every reply with 'howdy', 'reckon', and 'much obliged', and keep it easygoing."
)

agent = create_deep_agent(
    model=model,
    system_prompt=SYSTEM_PROMPT,
    name="butler_agent",
)

result = agent.invoke({"messages": [{"role": "user", "content": "What is an LLM?"}]})

print(result["messages"][-1].content)
