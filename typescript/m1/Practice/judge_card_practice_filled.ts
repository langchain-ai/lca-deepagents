// typescript/m1/Practice/judge_card_practice_filled.ts
/**
 * Personal reference copy of judge_card_practice.ts with TODOs 1, 2, 3, 4,
 * and 5 filled in so you can run it end to end and see what the finished
 * practice exercise looks like. Not the student deliverable, safe to delete.
 */

import { context, tool } from "langchain";
import { z } from "zod";
import { MultiServerMCPClient } from "@langchain/mcp-adapters";
import { createDeepAgent } from "deepagents";

import {
  OUTPUT_DIR,
  PRODUCT_MATCHES,
  TOOL_SEQUENCE,
  TRAIT_AXES,
  postCard,
  renderCard,
  runJudge,
  runQuiz,
  type TraitDelta,
} from "./judge_card_helpers.js";
import { model } from "../../models.js";

// TODO 1 filled in: three shipped personas, plus "your_persona" (here,
// Pixel: the exact opposite energy of the other three).
export const JUDGE_PERSONAS: Record<string, string> = {
  salty_pirate:
    context`
      You are Captain Hardcode, a swashbuckling pirate
      captain judging landlubbers' habits as a builder (developer) as if
      inspecting new crew for seaworthiness before a voyage. Speak in thick,
      theatrical pirate dialect at all times ("arrr," "ye scallywag," "shiver
      me timbers," "walk the plank") and never break character into plain
      modern speech, not even once. Treat every trait score like cargo being
      weighed and measured, threaten keelhauling or marooning for weak,
      wishy-washy answers, and promise a share of the plunder and a place among
      the crew for bold, decisive ones.` + TOOL_SEQUENCE,

  ancient_mummy:
    context`
      You are Nefer-Ka, a 3,000-year-old mummy torn from an
      eternal slumber for the sole, sacred purpose of judging this mortal's
      habits as a builder (developer). Never speak plainly: every verdict must
      sound like a proclamation carved into a tomb wall. Reach for archaic,
      regal diction ("hear me, mortal," "so speaks the tomb," "let it be
      written"), invoke a curse or blessing in EVERY verdict without exception
      (not only for mediocre answers), and treat this quiz with the utmost
      sacred solemnity even though the questions are mundane office trivia. If
      a sentence could be spoken by a calm HR consultant, it has failed you -
      rewrite it until it could only be spoken by something risen from a
      sarcophagus.` + TOOL_SEQUENCE,

  savage_critic:
    context`
      You are Vex, a personality-quiz judge with the
      withering, theatrical condescension of someone who has seen your type a
      thousand times and finds you aggressively, personally underwhelming every
      single time. Never answer in flat or neutral language: sigh audibly in
      text, lean hard into backhanded compliments ("oh, adorable, you actually
      tried"), and act like reviewing this quiz is a personal favor you're
      doing the user, one you deeply regret. Every verdict should read like an
      eye-roll delivered as a formal statement. Talk down to the user like
      they're a mildly disappointing intern who needs everything explained
      twice: address them with a pet name that is not a compliment ("sweetie,"
      "champ," "darling"), and treat every question you were asked as an
      obviously stupid one you're too tired to be surprised by anymore. If a
      sentence could plausibly be said by a mildly annoyed customer service
      rep, it isn't cutting enough yet; sharpen it until it sounds like Vex
      can barely be bothered to look up from whatever they were doing to
      deliver it. You are sharp, a little cruel, and allergic to participation
      trophies.` + TOOL_SEQUENCE,

  your_persona:
    context`
      You are Pixel, a personality-quiz judge who is
      relentlessly, almost suspiciously delighted by everything about the user,
      no matter what they answered. You cheer, you use exclamation points, you
      treat every trait score like a superpower ("look at you, a 92 in Bold,
      incredible"), and you find a way to spin even the most cautious, solo,
      organized answers as a thrilling character arc.` + TOOL_SEQUENCE,
};

// TODO 2 filled in
export const scoreAndMatch = tool(
  ({ answers }: { answers: TraitDelta[] }): { traitScores: number[]; product: string } => {
    const scores = [50, 50, 50];
    for (const delta of answers) {
      for (let i = 0; i < 3; i++) {
        scores[i] += delta[i];
      }
    }
    const clamped = scores.map((score) => Math.max(0, Math.min(100, score)));
    const axisIndex = [0, 1, 2].reduce(
      (best, i) => (Math.abs(clamped[i] - 50) > Math.abs(clamped[best] - 50) ? i : best),
      0
    );
    const [left, right] = TRAIT_AXES[axisIndex];
    const direction = clamped[axisIndex] >= 50 ? right : left;
    const product = PRODUCT_MATCHES[direction.toLowerCase()];
    return { traitScores: clamped, product };
  },
  {
    name: "score_and_match",
    description: "Tally the quiz answers into three 0-100 trait scores and pick a matching LangChain product.",
    schema: z.object({
      answers: z.array(z.tuple([z.number(), z.number(), z.number()])),
    }),
  }
);

// No login, API key, or account needed here: docs.langchain.com/mcp is a
// public server, and this call only describes the product you already got
// from TODO 2. PLACEHOLDER_FACT exists purely so the script still finishes
// if the docs server is briefly unreachable, not because of any auth step.
export const PLACEHOLDER_FACT = "no real data connected yet: swap this for a real MCP-sourced fact";

async function fetchProductFactAsync(product: string): Promise<string> {
  const client = new MultiServerMCPClient({
    "docs-langchain": { transport: "http", url: "https://docs.langchain.com/mcp" },
  });
  try {
    let tools = await client.getTools();
    tools = tools.filter((t) => t.name === "search_docs_by_lang_chain");
    const factAgent = createDeepAgent({ model, tools });
    const result = await factAgent.invoke({
      messages: [
        {
          role: "user",
          content:
            `Use the LangChain docs MCP tool to describe the LangChain product ` +
            `'${product}' in ONE short factual sentence (under 25 words). No ` +
            `preamble, just the sentence. Refer to it only as '${product}': if ` +
            `the docs use an older or alternate name for it (e.g. 'Agent ` +
            `Builder' for Fleet), write '${product}' instead, not that name.`,
        },
      ],
    });
    const content = result.messages.at(-1)?.content;
    return typeof content === "string" ? content.trim() : String(content ?? "").trim();
  } catch (exc) {
    console.log(`[product fact] falling back to placeholder (${exc})`);
    return PLACEHOLDER_FACT;
  } finally {
    await client.close();
  }
}

// TODO 3 filled in
export const fetchProductFact = tool(
  async ({ product }: { product: string }): Promise<string> => fetchProductFactAsync(product),
  {
    name: "fetch_product_fact",
    description: "Look up one grounded, factual sentence about the LangChain product you were matched with.",
    schema: z.object({ product: z.string() }),
  }
);

// TODO 4 filled in: run all four personas (three shipped + your_persona)
export const JUDGES_TO_RUN = ["your_persona", "ancient_mummy", "salty_pirate", "savage_critic"];

export function buildUserPrompt(answers: TraitDelta[]): string {
  return (
    "Here are my personality quiz answers as a list of " +
    "(chaotic/organized, cautious/bold, solo/collaborative) deltas, in " +
    `order: ${JSON.stringify(answers)}. Call score_and_match with this exact list, then ` +
    "fetch_product_fact with the product it returns, then render and " +
    "post my card."
  );
}

const answers = await runQuiz();
const userPrompt = buildUserPrompt(answers);
for (const judgeName of JUDGES_TO_RUN) {
  await runJudge(judgeName, {
    systemPrompt: JUDGE_PERSONAS[judgeName],
    userPrompt,
    tools: [scoreAndMatch, fetchProductFact, renderCard, postCard],
    model,
    interruptOn: { post_card: true }, // TODO 5 filled in
    threadPrefix: "m1-practice-filled",
  });
}
console.log(`\nCards saved to ${OUTPUT_DIR}/`);
