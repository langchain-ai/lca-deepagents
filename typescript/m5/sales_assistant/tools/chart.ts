// typescript/m5/sales_assistant/tools/chart.ts
/**
 * Render a chart from structured data — no code execution required.
 *
 * A fixed-purpose tool instead of a code-execution sandbox: the model
 * supplies a title and two parallel lists (never code), so there is no
 * execution surface to secure in the first place.
 *
 * Drawn with node-canvas (the Node port of the HTML5 Canvas API) and
 * exported straight to PNG, mirroring how the Python version rasterizes
 * with matplotlib — no SVG intermediary.
 */
import { basename } from "node:path";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { createCanvas } from "canvas";
import { z } from "zod";
import { context, tool } from "langchain";

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUTPUTS_DIR = join(__dirname, "..", "outputs");

const PALETTE = [
  "#4a86e8", "#e07798", "#44b984", "#ffad47", "#a479e2",
  "#f6c5be", "#149e60", "#cc3a21", "#6d9eeb", "#b694e8",
];

const WIDTH = 740;
const HEIGHT = 480;
const CX = 210;
const CY = 240;
const RADIUS = 160;

function renderPng(title: string, labels: string[], values: number[]): Buffer {
  const canvas = createCanvas(WIDTH, HEIGHT);
  const ctx = canvas.getContext("2d");

  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, WIDTH, HEIGHT);

  ctx.fillStyle = "#1a1a1a";
  ctx.font = "bold 18px sans-serif";
  ctx.textAlign = "center";
  ctx.fillText(title, WIDTH / 2 - 130, 30);

  const total = values.reduce((a, b) => a + b, 0);
  let angle = -Math.PI / 2;

  labels.forEach((label, i) => {
    const value = values[i];
    const fraction = total > 0 ? value / total : 0;
    const nextAngle = angle + fraction * 2 * Math.PI;
    const color = PALETTE[i % PALETTE.length];

    ctx.beginPath();
    ctx.moveTo(CX, CY);
    ctx.arc(CX, CY, RADIUS, angle, nextAngle);
    ctx.closePath();
    ctx.fillStyle = color;
    ctx.fill();
    ctx.strokeStyle = "#ffffff";
    ctx.lineWidth = 1.5;
    ctx.stroke();

    const pct = (fraction * 100).toFixed(0);
    const legendY = 50 + i * 22;
    ctx.fillStyle = color;
    ctx.fillRect(400, legendY - 12, 14, 14);
    ctx.fillStyle = "#1a1a1a";
    ctx.font = "13px sans-serif";
    ctx.textAlign = "left";
    ctx.fillText(`${label} (${pct}%)`, 420, legendY);

    angle = nextAngle;
  });

  return canvas.toBuffer("image/png");
}

export const renderPieChart = tool(
  ({
    title,
    labels,
    values,
    filename,
  }: {
    title: string;
    labels: string[];
    values: number[];
    filename: string;
  }) => {
    if (labels.length !== values.length) {
      return "Error: labels and values must be the same length.";
    }

    // Strip any directory components so a crafted filename can't write
    // outside outputs/, and force the .png extension this tool produces.
    const base = basename(filename).replace(/\.[^./]+$/, "");
    if (!base) {
      return "Error: filename must not be empty.";
    }
    const safeName = `${base}.png`;

    const png = renderPng(title, labels, values);

    mkdirSync(OUTPUTS_DIR, { recursive: true });
    writeFileSync(join(OUTPUTS_DIR, safeName), png);

    return `Saved to outputs/${safeName}`;
  },
  {
    name: "render_pie_chart",
    description: context`
      Render a labeled pie chart and save it as a PNG in outputs/.
      Args: title (chart title), labels (one per slice, e.g. genre names),
      values (one numeric value per label, same length as labels),
      filename (e.g. "territory_chart.png" — any directory components are
      stripped and the extension is forced to .png; the file is always
      saved into outputs/).`,
    schema: z.object({
      title: z.string(),
      labels: z.array(z.string()),
      values: z.array(z.number()),
      filename: z.string(),
    }),
  }
);
