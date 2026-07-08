// typescript/m5/sales_assistant/tools/chart.ts
/**
 * Render a chart from structured data — no code execution required.
 *
 * A fixed-purpose tool instead of a code-execution sandbox: the model
 * supplies a title and two parallel lists (never code), so there is no
 * execution surface to secure in the first place.
 *
 * No charting library is available in this stack without adding a native or
 * network dependency, so the pie chart is a hand-rolled SVG: plain trig to
 * compute each wedge's arc path, no dependency, no execution surface.
 */
import { basename } from "node:path";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { tool } from "@langchain/core/tools";
import { z } from "zod";

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUTPUTS_DIR = join(__dirname, "..", "outputs");

const PALETTE = [
  "#4a86e8", "#e07798", "#44b984", "#ffad47", "#a479e2",
  "#f6c5be", "#149e60", "#cc3a21", "#6d9eeb", "#b694e8",
];

const SIZE = 480;
const CX = 210;
const CY = 240;
const RADIUS = 160;

function wedgePath(startAngle: number, endAngle: number): string {
  const x1 = CX + RADIUS * Math.cos(startAngle);
  const y1 = CY + RADIUS * Math.sin(startAngle);
  const x2 = CX + RADIUS * Math.cos(endAngle);
  const y2 = CY + RADIUS * Math.sin(endAngle);
  const largeArc = endAngle - startAngle > Math.PI ? 1 : 0;
  return `M ${CX},${CY} L ${x1.toFixed(2)},${y1.toFixed(2)} A ${RADIUS},${RADIUS} 0 ${largeArc} 1 ${x2.toFixed(2)},${y2.toFixed(2)} Z`;
}

function escapeXml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function renderSvg(title: string, labels: string[], values: number[]): string {
  const total = values.reduce((a, b) => a + b, 0);
  let angle = -Math.PI / 2;

  const wedges: string[] = [];
  const legend: string[] = [];

  labels.forEach((label, i) => {
    const value = values[i];
    const fraction = total > 0 ? value / total : 0;
    const nextAngle = angle + fraction * 2 * Math.PI;
    const color = PALETTE[i % PALETTE.length];

    wedges.push(`<path d="${wedgePath(angle, nextAngle)}" fill="${color}" stroke="#fff" stroke-width="1.5" />`);

    const pct = (fraction * 100).toFixed(0);
    const legendY = 50 + i * 22;
    legend.push(
      `<rect x="400" y="${legendY - 12}" width="14" height="14" fill="${color}" />` +
        `<text x="420" y="${legendY}" font-size="13" font-family="sans-serif" fill="#1a1a1a">${escapeXml(label)} (${pct}%)</text>`
    );

    angle = nextAngle;
  });

  return `<svg xmlns="http://www.w3.org/2000/svg" width="${SIZE + 260}" height="${SIZE}" viewBox="0 0 ${SIZE + 260} ${SIZE}">
<rect width="100%" height="100%" fill="#ffffff" />
<text x="${SIZE / 2 + 130}" y="30" text-anchor="middle" font-size="18" font-family="sans-serif" font-weight="bold" fill="#1a1a1a">${escapeXml(title)}</text>
${wedges.join("\n")}
${legend.join("\n")}
</svg>`;
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
    // outside outputs/, and force the .svg extension this tool produces.
    const base = basename(filename).replace(/\.[^./]+$/, "");
    if (!base) {
      return "Error: filename must not be empty.";
    }
    const safeName = `${base}.svg`;

    const svg = renderSvg(title, labels, values);

    mkdirSync(OUTPUTS_DIR, { recursive: true });
    writeFileSync(join(OUTPUTS_DIR, safeName), svg, "utf-8");

    return `Saved to outputs/${safeName}`;
  },
  {
    name: "render_pie_chart",
    description:
      "Render a labeled pie chart and save it as an SVG in outputs/. " +
      "Args: title (chart title), labels (one per slice, e.g. genre names), " +
      "values (one numeric value per label, same length as labels), " +
      "filename (e.g. \"territory_chart.svg\" — any directory components are " +
      "stripped and the extension is forced to .svg; the file is always " +
      "saved into outputs/).",
    schema: z.object({
      title: z.string(),
      labels: z.array(z.string()),
      values: z.array(z.number()),
      filename: z.string(),
    }),
  }
);
