// typescript/m1/Practice/judge_card_helpers.ts
/**
 * Provided setup for judge_card_practice.ts: the quiz, the ASCII card
 * renderer, persona styling, the "publish" tool, and the invoke/interrupt-
 * resume loop.
 *
 * Nothing in here is a TODO. Read renderResultCard()'s docstring if you
 * want to restyle a card, otherwise you shouldn't need to open this file.
 */

import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { createInterface } from "node:readline/promises";

import { z } from "zod";
import { select } from "@inquirer/prompts";
import { context, tool } from "langchain";
import { Command, INTERRUPT, isInterrupted, MemorySaver } from "@langchain/langgraph";
import { createDeepAgent } from "deepagents";

// Params accepted by createDeepAgent, extracted so runJudge can forward
// model/tools/interruptOn through with the exact same types deepagents expects.
type CreateDeepAgentParams = NonNullable<Parameters<typeof createDeepAgent>[0]>;

const __dirname = dirname(fileURLToPath(import.meta.url));
export const OUTPUT_DIR = join(__dirname, "output");
mkdirSync(OUTPUT_DIR, { recursive: true });

// A trait-axis delta: (chaotic/organized, cautious/bold, solo/collaborative).
export type TraitDelta = [number, number, number];

// Shared tool-calling steps appended to every persona in JUDGE_PERSONAS, so
// each persona string only needs to define its voice, not repeat the
// mechanics.
export const TOOL_SEQUENCE = context`
  This is a single-shot judgment call: you will not get a reply if you ask a
  question, and refusing or asking for more information is not an option.
  Always call the matched product by the exact name score_and_match
  returned (e.g. "Fleet"); never an older or alternate name for it (e.g.
  "Agent Builder"), even if you recall one from your own knowledge. Never
  use an em dash (—) or a hyphen used as a standalone connector (" - ")
  anywhere in your verdict or caption text. Use only a comma, a period, a
  colon, or a semicolon to join clauses instead.
  These steps are a strict dependency chain, not independent work you can
  parallelize: each one needs the previous one's actual result (the fact,
  the trait_scores, the render_card success) before it can run. Call
  exactly one of these tools per turn and wait for its result before
  calling the next one; never call two of them in the same response, even
  if you're confident you already know what the next call's arguments
  will be.
  1. Call score_and_match with the quiz answers list you were given, exactly
     as given.
  2. Call fetch_product_fact with the product name score_and_match returned.
  3. Decide a "builder (developer) type" headline and a one-line verdict in
     your voice, using the trait_scores and the fact you just got. Open the
     verdict by naming the matched product directly (e.g. "Fleet is your
     match" or, in a pirate's voice, "Ye've earned Fleet, matey"), then
     explain why in one clause grounded in the fact you fetched; don't
     bury the product in a dependent clause at the end.
  4. Call render_card with your builder_type, your judge_name, your verdict,
     the trait_scores, and the product.
  5. Once that succeeds, call post_card with a one-line caption. Unlike
     your verdict, write this one in plain, casual, polished modern
     English, not your persona's voice, the way you'd actually post it
     yourself. It should read like a real completion announcement: you
     just finished Module 1 of LangChain's Deep Agents course, built this
     practice exercise, and got named your builder_type. Name the product
     score_and_match matched you with explicitly and plainly (e.g.
     "assigned: Fleet"), then give one concrete reason it fits, not a
     vague invented tagline about what the product does. E.g. "Just
     finished Module 1 of LangChain's Deep Agents course and built a quiz
     that judges your dev habits. Got named The Pragmatic Orchestrator and
     assigned Fleet, no-code agents with built-in approvals. Feels about
     right."
`;

export const RESET = "[0m";
export const BOLD = "[1m";
export const DEFAULT_COLOR = "[92m"; // bright green (unstyled personas, e.g. your own)

export const DEFAULT_MASCOT = [" ___", "[o_o]", "/|_|\\", " | |"].join("\n");

// The 3 fixed personality axes the quiz scores you on. Each trait score
// (0-100, from scoreAndMatch in judge_card_practice.ts) says how far
// toward the *right* label you land.
export const TRAIT_AXES: Array<[string, string]> = [
  ["Chaotic", "Organized"],
  ["Cautious", "Bold"],
  ["Solo", "Collaborative"],
];

interface QuizQuestion {
  question: string;
  // Each choice is a (label, delta) tuple, mirroring the Python
  // list[tuple[str, tuple[int, int, int]]] shape.
  choices: Array<[string, TraitDelta]>;
}

// 8 fixed quiz questions. Each choice carries a (chaotic/organized,
// cautious/bold, solo/collaborative) delta applied to a running score that
// starts at 50 per axis.
export const QUIZ_QUESTIONS: QuizQuestion[] = [
  {
    question: "It's 9am, you have 3 unread pings and one big task due today.",
    choices: [
      ["Reply to all three immediately, big task can wait", [-2, 0, 2]],
      ["Silence notifications, focus on the big task first", [2, 0, -2]],
      ["Skim them, answer only the urgent one, then dive in", [0, 1, 0]],
    ],
  },
  {
    question: "You find a bug in code you didn't write. It's not blocking you.",
    choices: [
      ["Fix it immediately, mid-task", [-1, 2, 0]],
      ["File a ticket, get back to what you were doing", [1, -1, 1]],
      ["Leave a comment, let the original author decide", [0, -2, 1]],
    ],
  },
  {
    question: "Your project's plan just changed with zero warning.",
    choices: [
      ["Thrilling. Let's improvise.", [-2, 1, 0]],
      ["Panic quietly, then rebuild the plan from scratch.", [2, -1, 0]],
      ["Ask the team what changed and why before reacting.", [0, 0, 2]],
    ],
  },
  {
    question: "How do you feel about shipping code you haven't fully tested?",
    choices: [
      ["Ship it, fix forward.", [-1, 2, 0]],
      ["Absolutely not, I need to be sure.", [1, -2, 0]],
      ["Depends who's watching the deploy.", [0, 0, 1]],
    ],
  },
  {
    question: "Pick your ideal work session:",
    choices: [
      ["Solo, headphones on, no meetings.", [0, 0, -2]],
      ["Pair programming, thinking out loud with someone.", [0, 0, 2]],
      ["Whiteboarding with the whole team.", [-1, 1, 2]],
    ],
  },
  {
    question: "Someone asks you to review their PR right now.",
    choices: [
      ["Sure, dropping what I'm doing to look now.", [0, -1, 2]],
      ["I'll finish my current task first, then review.", [1, 0, 0]],
      ["Skim it fast, leave a couple comments, move on.", [-1, 0, 1]],
    ],
  },
  {
    question: "Your build just failed in CI. What's your first move?",
    choices: [
      ["Re-run it, probably flaky.", [-1, 1, 0]],
      ["Read the full log before touching anything.", [1, -1, 0]],
      ["Ping whoever touched that file last.", [0, 0, 2]],
    ],
  },
  {
    question: "How do you feel about writing documentation?",
    choices: [
      ["Write it as I go, future me will thank me.", [1, -1, 0]],
      ["I'll write it eventually. Probably.", [-2, 1, -1]],
      ["Only if someone else is going to read it soon.", [0, 0, 1]],
    ],
  },
];

// One real LangChain product per axis-leaning direction, keyed lowercase.
// (See https://docs.langchain.com for the full product lineup.) This
// lookup is what decides which product you get; TODO 3's MCP call only
// describes whichever product this table already picked, it doesn't
// choose it.
export const PRODUCT_MATCHES: Record<string, string> = {
  chaotic: "Fleet",
  organized: "Evaluation",
  cautious: "Observability",
  bold: "Engine",
  solo: "Sandboxes",
  collaborative: "Deployment",
};

/** Ask the 8 fixed quiz questions with arrow-key selection and return the
 * chosen (chaotic/organized, cautious/bold, solo/collaborative) delta for
 * each answer, in order. */
export async function runQuiz(): Promise<TraitDelta[]> {
  const answers: TraitDelta[] = [];
  for (const q of QUIZ_QUESTIONS) {
    const picked = await select({
      message: q.question,
      choices: q.choices.map(([label]) => ({ name: label, value: label })),
    });
    const [, deltas] = q.choices.find(([label]) => label === picked)!;
    answers.push(deltas);
  }
  return answers;
}

/** Word-wrap text to at most `width` characters per line, breaking on
 * spaces (no textwrap module in Node, so a small local helper instead of a
 * new dependency). */
function wrapText(text: string, width: number): string[] {
  const words = text.split(/\s+/).filter((w) => w.length > 0);
  const lines: string[] = [];
  let current = "";
  for (const word of words) {
    if (current.length === 0) {
      current = word;
    } else if (current.length + 1 + word.length <= width) {
      current += ` ${word}`;
    } else {
      lines.push(current);
      current = word;
    }
  }
  if (current.length > 0) lines.push(current);
  return lines;
}

/** Python str.center() equivalent: pads both sides to `width`, extra
 * padding (when the gap is odd) goes on the right, same as CPython. */
function center(text: string, width: number): string {
  if (text.length >= width) return text;
  const totalPad = width - text.length;
  const left = Math.floor(totalPad / 2);
  const right = totalPad - left;
  return " ".repeat(left) + text + " ".repeat(right);
}

/**
 * Print a colorized ASCII result card to the terminal and return the plain
 * (no-ANSI-codes) text so the caller can also save it to a file.
 *
 * meters: up to 3 [leftLabel, rightLabel, score0to100] tuples, where the
 * score is how far toward the *right* label the result sits.
 *
 * mascot/color: optional per-persona styling (see PERSONA_STYLES).
 */
export function renderResultCard(
  builderType: string,
  meters: Array<[string, string, number]>,
  verdict: string,
  judgeName: string,
  mascot: string = DEFAULT_MASCOT,
  color: string = DEFAULT_COLOR
): string {
  const margin = "  ";
  const width = Math.max(builderType.length + 4, 24);
  const titleTop = `${margin}┌${"─".repeat(width)}┐`;
  const titleMid = `${margin}│${center(builderType.toUpperCase(), width)}│`;
  const titleBot = `${margin}└${"─".repeat(width)}┘`;
  const boxWidth = width + 2;

  const mascotLines = mascot.split("\n");
  const artWidth = Math.max(...mascotLines.map((line) => line.length));
  const leftPad = margin + " ".repeat(Math.max(Math.floor((boxWidth - artWidth) / 2), 0));
  const mascotBlock = mascotLines.map((line) => leftPad + line).join("\n");

  const barWidth = 14;
  const trimmedMeters = meters.slice(0, 3);
  const labelWidth = trimmedMeters.length
    ? Math.max(...trimmedMeters.map(([left]) => left.length))
    : 0;
  const barLines: string[] = [];
  for (const [left, right, rawScore] of trimmedMeters) {
    const score = Math.max(0, Math.min(100, rawScore));
    const filled = Math.round((barWidth * score) / 100);
    const bar = "█".repeat(filled) + "░".repeat(barWidth - filled);
    barLines.push(`  ${left.padEnd(labelWidth)} [${bar}] ${right}`);
  }

  const sepWidth = barLines.length ? Math.max(...barLines.map((line) => line.length)) - 2 : 2;
  const separator = `  ${"─".repeat(sepWidth)}`;
  const barBlock: string[] = [];
  barLines.forEach((line, i) => {
    barBlock.push(line);
    if (i < barLines.length - 1) barBlock.push(separator);
  });

  const cleanedVerdict = verdict.replace(/\s*—\s*/g, ", ");
  const wrapped = wrapText(cleanedVerdict, 44);
  if (wrapped.length === 0) wrapped.push("");
  wrapped[0] = `"${wrapped[0]}`;
  wrapped[wrapped.length - 1] = `${wrapped[wrapped.length - 1]}"`;
  const verdictLines = wrapped.map((line) => `  ${line}`);

  const plainLines = [
    "",
    mascotBlock,
    "",
    titleTop,
    titleMid,
    titleBot,
    "",
    ...barBlock,
    "",
    ...verdictLines,
    "",
    `  judged by ${judgeName}`,
  ];

  const highlighted = new Set([titleTop, titleMid, titleBot, ...barLines]);
  for (const line of plainLines) {
    if (line === mascotBlock || highlighted.has(line)) {
      console.log(`${color}${BOLD}${line}${RESET}`);
    } else {
      console.log(line);
    }
  }

  return plainLines.join("\n");
}

interface PersonaStyle {
  mascot?: string;
  color?: string;
}

// Optional per-persona styling passed through to renderResultCard, keyed by
// judgeName (the name the persona calls itself, e.g. "Nefer-Ka") since
// that's what renderCard receives, not the JUDGE_PERSONAS dict key. Any
// persona not listed here just gets the default look (default mascot,
// green bars). Add an entry for your own persona if you want a distinct
// theme: PERSONA_STYLES["your_persona_name"] = {...}.
export const PERSONA_STYLES: Record<string, PersonaStyle> = {
  "Captain Hardcode": {
    mascot: [
      "                  ______",
      '               .-"      "-.',
      "              /            \\",
      "  _          |              |          _",
      " ( \\         |,  .-.  .-.  ,|         / )",
      '  > "=._     | )(__/  \\__)( |     _.=" <',
      ' (_/"=._"=._ |/     /\\     \\| _.="_.="\\_)',
      '        "=._"(_     ^^     _)"_.="',
      '            "=\\__|IIIIII|__/="',
      '           _.="| \\IIIIII/ |"=._',
      ' _     _.="_.="\\          /"=._"=._     _',
      '( \\_.="_.="     `--------`     "=._"=._/ )',
      ' > _.="                            "=._ <',
      "(_/                                    \\_)",
    ].join("\n"),
    color: "[95m", // bright magenta/purple
  },
  "Nefer-Ka": {
    mascot: [
      "     .--.",
      "    | = o\\",
      "    \\= =_/",
      "     )= \\____",
      "    ; = _|__-\\",
      "    |= ----.\\",
      "    ('.==|",
      "   / \\=\\=\\",
      "_.'  /=/\\=\\_",
      "    /__) \\__)",
    ].join("\n"),
    color: "[93m", // bright yellow/gold
  },
  Vex: {
    mascot: [
      "  ///-\\\\\\",
      "  |-   ^|",
      "  |-   -|",
      "  |  ~ *scoff*",
      "   \\ O /",
      "    | |",
    ].join("\n"),
    color: "[91m", // bright red
  },
};

export const PLATFORM = "X";
export const HANDLE = "@you";

export const POSTED_BANNER = [
  "                                    ░██                      ░██",
  "                                    ░██                      ░██",
  "░████████   ░███████   ░███████  ░████████  ░███████   ░████████",
  "░██    ░██ ░██    ░██ ░██           ░██    ░██    ░██ ░██    ░██",
  "░██    ░██ ░██    ░██  ░███████     ░██    ░█████████ ░██    ░██",
  "░███   ░██ ░██    ░██        ░██    ░██    ░██        ░██   ░███",
  "░██░█████   ░███████   ░███████      ░████  ░███████   ░█████░██",
  "░██",
  "░██",
];

/**
 * Print a small X-styled mock post card: a "Draft" preview (shown at the
 * HITL approval prompt, before you've decided, with the caption text
 * inside) or a "Posted" confirmation (shown after postCard actually runs,
 * with a big "posted" banner instead of repeating the same caption).
 * Returns the plain text too.
 */
export function renderMockPost(caption: string, posted: boolean): string {
  const cleanedCaption = caption.replace(/\s*—\s*/g, ", ");
  let width: number;
  let body: string[];
  if (posted) {
    const bannerWidth = Math.max(...POSTED_BANNER.map((line) => line.length));
    width = bannerWidth + 4;
    const pad = " ".repeat(Math.floor((width - bannerWidth) / 2));
    body = POSTED_BANNER.map((line) => `│${pad}${line.padEnd(bannerWidth)}${pad}│`);
  } else {
    width = 46;
    const wrapped = wrapText(cleanedCaption, width - 2);
    if (wrapped.length === 0) wrapped.push("");
    body = [
      ...wrapped.map((line) => `${`│ ${line}`.padEnd(width + 1)}│`),
      `│${"".padEnd(width)}│`,
      `│${"  ♡ 0    ↻ 0    ⤴ share".padEnd(width)}│`,
    ];
  }
  const lines = [
    `┌${"─".repeat(width)}┐`,
    `│${` ${HANDLE} on ${PLATFORM}`.padEnd(width)}│`,
    `│${"".padEnd(width)}│`,
    ...body,
    `└${"─".repeat(width)}┘`,
    posted ? "  ● Posted" : "  ○ Draft, awaiting your approval",
  ];
  const text = lines.join("\n");
  console.log(text);
  return text;
}

export const renderCard = tool(
  ({
    builderType,
    judgeName,
    verdict,
    traitScores,
    product,
  }: {
    builderType: string;
    judgeName: string;
    verdict: string;
    traitScores: number[];
    product: string;
  }) => {
    const meters: Array<[string, string, number]> = TRAIT_AXES.map(([left, right], i) => [
      left,
      right,
      traitScores[i],
    ]);
    const style = PERSONA_STYLES[judgeName] ?? {};
    const cardText = renderResultCard(builderType, meters, verdict, judgeName, style.mascot, style.color);
    const safeType = builderType
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/^_+|_+$/g, "");
    const safeJudge = judgeName
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/^_+|_+$/g, "");
    const outPath = join(OUTPUT_DIR, `${safeJudge}_${safeType}.txt`);
    writeFileSync(outPath, `${cardText}\n\n  matched product: ${product}\n`);
    return `Card printed above and saved to ${outPath}. Matched LangChain product: ${product}.`;
  },
  {
    name: "render_card",
    description:
      "Render and save the finished result card. Call this only after score_and_match has given you traitScores and a matched product, and you've decided on a builderType headline and a one-line verdict.",
    schema: z.object({
      builderType: z.string(),
      judgeName: z.string(),
      verdict: z.string(),
      traitScores: z.array(z.number()),
      product: z.string(),
    }),
  }
);

export const postCard = tool(
  ({ caption }: { caption: string }) => {
    renderMockPost(caption, true);
    console.log(
      "\n  * Reminder: that's a mock post, nothing left this terminal. " +
        "Screenshot your real card and share it on X or LinkedIn, tag " +
        "@LangChain, if you want it to count for real!"
    );
    return `Posted with caption: ${JSON.stringify(caption)}`;
  },
  {
    name: "post_card",
    description:
      "Publish the finished result card as a mock post on X. Nothing ever leaves this terminal. Only call this after render_card has produced the card.",
    schema: z.object({ caption: z.string() }),
  }
);

interface ActionRequest {
  name: string;
  args: Record<string, unknown>;
}

interface ApprovalRequest {
  actionRequests: ActionRequest[];
}

export interface RunJudgeOptions {
  systemPrompt: string;
  userPrompt: string;
  tools: CreateDeepAgentParams["tools"];
  model: CreateDeepAgentParams["model"];
  interruptOn?: CreateDeepAgentParams["interruptOn"];
  threadPrefix?: string;
}

/** Build the agent for one judge persona, run the quiz, and walk through
 * any human-in-the-loop approval prompts until it's done. */
export async function runJudge(judgeName: string, options: RunJudgeOptions): Promise<void> {
  const { systemPrompt, userPrompt, tools, model, interruptOn, threadPrefix = "m1-practice" } = options;

  const agent = createDeepAgent({
    model,
    tools,
    systemPrompt,
    interruptOn,
    checkpointer: new MemorySaver(),
  });
  const config = { configurable: { thread_id: `${threadPrefix}-${judgeName}` } };

  let result = await agent.invoke({ messages: [{ role: "user", content: userPrompt }] }, config);

  const rl = createInterface({ input: process.stdin, output: process.stdout });
  try {
    while (isInterrupted<ApprovalRequest>(result) && result[INTERRUPT].length) {
      const pending = result[INTERRUPT][0].value!;
      const decisions = [];

      for (const req of pending.actionRequests) {
        console.log(`\n[${judgeName}] approval required for ${req.name}:`);
        if (req.name === "post_card") {
          renderMockPost(String(req.args.caption ?? ""), false);
        } else {
          for (const [key, value] of Object.entries(req.args)) {
            if (typeof value === "string") {
              const wrapped = wrapText(value, 44);
              const indent = " ".repeat(key.length + 4);
              console.log(`  ${key}: ${wrapped[0] ?? ""}`);
              for (const line of wrapped.slice(1)) {
                console.log(`${indent}${line}`);
              }
            } else {
              console.log(`  ${key}: ${value}`);
            }
          }
        }

        for (;;) {
          const choice = (await rl.question("Approve, edit, or reject? (approve/edit/reject): "))
            .trim()
            .toLowerCase();
          if (["approve", "accept", "yes", "y"].includes(choice)) {
            decisions.push({ type: "approve" });
            break;
          } else if (["edit", "e"].includes(choice)) {
            const editedArgs: Record<string, unknown> = { ...req.args };
            editedArgs.caption = await rl.question("New caption: ");
            decisions.push({ type: "edit", editedAction: { name: req.name, args: editedArgs } });
            break;
          } else if (["reject", "r", "no", "n"].includes(choice)) {
            decisions.push({ type: "reject", message: "User rejected this card before it posted." });
            break;
          } else {
            console.log("  Please type approve, edit, or reject.");
          }
        }
      }

      result = await agent.invoke(new Command({ resume: { decisions } }), config);
    }
  } finally {
    rl.close();
  }
}
