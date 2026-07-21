// typescript/m4/m4.2_homework.ts
/**
 * M4.2 Homework: Build Your Own Subagent Team.
 *
 * THE IDEA
 * The lab built one "editor" main agent that delegated to a single
 * genre-researcher subagent type, once per music genre. This homework asks
 * you to build your own small team of 2-3 subagent types for a domain YOU
 * pick (not a newsletter, not music genres): a trip-planning assistant, a
 * home-cooking assistant, a study buddy, whatever you're into. There's no
 * single correct team here, that's the point. Two students doing this
 * homework could end up with completely different subagents and completely
 * different delegation instructions.
 *
 * WHAT YOU FILL IN
 *   TODO 1: define 2-3 SubAgent objects (name, description, systemPrompt, and
 *     optionally model) for your own domain.
 *   TODO 2: write the main agent's system prompt, telling it which subagent
 *     to call for which part of the job, and a user request that should
 *     trigger delegation to more than one of your subagents.
 *
 * RUN
 *   cd typescript
 *   pnpm tsx ./m4/m4.2_homework.ts
 */

import { createDeepAgent, type SubAgent } from "deepagents";

import { model, strongModel } from "../models.js";

// ════════════════════════════════════════════════════════════════════════
// TODO 1: Define your own subagent team.
//
// Requirements:
//   - 2 to 3 subagents, each a plain object with at least "name",
//     "description", and "systemPrompt".
//   - Each subagent should have a distinct, narrow job; the main agent will
//     decide when to call each one based on its "description".
//   - "model" is optional per subagent (defaults to the main agent's model
//     if omitted); the lab used the cheaper `model` for its researcher.
//
// Example shape (delete this and write your own):
//   return [
//     {
//       name: "your-subagent-name",
//       description: "When the main agent should delegate to this one.",
//       systemPrompt: "You are ... Your job is to ...",
//       model,
//     },
//     ...
//   ];
// ════════════════════════════════════════════════════════════════════════

function buildSubagentTeam(): SubAgent[] {
  // TODO 1: return a list of 2-3 SubAgent objects for your own domain.
  throw new Error("TODO 1: see the comment block above");
}

// ════════════════════════════════════════════════════════════════════════
// TODO 2: Write the main agent's system prompt and a triggering request.
//
// MAIN_PROMPT should tell the main agent about each subagent by name and
// when to call it (mirror how EDITOR_PROMPT in the lab named
// genre-researcher and explained the job).
// USER_REQUEST should be a task that should make the main agent delegate to
// more than one of your subagents.
// ════════════════════════════════════════════════════════════════════════

const MAIN_PROMPT = `TODO 2: replace this with your own main agent system prompt.`;
const USER_REQUEST =
  "TODO 2: replace this with a request that should trigger delegation to your team.";

const agent = createDeepAgent({
  model: strongModel,
  name: "Homework_Team_Agent",
  systemPrompt: MAIN_PROMPT,
  subagents: buildSubagentTeam(),
});

const result = await agent.invoke(
  { messages: [{ role: "user", content: USER_REQUEST }] },
  { recursionLimit: 50 }
);
console.log(result.messages.at(-1)?.content);
