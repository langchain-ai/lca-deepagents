import { createDeepAgent } from "deepagents";
import { HumanMessage } from "@langchain/core/messages";

import { model } from "../models.js";

const agent = createDeepAgent({ model });

const result = await agent.invoke({"messages": [{"role": "user", "content": "What is an LLM?"}]});

console.log(result.messages[result.messages.length - 1].content);
