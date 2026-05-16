---
description: Summarize spending from the latest snapshot (or a given date). Shows monthly totals, top merchants, category breakdown, month-over-month delta, and per-person spend.
---

Analyze the latest transaction snapshot and produce a spending summary.

## Usage

- `/spending-summary` — use the most recent snapshot
- `/spending-summary 2026-04-01` — use the snapshot from that date

## Steps

1. Determine the snapshot directory:
   - If the user provided a date, use `~/Documents/financials/snapshots/<date>/`
   - Otherwise find the most recently dated folder in `~/Documents/financials/snapshots/`

2. Read all CSV files in that folder with the Bash tool.

3. Normalize amounts: outflows are negative, inflows are positive.

4. Produce a markdown report with these sections:

   **Monthly Totals** — total spend (sum of negative amounts, shown as positive) per calendar month in the snapshot

   **Top 10 Merchants** — ranked by absolute spend, descending, with total amount

   **Category Breakdown** — infer category from the description field using your judgment. Group totals by category.

   **Month-over-Month Delta** — % change in total spend between the two most recent complete months

   **By Person** — total spend per unique value in the `person` column; skip rows where person is null
