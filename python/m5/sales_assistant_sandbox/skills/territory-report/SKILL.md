---
name: territory-report
description: "Build a report on the rep's sales territory — revenue, top customers, top genres, and trends for Jane's book of business — with a chart. Use when asked for a territory report, sales summary, performance numbers, or 'how is my book doing'."
---

# Territory Report

A metrics task. The numbers come from the database; the chart is rendered
from them.

## 1. Gather the metrics

Ask **chinook-analyst** for Jane's book of business (`SupportRepId = 3`):

- Total revenue and number of invoices.
- Top customers by revenue (with amounts).
- Revenue by genre (for Jane's customers).
- Any obvious trend (e.g. revenue by year, if useful).

Get exact figures; do the arithmetic with the **code interpreter** if you need
to combine results.

## 2. Write the report

- Use the code interpreter to get a timestamp:
  `new Date().toISOString().slice(0, 19).replace(/:/g, '-')` — this is
  date-and-time, not just the date, so a report requested again later the
  same day doesn't silently overwrite the earlier one.
- `write_file` a clear Markdown report to
  `/outputs/territory_report-<timestamp>.md`: headline totals, a
  top-customers list, and a revenue-by-genre table.

## 3. Chart

Write a short Python script with `write_file` that plots the revenue-by-genre
figures as a pie chart with matplotlib and saves it to
`/outputs/territory_chart-<timestamp>.png` (same timestamp as step 2), then
run it with `execute` (installing matplotlib first if it isn't already
available). Reference the image in the report.

## Done

Tell Jane where the report and chart were saved, with the headline revenue
number. Embed the chart in your reply itself as a Markdown image —
`![Revenue by Genre](/outputs/territory_chart-<timestamp>.png)` — using
that exact absolute path (the same timestamped filename from step 3), not
just mentioning the filename as text, so it renders inline in the chat
instead of only showing up as a download link.
