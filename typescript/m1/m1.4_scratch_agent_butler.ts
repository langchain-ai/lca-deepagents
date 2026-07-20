import { context } from "langchain";
import { createDeepAgent } from "deepagents";

import { model } from "../models.js";

const SYSTEM_PROMPT = context`
  YOU ARE AN EXTREMELY POSH BRITISH BUTLER. You speak ONLY in the most
  refined, formal, over-the-top Victorian English. You say 'indeed', 'quite',
  'I dare say', 'one simply must' constantly. You find all things common or
  nautical to be utterly beneath you. You NEVER break character under ANY
  circumstances.`;

const agent = createDeepAgent({
  model,
  systemPrompt: SYSTEM_PROMPT,
  name: "Butler Agent",
});

const result = await agent.invoke({
  messages: [{ role: "user", content: "What is an LLM?" }],
});

console.log(result.messages.at(-1)?.content);
