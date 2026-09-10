// typescript/m5/sales_assistant_sandbox/tools/search.ts
/**
 * Web search tool for the genre-researcher subagent (weekly newsletter).
 *
 * Thin wrapper over Tavily, identical in spirit to the Module 4 lab. Belongs
 * only to the research subagent. Requires TAVILY_API_KEY in the environment;
 * if it's absent the tool is simply not registered (see subagents.ts), so
 * the rest of the assistant still runs.
 */
import { z } from "zod";
import { context, tool } from "langchain";
import { TavilySearchAPIWrapper } from "@langchain/tavily";

const tavily = new TavilySearchAPIWrapper({
  tavilyApiKey: process.env.TAVILY_API_KEY,
});

const MAX_ATTEMPTS = 3;
const RETRY_DELAY_MS = 2000;

// newsletter-agent's genre research fires several of these off at once in one
// turn, and the remote sometimes hands back a keep-alive socket it has already
// closed, surfacing as a connection reset. Python's version avoids the shared
// pool by building a fresh client per call; that has no equivalent here, since
// node's fetch keeps its pool in a process-global dispatcher and a new wrapper
// would draw from the same one. So the retry is what actually covers it.
//
// Only transport failures are retried: fetch rejects those with a `cause`,
// while a non-ok HTTP response arrives as a plain `Error ${status}: ...`.
// Retrying a 401 or 429 would just amplify load and hide the real problem.
function isTransportError(err: unknown): boolean {
  return err instanceof Error && (err.cause !== undefined || err.message === "fetch failed");
}

export const internetSearch = tool(
  async ({ query, maxResults }: { query: string; maxResults: number }) => {
    let lastError: unknown;
    for (let attempt = 0; attempt < MAX_ATTEMPTS; attempt++) {
      try {
        return await tavily.rawResults({ query, max_results: maxResults, topic: "news" });
      } catch (err) {
        if (!isTransportError(err)) throw err;
        lastError = err;
        if (attempt < MAX_ATTEMPTS - 1) {
          await new Promise((resolve) => setTimeout(resolve, RETRY_DELAY_MS));
        }
      }
    }
    throw lastError;
  },
  {
    name: "internet_search",
    description: context`
      Search the web for recent news. Use this to research what's new in a
      music genre — new releases, notable artists, trends, and events.`,
    schema: z.object({
      query: z.string(),
      maxResults: z.number().default(8),
    }),
  }
);
