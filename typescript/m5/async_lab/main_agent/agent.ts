// typescript/m5/async_lab/main_agent/agent.ts
/**
 * M5.4 Lab: the main agent, delegating to a separate, specialized deployment.
 *
 * THE IDEA
 * This agent stays light: it pulls the shared model from the course's
 * models.ts, like every other lab in the course. It delegates all sales
 * analysis to an async subagent, "analyst", running as its OWN deployment on
 * port 2025 (see ../specialized_agent), so the slow analysis job never
 * blocks this agent's own model calls.
 *
 * RUN
 *   Start ../specialized_agent first (see its own docstring), then:
 *     cd typescript/m5/async_lab/main_agent
 *     pnpm exec langgraphjs dev
 * Chat with it in the Studio window that opens. Ask it to run two analyses
 * at once (e.g. by region and by product), then keep chatting, it should
 * report two task IDs right away. From there you can update one task with
 * new instructions, cancel the other, and check on what's left.
 */

import { type AsyncSubAgent, createDeepAgent } from "deepagents";

import { model } from "../../../models.js";

const subagents: AsyncSubAgent[] = [
  {
    name: "analyst",
    description:
      "Runs sales analysis grouped by region or by product, returning total " +
      "revenue and units sold per group, ranked by revenue - that's all the " +
      "data available, so don't ask it for anything else (e.g. average " +
      "transaction value, transaction counts, or growth metrics). Slow, so it " +
      "lives on its own deployment instead of running in-process here. Launch " +
      "one task per grouping if you need both.",
    graphId: "agent",
    // `langgraphjs dev` binds IPv6 loopback ([::1]) only, so use "localhost"
    // here rather than "127.0.0.1", which will not reach it.
    url: "http://localhost:2025",
  },
];

// `langgraph.json` points at this module-level export: "./agent.ts:graph".
export const graph = createDeepAgent({ model, subagents });
