// typescript/m1/m1.5_homework.ts
/**
 * M1.5 Homework: Build Your Own Custom Tool.
 *
 * THE IDEA
 * The lab wired up one custom tool (readSql) for one fixed topic (the
 * Chinook music database). This homework asks you to do the same thing for
 * a topic YOU pick: something you actually know or care about (a game, a
 * sport, a show, your favorite band's discography, local trivia, whatever).
 * There's no single correct topic or persona here, that's the point. Two
 * students doing this homework could end up with two completely different
 * tools and agents.
 *
 * WHAT YOU FILL IN
 *   TODO 1: write your own custom tool with the `tool()` helper. Pick any
 *     topic, store a small lookup (a plain object is fine, no API needed)
 *     of facts about it, and return one back based on the argument the
 *     model passes.
 *   TODO 2: write a system prompt that gives the agent a persona of your
 *     choosing and tells it to use your tool before answering.
 *
 * RUN
 *   cd typescript
 *   pnpm tsx ./m1/m1.5_homework.ts
 */

import { z } from "zod";
import { tool } from "langchain";
import { createDeepAgent } from "deepagents";

import { model } from "../models.js";

// ════════════════════════════════════════════════════════════════════════
// TODO 1: Define your own custom tool.
//
// Requirements:
//   - Keep the `tool()` helper, with a `name`, `description`, and `schema`.
//   - Give it a real description: one sentence the model will read to
//     decide when to call this tool.
//   - Have it take at least one argument and return a string.
//   - The lookup data can just live in this file (an object, an array,
//     whatever fits your topic). No external API or key needed.
//
// Example shape (delete this and write your own):
//   const lookupSomething = tool(
//     ({ query }) => {
//       ...
//     },
//     {
//       name: "lookup_something",
//       description: "One sentence describing what this returns and when to call it.",
//       schema: z.object({ query: z.string() }),
//     }
//   );
// ════════════════════════════════════════════════════════════════════════

const yourCustomTool = tool(
  ({ query }) => {
    throw new Error("TODO 1: see the comment block above");
  },
  {
    name: "your_custom_tool",
    description: "TODO 1: replace this description and body with your own tool.",
    schema: z.object({ query: z.string() }),
  }
);

// ════════════════════════════════════════════════════════════════════════
// TODO 2: Write a system prompt for your agent.
//
// Give it a persona (a name, a voice, a personality, anything you want)
// and tell it to call yourCustomTool (rename it if you like) before
// answering, the same way the lab's SYSTEM_PROMPT pointed the agent at
// readSql.
// ════════════════════════════════════════════════════════════════════════

const SYSTEM_PROMPT = "TODO 2: replace this with your own system prompt.";

if (yourCustomTool.description.includes("TODO 1")) {
  throw new Error("TODO 1: see the comment block above");
}
if (SYSTEM_PROMPT.includes("TODO 2")) {
  throw new Error("TODO 2: see the comment block above");
}

const agent = createDeepAgent({
  model,
  name: "Homework_Agent",
  tools: [yourCustomTool],
  systemPrompt: SYSTEM_PROMPT,
});

const result = await agent.invoke({
  messages: [{ role: "user", content: "Ask your agent a question that needs your tool." }],
});

console.log(result.messages.at(-1)?.content);
