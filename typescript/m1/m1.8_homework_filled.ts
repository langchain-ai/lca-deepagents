// typescript/m1/m1.8_homework_filled.ts
/**
 * Reference copy of m1.8_homework.ts with TODOs 1 and 2 filled in so you
 * can run it end to end and see what "done" looks like. This is just one
 * possible answer, so yours might be different. Explore!
 */

import { createInterface } from "node:readline/promises";
import { z } from "zod";

import { tool, ToolMessage, type InterruptOnConfig } from "langchain";
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

// TODO 1 filled in
const postTweet = tool(
  ({ content }: { content: string }) => `Tweet posted: ${JSON.stringify(content)}`,
  {
    name: "post_tweet",
    description: "Post a tweet with the given content.",
    schema: z.object({ content: z.string() }),
  }
);

// TODO 2 filled in
const SYSTEM_PROMPT = `You are a social media assistant that drafts and posts tweets.

Rules:
- Use post_tweet when the user asks you to post something.
- Keep tweets under 280 characters and upbeat in tone.
- Do not claim a tweet was posted until the tool result confirms it.
`;
const INITIAL_REQUEST = "Post a tweet announcing that our new product launches this Friday.";
const INTERRUPT_ON = {
  post_tweet: { allowedDecisions: ["approve", "edit", "reject"] },
} satisfies Record<string, boolean | InterruptOnConfig>;

const agent = createDeepAgent({
  model,
  tools: [postTweet],
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
      editedArgs.content = await rl.question("New tweet content: ");
      decisions.push({
        type: "edit",
        editedAction: { name: req.name, args: editedArgs },
      });
    } else {
      decisions.push({ type: "reject", message: "User rejected this tweet draft." });
    }
  }

  result = await agent.invoke(new Command({ resume: { decisions } }), config);
}

rl.close();
for (const msg of result.messages) {
  if (ToolMessage.isInstance(msg) && msg.name === "post_tweet") {
    console.log(msg.content);
    break;
  }
}
