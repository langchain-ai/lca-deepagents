---
name: rfq-quote
description: "Process an incoming request for quote (RFQ) from a customer: read the email, look up the customer and catalogue prices, compute a quote, have it reviewed, draft the reply, and log it. Use whenever a customer asks for a price, a quote, or to license/buy a batch of tracks."
---

# Processing a Request for Quote

Follow these steps in order. Keep a todo list so Jane can see progress.

## 1. Read the request

- Ask **inbox-manager** to find the request and read it in full. Pull out: who
  is asking, their company/email, and exactly what they want (which
  genres/tracks, how many of each).

## 2. Identify the customer

- Ask **chinook-analyst** to find the customer by email (and name as a
  fallback).
- **If they are not in the system**, ask chinook-analyst to add them with
  `add_customer`. The system pauses automatically for Jane to approve — the
  analyst should just make the call, not ask in prose. Once approved, continue.

## 3. Get the prices

- Ask **chinook-analyst** for the unit prices needed:
  - For "N tracks in genre X": the count of available tracks and the standard
    `UnitPrice` for that genre (tracks are normally $0.99; verify, don't assume).
  - For "best-selling tracks": ask the analyst for the top sellers by quantity.
- Get real numbers from the database; never guess a price.

## 4. Compute the quote (exactly)

- Use the **code interpreter** to do the arithmetic — quantities × unit prices,
  any line discounts, and the total. Never hand-add money.
- A reasonable default volume discount: 10% off when the order is 50+ tracks.
  State the discount explicitly in the quote.

## 5. Have it reviewed

- Send the line items and totals to **quote-reviewer**. Apply its corrections
  before drafting.

## 6. Draft the reply

- Write a short, friendly reply from Jane: thank them, list each line
  (description, qty, unit price, line total), show any discount and the grand
  total, and offer next steps.
- Ask **inbox-manager** to save it as a draft to the sender, passing the
  subject and the full body. The system pauses automatically for Jane to
  approve or edit the wording before it's saved — don't ask for permission in a
  message first. Drafts are never auto-sent.

## 7. Log it

- Append one line to `/outputs/quotes_ledger.md` recording: date, customer,
  items summary, total, and the draft id. Create the file with a header row if
  it doesn't exist yet.

## Done

Tell Jane the draft is in her drafts folder and summarize the quote total.
