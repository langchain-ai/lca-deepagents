---
name: weekly-newsletter
description: "Produce the weekly 'This Week in Music' customer newsletter by researching the distributor's top genres in parallel and assembling a styled HTML page. Use when asked to create, write, or send the weekly newsletter or a music-news roundup."
---

# Weekly Newsletter

A parallel-research task. Coordinate; let the researchers do the digging.

## 1. Pick the genres

- If Jane named genres, use those. Otherwise ask **chinook-analyst** for the
  top 4 genres by revenue across the catalogue and feature those.

## 2. Research in parallel

- Use the code interpreter to get a timestamp for this run:
  `new Date().toISOString().slice(0, 19).replace(/[:.]/g, "-")` (e.g.
  `2026-07-30T14-23-05`). Reuse this same value in step 4. Using the full
  date-time (not just the date) keeps runs from colliding when this is run
  more than once in a day, e.g. during testing.
- For **each** genre, delegate to a **genre-researcher** subagent with the
  `task` tool — fire them all off together so they run in parallel.
- Tell each researcher its one genre and a private folder
  (`/research/<timestamp>/<genre>/`) for raw notes, using this run's
  timestamp. This keeps each run's scratch files separate so a subagent
  never finds leftover notes from a prior run. Ask for a single ~120–180
  word Markdown segment headed `## <Genre>`.
- Do **not** research genres yourself — your job is to assemble.

## 3. Assemble

- Collect the returned segments into one Markdown document:
  - `# This Week in Music` title
  - a one-sentence intro
  - the genre segments, in order

## 4. Render and save

- Call `markdown_to_html` on the assembled Markdown.
- `write_file` the returned HTML to `/outputs/newsletter-<timestamp>.html`,
  using the same timestamp from step 2.

## Done

Tell Jane where the newsletter was saved and list the genres covered.
