// typescript/m5/hello/agent.ts
/**
 * A minimal deep agent, exposed as a graph for `langgraph dev`.
 *
 * This is the whole agent: a model, nothing else. The point of this lab is the
 * *deployment*, not the agent — so we keep the agent as small as it gets and let
 * `langgraph dev` serve it over HTTP.
 */

import { createDeepAgent } from "deepagents";

import { model } from "../../models.js";

// `langgraph.json` points at this module-level export: "./agent.ts:graph".
export const graph = createDeepAgent({ model });
