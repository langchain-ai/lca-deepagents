import { input, select } from "@inquirer/prompts";
import { z } from "zod";

import { tool, ToolMessage, type Decision } from "langchain";
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

const askUser = tool(
  ({ question }) => `[No response recorded for: ${question}]`,
  {
    name: "ask_user",
    description: "Ask the user a clarifying question with a fixed set of choices.",
    schema: z.object({
      question: z.string(),
      choices: z.array(z.string()),
    }),
  }
);

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
- If the user's request depends on a choice only they can make, call ask_user
  with the question and the list of choices before drafting anything.
- Use the ask_user response to decide what the email should say.
- Use send_email when you are ready to send.
- Keep emails concise and professional.
- Do not claim an email was sent until the tool result confirms it.
- When confirming an email was sent, quote the subject and body from the tool result, not the original request.
`;

const agent = createDeepAgent({
  model,
  tools: [askUser, sendEmail],
  systemPrompt: SYSTEM_PROMPT,
  interruptOn: {
    ask_user: { allowedDecisions: ["respond"] },
    send_email: { allowedDecisions: ["approve", "edit", "reject"] },
  },
  checkpointer: new MemorySaver(),
});

const config = { configurable: { thread_id: "m1-8-hitl-respond-demo" } };

let result = await agent.invoke(
  {
    messages: [
      {
        role: "user",
        content:
          "Email professor.weng@university.edu that I'll be late, but first " +
          "check whether I should just apologize or ask for a short extension.",
      },
    ],
  },
  config
);

while (isInterrupted<ApprovalRequest>(result) && result[INTERRUPT].length) {
  const pending = result[INTERRUPT][0].value!;
  const decisions: Decision[] = [];

  for (const req of pending.actionRequests) {
    if (req.name === "ask_user") {
      const { question, choices } = req.args as { question: string; choices: string[] };
      const selected = await select({
        message: question,
        choices: choices.map((choice) => ({ name: choice, value: choice })),
      });
      decisions.push({ type: "respond", message: selected });
    } else if (req.name === "send_email") {
      console.log(`\nApproval required for ${req.name}:`);
      console.log(req.args);

      const action = await select({
        message: "How do you want to handle this email?",
        choices: ["approve", "edit", "reject"].map((choice) => ({ name: choice, value: choice })),
      });

      if (action === "approve") {
        decisions.push({ type: "approve" });
      } else if (action === "edit") {
        const editedArgs = { ...req.args };
        editedArgs.body = await input({ message: "New email body:" });
        decisions.push({
          type: "edit",
          editedAction: { name: req.name, args: editedArgs },
        });
      } else {
        decisions.push({ type: "reject", message: "User rejected this email draft." });
      }
    }
  }

  result = await agent.invoke(new Command({ resume: { decisions } }), config);
}

for (const msg of result.messages) {
  if (ToolMessage.isInstance(msg) && msg.name === "send_email") {
    console.log(msg.text);
    break;
  }
}
