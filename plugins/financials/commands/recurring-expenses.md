---
description: Identify recurring transactions — bills, subscriptions, and regular transfers — from the latest snapshot. Shows estimated monthly recurring total.
---

Scan transaction history for recurring charges.

## Usage

- `/recurring-expenses` — use the most recent snapshot
- `/recurring-expenses 2026-04-01` — use the snapshot from that date

## Steps

1. Determine the snapshot directory:
   - If the user provided a date, use `~/Documents/financials/snapshots/<date>/`
   - Otherwise find the most recently dated folder in `~/Documents/financials/snapshots/`

2. Read all CSV files in that folder.

3. Identify recurring transactions: same merchant (or very similar description) appearing in 2+ different calendar months with a similar amount (within 10%).

4. Group into three buckets:

   **Bills** — utilities, insurance, mortgage/rent, phone, internet

   **Subscriptions** — streaming, software/SaaS, memberships, news sites

   **Regular Transfers** — recurring transfers that aren't vendor charges (e.g. Venmo to a specific person monthly)

5. For each recurring item show: merchant name, typical amount, how many months it appeared, which account, and which person (if person field is populated).

6. End with an estimated monthly recurring total across all buckets.
