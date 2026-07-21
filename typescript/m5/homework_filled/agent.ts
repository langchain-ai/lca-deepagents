// typescript/m5/homework_filled/agent.ts
/**
 * Reference copy of the m5.2 homework starter with TODOs 1 and 2 filled
 * in so you can deploy it and chat with it in Studio, or query it over
 * the API with call_agent_api.ts in this same folder. This is just one
 * possible answer, so yours might be different. Explore!
 */

import { z } from "zod";
import { tool } from "langchain";
import { createDeepAgent } from "deepagents";

import { model } from "../../models.js";

const EXTREME_WEATHER_FACTS: Record<string, string> = {
  hottest:
    "The hottest air temperature ever reliably recorded on Earth's surface was 56.7°C (134°F), in Death Valley, California, in July 1913.",
  coldest:
    "The coldest temperature ever recorded on Earth's surface was -89.2°C (-128.6°F), at Vostok Station, Antarctica, in July 1983.",
  windiest:
    "The highest surface wind speed ever measured was 408 km/h (253 mph), during a tornado near Bridge Creek, Oklahoma, in 1999.",
  wettest:
    "Mawsynram, India receives the most average annual rainfall of any inhabited place on Earth, over 11,000 mm (about 467 inches) a year.",
};

// TODO 1 filled in
const lookupExtremeWeather = tool(
  ({ category }: { category: string }) => {
    const key = category.toLowerCase();
    return (
      EXTREME_WEATHER_FACTS[key] ??
      `No record on file for '${category}'. Try hottest, coldest, windiest, or wettest.`
    );
  },
  {
    name: "lookup_extreme_weather",
    description:
      "Look up a fact about extreme weather. category is one of: hottest, coldest, windiest, wettest.",
    schema: z.object({ category: z.string() }),
  }
);

// TODO 2 filled in
const SYSTEM_PROMPT = `You are Storm Watch, a caffeinated, slightly breathless
storm-chaser broadcasting live from wherever the weather is worst. Always
call lookup_extreme_weather before answering a weather-records question,
then deliver the fact like a live field report: urgent and a little
dramatic, before wrapping up calmly.`;

// `langgraph.json` points at this module-level export: "./agent.ts:graph".
export const graph = createDeepAgent({
  model,
  tools: [lookupExtremeWeather],
  systemPrompt: SYSTEM_PROMPT,
});
