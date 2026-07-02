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

- Use the code interpreter to get today's date (Python: `import datetime; datetime.date.today().isoformat()`).
- `write_file` a clear Markdown report to `/outputs/territory_report-<date>.md`:
  headline totals, a top-customers list, and a revenue-by-genre table.

## 3. Chart (optional)

- **If `retrieve_output` is available** (sandbox mode): use `execute_code` to
  generate a matplotlib pie chart of revenue by genre, save it to
  `/retrieve/territory_chart.png`, then call `retrieve_output` to copy it
  locally. Reference the image in the report.
- **Otherwise**, skip the image — the Markdown report is the deliverable.
  Note in the report that charting is not available in this environment.

## Done

Tell Jane where the report (and chart, if any) was saved, with the headline
revenue number.
