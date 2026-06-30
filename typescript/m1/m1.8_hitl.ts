import { createInterface } from "node:readline/promises";
import { tool } from "@langchain/core/tools";
import { z } from "zod";
import { MemorySaver } from "@langchain/langgraph";
import { Command } from "@langchain/langgraph";
import { createDeepAgent } from "deepagents";

import { model } from "../models.js";

const sendEmail = tool(
  ({ to, subject, body }) =>
    `Email sent to ${to} with subject ${JSON.stringify(subject)}. Body: ${body}`,
  {
    name: "send_email",
    description: "Send an email to a recipient.",
    schema: z.object({
      to: z.string(),
      subject: z.string(),
      body: z.string(),
    }),
  }
);

const SYSTEM_PROMPT = `You are a helpful assistant that can send emails.

Rules:
- Use send_email when the user asks you to send an email.
- Keep emails concise and professional.
- Do not claim an email was sent until the tool result confirms it.
`;

const agent = createDeepAgent({
  model,
  tools: [sendEmail],
  systemPrompt: SYSTEM_PROMPT,
  interruptOn: { send_email: true },
  checkpointer: new MemorySaver(),
});

const config = { configurable: { thread_id: "m1-8-hitl-demo" } };

let result = await agent.invoke(
  {
    messages: [
      {
        role: "user",
        content: "Send an email to jane@example.com saying I will be 10 minutes late.",
      },
    ],
  },
  config
);

const rl = createInterface({ input: process.stdin, output: process.stdout });

while ((result as any).__interrupt__?.length) {
  const pending = (result as any).__interrupt__[0].value;
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
      editedArgs.body = await rl.question("New email body: ");
      decisions.push({
        type: "edit",
        editedAction: { name: req.name, args: editedArgs },
      });
    } else {
      decisions.push({ type: "reject", message: "User rejected this email draft." });
    }
  }

  result = await agent.invoke(new Command({ resume: { decisions } }), config);
}

rl.close();
console.log(result.messages[result.messages.length - 1].content);
