// typescript/m5/sales_assistant_sandbox/newsletter-agent.ts
/**
 * newsletter-agent: a standalone graph, launched as an async subagent.
 *
 * Registered as its own entry in langgraph.json so the main agent's
 * async-subagent middleware can launch it via the LangGraph SDK and return
 * immediately, instead of blocking on an in-process subagent call.
 *
 * This graph does the FULL newsletter job itself — researching every genre
 * and assembling the finished HTML — rather than being one of several
 * parallel async launches the main agent has to fan back in. Internally it
 * delegates to a genre-researcher subagent the ordinary, SYNCHRONOUS way
 * (the `task` tool, same mechanism the main agent's other specialists use):
 * those calls happen in-process, in parallel, within this graph's own single
 * run, so there is nothing to fan in across threads.
 *
 * No completion-notification middleware here — the main agent finds out
 * this task is done the ordinary way, by checking
 * check_async_task/list_async_tasks the next time it's asked, rather than
 * being woken by a cross-thread run. That's what lets this graph be a plain,
 * static object instead of a per-run async factory.
 *
 * Storage: a StoreBackend namespaced by this run's own thread_id, resolved
 * lazily from the backend context — read only when the backend actually does
 * a store operation during a real run, not at graph construction time, so no
 * factory/config param is needed to build this graph. Each start_async_task
 * call creates a fresh thread here, so that thread_id is already a unique,
 * collision-free namespace — no cross-graph ID forwarding needed. The
 * genre-researcher subagent inherits this same backend (subagents inherit
 * their parent's backend unless they set their own), so its
 * /research/<genre>/sources.md dumps land in this run's own namespace too.
 */
import { StoreBackend, createDeepAgent, type SubAgent } from "deepagents";
import { context } from "langchain";

import { model, strongModel } from "../../models.js";
import { GENRE_PROMPT } from "./subagents.js";
import { markdownToHtml } from "./tools/html.js";

// This module is always imported by the langgraph platform (it's a
// registered graph in langgraph.json) regardless of whether the main agent
// ever exposes the launch tool for it — so importing tools/search.js (which
// instantiates a Tavily client from TAVILY_API_KEY) has to stay conditional
// here too, matching agent.ts's own enableSearch guard.
const enableSearch = Boolean(process.env.TAVILY_API_KEY);
const genreResearcherTools = enableSearch
  ? [(await import("./tools/search.js")).internetSearch]
  : [];

const NEWSLETTER_AGENT_PROMPT = context`
  You assemble Chinook's weekly "This Week in Music" customer newsletter. You
  run in the background — the sales assistant already told Jane you're
  working and will hand her the finished result the moment you're done.

  You will be given a list of genres to cover. For EACH genre, delegate to
  the genre-researcher subagent — call it once per genre, all in this same
  turn, so the research happens in parallel — and collect its returned
  segment.

  Once every genre-researcher call has returned:
  1. Assemble one Markdown document from the genres that succeeded: a
     "# This Week in Music" title, a one-sentence intro, then each genre's
     segment in the order given. If a genre's research failed, skip it and
     add one short line noting which genre(s) didn't make it this week —
     don't leave the newsletter looking unfinished, and don't silently drop
     the fact that something's missing. If every genre failed, don't produce
     a newsletter at all — reply with a single plain sentence saying research
     failed for every genre this week, and stop there.
  2. Call markdown_to_html on the assembled Markdown.

  Reply with ONLY the tool's returned HTML — nothing before it, nothing after
  it, no commentary. Your reply is written directly to a file verbatim; any
  extra sentence you add around the HTML ends up inside that file too.`;

const genreResearcher: SubAgent = {
  name: "genre-researcher",
  description: context`
    Research one music genre and write a newsletter segment about
    what's new in it. Call once per genre, in parallel.`,
  systemPrompt: GENRE_PROMPT,
  tools: genreResearcherTools,
  model,
};

const backend = new StoreBackend({
  namespace: (ctx) => [ctx.config?.configurable?.thread_id as string, "research"],
});

export const graph = createDeepAgent({
  model: strongModel,
  tools: [markdownToHtml],
  systemPrompt: NEWSLETTER_AGENT_PROMPT,
  subagents: [genreResearcher],
  backend,
  name: "newsletter-agent",
});
