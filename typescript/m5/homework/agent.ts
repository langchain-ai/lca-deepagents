// typescript/m5/homework/agent.ts
/**
 * M5.2 Homework: Deploy Your Own Agent.
 *
 * THE IDEA
 * The lab deployed a fairly bare-bones agent (no tools, no persona, just
 * createDeepAgent({ model })) and you only ever talked to it through
 * Studio's chat panel. This homework has two parts: first, deploy an agent
 * with your personal touch; second, talk to it the way any other client
 * would, straight over the Agent Server API this lesson covers, instead of
 * through Studio.
 *
 * WHAT YOU FILL IN
 *   TODO 1: write your own tool with the `tool()` helper on a topic of your
 *     choosing. A plain object lookup is enough, no external API or key
 *     required.
 *   TODO 2: write a systemPrompt that gives the agent a persona of your
 *     choosing and tells it to call your tool before answering.
 *   Then open call_agent_api.ts in this same folder for TODO 3, which
 *   talks to this deployed agent over HTTP instead of through Studio.
 *
 * RUN
 *   cd typescript/m5/homework
 *   pnpm exec langgraphjs dev
 * Then chat with your agent in the Studio window that opens, or see
 * call_agent_api.ts to talk to it over the API instead.
 */

import { z } from "zod";
import { tool } from "langchain";
import { createDeepAgent } from "deepagents";

import { model } from "../../models.js";

// TODO 1: replace this with your own tool.
const lookupFact = tool(
  (_: { topic: string }) => {
    throw new Error("TODO 1: see the comment block above");
  },
  {
    name: "lookup_fact",
    description: "TODO 1: replace this with your own tool on a topic of your choosing.",
    schema: z.object({ topic: z.string() }),
  }
);

// TODO 2: replace this with your own persona system prompt.
const SYSTEM_PROMPT = "TODO 2: replace this with your own system prompt.";

// `langgraph.json` points at this module-level export: "./agent.ts:graph".
export const graph = createDeepAgent({ model, tools: [lookupFact], systemPrompt: SYSTEM_PROMPT });
