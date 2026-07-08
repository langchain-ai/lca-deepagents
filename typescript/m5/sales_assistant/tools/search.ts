// typescript/m5/sales_assistant/tools/search.ts
/**
 * Web search tool for the genre-researcher subagent (weekly newsletter).
 *
 * Thin wrapper over Tavily, identical in spirit to the Module 4 lab. Belongs
 * only to the research subagent. Requires TAVILY_API_KEY in the environment;
 * if it's absent the tool is simply not registered (see subagents.ts), so
 * the rest of the assistant still runs.
 */
import { TavilySearchAPIWrapper } from "@langchain/tavily";
import { tool } from "@langchain/core/tools";
import { z } from "zod";

const tavily = new TavilySearchAPIWrapper({
  tavilyApiKey: process.env.TAVILY_API_KEY,
});

export const internetSearch = tool(
  async ({ query, maxResults }: { query: string; maxResults: number }) => {
    return tavily.rawResults({ query, max_results: maxResults, topic: "news" });
  },
  {
    name: "internet_search",
    description:
      "Search the web for recent news. Use this to research what's new in a " +
      "music genre — new releases, notable artists, trends, and events.",
    schema: z.object({
      query: z.string(),
      maxResults: z.number().default(8),
    }),
  }
);
