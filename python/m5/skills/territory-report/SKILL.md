---
name: territory-report
description: "Build a report on the rep's sales territory — revenue, top customers, top genres, and trends for Jane's book of business — with an optional chart. Use when asked for a territory report, sales summary, performance numbers, or 'how is my book doing'."
---

# Territory Report

A metrics task. The numbers always come from the database; the chart is
optional.

## 1. Gather the metrics

Ask **chinook-analyst** for Jane's book of business (`SupportRepId = 3`):

- Total revenue and number of invoices.
- Top customers by revenue (with amounts).
- Revenue by genre (for Jane's customers).
- Any obvious trend (e.g. revenue by year, if useful).

Get exact figures; do the arithmetic with the **code interpreter** if you need
to combine results.

## 2. Write the report

- `write_file` a clear Markdown report to `/outputs/territory_report.md`:
  headline totals, a top-customers list, and a revenue-by-genre table.

## 3. Chart (optional)

- **If the `render_chart` tool is available**, call it with the revenue-by-genre
  labels and values (a "pie" chart works well) and save it to
  `/outputs/territory_chart.png`. Reference the image in the report.
- **If `render_chart` is not available**, skip the image — the Markdown report
  with its numbers is the deliverable. Note in the report that charting is off.

## Done

Tell Jane where the report (and chart, if any) was saved, with the headline
revenue number.
