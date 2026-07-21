// typescript/m1/m1.4_homework_filled.ts
/**
 * Reference copy of m1.4_homework.ts with TODOs 1 and 2 filled in so you
 * can run it end to end and see what "done" looks like. This is just one
 * possible answer, so yours might be different. Explore!
 */

import { createDeepAgent } from "deepagents";

import { model } from "../models.js";

// TODO 1 filled in
const SYSTEM_PROMPT =
  "You only answer questions about houseplants: care, watering, light, " +
  "pests, soil, and propagation. If asked about anything outside " +
  "houseplants, say you can't help with that and redirect the " +
  "conversation back to houseplants.";

const agent = createDeepAgent({
  model,
  systemPrompt: SYSTEM_PROMPT,
  name: "Homework_Agent",
});

// TODO 2 filled in
async function runTestPrompts() {
  const prompts = [
    "Why are the leaves on my pothos turning yellow?",
    "What's a good way to organize my closet?",
  ];
  for (let i = 0; i < prompts.length; i++) {
    const prompt = prompts[i];
    const result = await agent.invoke({
      messages: [{ role: "user", content: prompt }],
    });
    console.log(`=== Test prompt ${i + 1}: ${prompt} ===`);
    console.log(result.messages.at(-1)?.content);
    console.log();
  }
}

await runTestPrompts();
