// typescript/m5/async_lab/specialized_agent/agent.ts
/**
 * M5.4 Lab: the "specialized" deployment.
 *
 * THE IDEA
 * This is a second, independent deployment, served by its own
 * `langgraphjs dev` process on its own port. The analysis tool below is
 * deliberately slow, the kind of job you don't want running inside the main
 * agent's process where it would block that agent's own model calls. Giving
 * it its own deployment also means it can be scaled, restarted, or taken
 * down without touching the main agent.
 *
 * The main agent reaches it over HTTP as an async subagent, exactly like any
 * other remote Agent Protocol server.
 *
 * RUN
 *   cd typescript/m5/async_lab/specialized_agent
 *   pnpm exec langgraphjs dev --port 2025
 * Leave this running, then start ../main_agent in a second terminal.
 */

import { z } from "zod";
import { tool } from "langchain";
import { initChatModel } from "langchain";
import { createDeepAgent } from "deepagents";

interface SalesRow {
  region: string;
  product: string;
  unitsSold: number;
  revenue: number;
}

const SALES: SalesRow[] = [
  { region: "West", product: "Widget", unitsSold: 1200, revenue: 36000 },
  { region: "West", product: "Gadget", unitsSold: 850, revenue: 42500 },
  { region: "East", product: "Widget", unitsSold: 980, revenue: 29400 },
  { region: "East", product: "Gadget", unitsSold: 1400, revenue: 70000 },
  { region: "Central", product: "Widget", unitsSold: 630, revenue: 18900 },
  { region: "Central", product: "Gadget", unitsSold: 720, revenue: 36000 },
];

const analyzeSales = tool(
  async ({ groupBy }: { groupBy: "region" | "product" }) => {
    // Stands in for a genuinely slow job (a big data pipeline, a model call, etc.).
    await new Promise((resolve) => setTimeout(resolve, 20_000));

    const totals = new Map<string, { unitsSold: number; revenue: number }>();
    for (const row of SALES) {
      const key = row[groupBy];
      const acc = totals.get(key) ?? { unitsSold: 0, revenue: 0 };
      acc.unitsSold += row.unitsSold;
      acc.revenue += row.revenue;
      totals.set(key, acc);
    }

    return [...totals.entries()]
      .sort((a, b) => b[1].revenue - a[1].revenue)
      .map(
        ([name, t]) =>
          `${name}: $${t.revenue.toLocaleString("en-US")} revenue, ${t.unitsSold.toLocaleString("en-US")} units`
      )
      .join("\n");
  },
  {
    name: "analyze_sales",
    description:
      'Run a full sales breakdown, grouped by "region" or by "product", ranked highest revenue first. ' +
      "This is a slow, heavyweight analysis job, not something you'd want blocking the main agent's own model calls.",
    schema: z.object({
      groupBy: z
        .enum(["region", "product"])
        .default("region")
        .describe('Which dimension to group the breakdown by: "region" or "product".'),
    }),
  }
);

const model = await initChatModel("anthropic:claude-haiku-4-5");

// `langgraph.json` points at this module-level export: "./agent.ts:graph".
export const graph = createDeepAgent({ model, tools: [analyzeSales] });
