---
description: Show spending organized by category for the latest snapshot — no targets, just actuals. Categories inferred by Claude from transaction descriptions.
---

Break down spending by category for the latest snapshot (or a given date).

## Usage

- `/spending-breakdown` — use the most recent snapshot
- `/spending-breakdown 2026-04-01` — use the snapshot from that date

## Steps

1. Determine the snapshot directory:
   - If the user provided a date, use `~/Documents/financials/snapshots/<date>/`
   - Otherwise find the most recently dated folder in `~/Documents/financials/snapshots/`

2. Read all CSV files in that folder.

3. For each transaction, infer a category from the description field. Examples:
   - Whole Foods, Kroger, Trader Joe's, Publix → Groceries
   - Restaurants, cafes, DoorDash, Uber Eats → Dining
   - Airlines, hotels, Airbnb, Uber, Lyft → Travel
   - Shell, BP, ExxonMobil → Gas & Auto
   - Netflix, Spotify, Adobe, Apple subscriptions → Subscriptions
   - CVS, Walgreens, doctor/hospital names → Medical
   - Amazon, Target, retail → Shopping
   - Utilities, insurance providers → Bills
   - Transfers, payments, Venmo, Zelle → Transfers
   - Everything else → Other

4. Produce a table sorted by total spend descending:

   | Category | Transactions | Total Spent |
   |----------|-------------|-------------|

5. List any transactions you couldn't confidently categorize at the bottom for user review.
