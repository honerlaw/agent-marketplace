---
description: Net cash flow view across all accounts (Truist, Amex, Citi) for the latest snapshot. Shows total inflow vs outflow, per-account breakdown, and 3-month trend.
---

Produce a cross-account cash flow summary.

## Usage

- `/cross-account` — use the most recent snapshot
- `/cross-account 2026-04-01` — use the snapshot from that date

## Steps

1. Determine the snapshot directory:
   - If the user provided a date, use `~/Documents/financials/snapshots/<date>/`
   - Otherwise find the most recently dated folder in `~/Documents/financials/snapshots/`

2. Read all CSV files in that folder. The `bank` column identifies which account each transaction belongs to.

3. Produce this report:

   **Total Inflow vs Outflow** — sum of all positive amounts (inflow) and absolute sum of all negative amounts (outflow) across all accounts. Net = inflow − outflow.

   **Per-Account Summary** — for each bank: total inflow, total outflow, net

   **Spend Distribution** — which account carries what % of total spend

   **3-Month Trend** — if the snapshot spans multiple months, show net cash flow per month as a simple table

4. Call out any notable patterns (e.g. a month where outflow significantly exceeds inflow, or one account dominating spend).
