// typescript/m1/m1.8_homework.ts
/**
 * M1.8 Homework: Gate Your Own Action Tool.
 *
 * THE IDEA
 * Lab 1 gated one action tool, `sendEmail`, behind `interruptOn` and
 * walked through approve/edit/reject on it. This homework asks you to do
 * the same thing for an action tool of your own choosing: post a tweet,
 * book a meeting room, place an order, delete a file, whatever you like.
 *
 * WHAT YOU FILL IN
 *   TODO 1: define your own action tool with `tool(...)` and a Zod
 *     schema. Pick any side-effecting action you like; the function body
 *     can just return a confirmation string, the same way Lab 1's
 *     `sendEmail` did.
 *   TODO 2: configure `interruptOn` for your tool with an
 *     `allowedDecisions` list of your choosing, and write a system
 *     prompt plus an initial user request that would lead the model to
 *     propose calling it.
 *
 * The review loop below (borrowed from Lab 1, unchanged) prints any
 * pending tool call and asks you to approve, edit, or reject it. Run the
 * script more than once, picking a different choice each time, to see
 * both an approve/edit path and a reject path.
 *
 * RUN
 *   cd typescript
 *   pnpm tsx ./m1/m1.8_homework.ts
 */

import { createInterface } from "node:readline/promises";
import { z } from "zod";

import { tool, ToolMessage } from "langchain";
import { Command, INTERRUPT, isInterrupted, MemorySaver } from "@langchain/langgraph";
import { createDeepAgent } from "deepagents";

import { model } from "../models.js";

interface ActionRequest {
  name: string;
  args: Record<string, unknown>;
}

interface ApprovalRequest {
  actionRequests: ActionRequest[];
}

// ════════════════════════════════════════════════════════════════════════
// TODO 1: Define your own action tool.
//
// Requirements:
//   - Keep the `tool(...)` wrapper with a Zod schema.
//   - Give it a real description describing the action it performs.
//   - Have it take at least one argument and return a confirmation
//     string, the same way sendEmail returned a confirmation string
//     instead of actually sending mail.
//
// Example shape (delete this and write your own):
//   const postTweet = tool(
//     ({ content }) => `Tweet posted: ${JSON.stringify(content)}`,
//     {
//       name: "post_tweet",
//       description: "Post a tweet with the given content.",
//       schema: z.object({ content: z.string() }),
//     }
//   );
// ════════════════════════════════════════════════════════════════════════

const yourActionTool = tool(
  (_input: { argument: string }): string => {
    throw new Error("TODO 1: see the comment block above");
  },
  {
    name: "your_action_tool",
    description: "TODO 1: replace this description and body with your own action tool.",
    schema: z.object({ argument: z.string() }),
  }
);

// ════════════════════════════════════════════════════════════════════════
// TODO 2: Configure interruptOn for your tool, and write a system prompt
// plus an initial user request that would lead the model to propose
// calling it.
//
// Requirements:
//   - interruptOn should name your tool (rename your_action_tool if you
//     like) and an allowedDecisions list, e.g.
//     { your_action_tool: { allowedDecisions: ["approve", "edit", "reject"] } }
//   - SYSTEM_PROMPT should tell the agent when to use your tool.
//   - INITIAL_REQUEST should be a user message that would make the agent
//     want to call it.
// ════════════════════════════════════════════════════════════════════════

const SYSTEM_PROMPT = "TODO 2: replace this with your own system prompt.";
const INITIAL_REQUEST = "TODO 2: replace this with a request that would trigger your tool.";
const INTERRUPT_ON = { your_action_tool: true }; // TODO 2: replace with your own allowedDecisions config

if (yourActionTool.description.includes("TODO 1")) {
  throw new Error("TODO 1: see the comment block above");
}
if (SYSTEM_PROMPT.includes("TODO 2") || INITIAL_REQUEST.includes("TODO 2")) {
  throw new Error("TODO 2: see the comment block above");
}

const agent = createDeepAgent({
  model,
  tools: [yourActionTool],
  systemPrompt: SYSTEM_PROMPT,
  interruptOn: INTERRUPT_ON,
  checkpointer: new MemorySaver(),
});

const config = { configurable: { thread_id: "m1-8-homework-demo" } };

let result = await agent.invoke(
  { messages: [{ role: "user", content: INITIAL_REQUEST }] },
  config
);

const rl = createInterface({ input: process.stdin, output: process.stdout });

while (isInterrupted<ApprovalRequest>(result) && result[INTERRUPT].length) {
  const pending = result[INTERRUPT][0].value!;
  const decisions = [];

  for (const req of pending.actionRequests) {
    console.log(`\nApproval required for ${req.name}:`);
    console.log(req.args);

    const choice = (
      await rl.question("\nApprove, edit, or reject? (approve/edit/reject): ")
    )
      .trim()
      .toLowerCase();

    if (["approve", "yes", "y"].includes(choice)) {
      decisions.push({ type: "approve" });
    } else if (["edit", "e"].includes(choice)) {
      const editedArgs = { ...req.args };
      const key = Object.keys(editedArgs)[0];
      editedArgs[key] = await rl.question(`New value for '${key}': `);
      decisions.push({
        type: "edit",
        editedAction: { name: req.name, args: editedArgs },
      });
    } else {
      decisions.push({ type: "reject", message: "User rejected this action." });
    }
  }

  result = await agent.invoke(new Command({ resume: { decisions } }), config);
}

rl.close();
for (const msg of result.messages) {
  if (ToolMessage.isInstance(msg) && msg.name === "your_action_tool") {
    console.log(msg.content);
    break;
  }
}
