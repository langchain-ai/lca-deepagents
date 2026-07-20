---
name: weekly-newsletter
description: "Produce the weekly 'This Week in Music' customer newsletter by researching the distributor's top genres and assembling a styled HTML page. Use when asked to create, write, or send the weekly newsletter or a music-news roundup."
---

# Weekly Newsletter

A background job. Launch it, then get out of the way — newsletter-agent
researches every genre and assembles the finished HTML itself.

## 1. Pick the genres

- If Jane named genres, use those. Otherwise ask **chinook-analyst** for the
  top 4 genres by revenue across the catalogue and feature those.

## 2. Launch in the background

- Call `start_async_task(subagent_type="newsletter-agent", description=...)`
  **once**, with the genre list in `description` (e.g. "Research and
  assemble this week's newsletter for these genres: Rock, Latin, Jazz,
  Classical"). It returns a task ID immediately; it does not block.
- Tell Jane the newsletter is being put together in the background, then
  **stop**. Do not poll — newsletter-agent notifies you when it's done.
- Do **not** research genres or assemble the newsletter yourself — that's
  entirely newsletter-agent's job.

## 3. When woken by a completion notification (or asked for a status check)

- Get the task_id: call `list_async_tasks()` and read the `task_id:` field for
  the newsletter-agent entry. Don't rely on the task_id from earlier in the
  conversation — it may have scrolled out of context or been summarized away;
  `list_async_tasks` reads it from durable state, not memory.
- Call `check_async_task(task_id)`.
- If `status` isn't terminal yet (`success` or `error`), report progress to
  Jane and stop — you'll be woken again when it finishes.
- If `status` is `error`, tell Jane the newsletter couldn't be put together
  this week and stop — there's no HTML to save.
- If `status` is `success`, `result` is the finished HTML, verbatim — no
  markdown conversion needed here, newsletter-agent already did that.
  Continue to step 4 immediately, in the same turn — don't ask Jane for
  permission first. She already asked for the newsletter back in step 1; a
  completed background job isn't a new decision that needs re-confirming.

## 4. Save (once)

- You can be woken more than once for the same task_id (e.g. Jane asks "is
  it ready?" again after you already saved it) — don't save a duplicate
  file. Check deterministically, not from conversation memory (which can be
  summarized away): call `glob("/outputs/newsletter-*-<task_id, first 8
  chars>.html")`. If that already matches a file, tell Jane it's already
  saved at that path and stop.
- Otherwise, use the code interpreter to get a timestamp:
  `new Date().toISOString().slice(0, 19).replace(/:/g, '-')` — this is
  date-and-time, not just the date, so a genuinely new newsletter request
  later the same day produces a new file instead of overwriting the last
  one.
- `write_file` the HTML from step 3 **exactly as returned** — no edits, no
  added commentary — to
  `/outputs/newsletter-<timestamp>-<task_id, first 8 chars>.html`.

## Done

Tell Jane where the newsletter was saved. If the HTML you just saved
mentions a genre that didn't make it in (newsletter-agent notes this itself
when a genre's research fails), pass that along in your own words.
