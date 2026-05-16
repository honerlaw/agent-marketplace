# financials plugin

Pulls transaction CSVs from Truist, Amex, and Citi via Playwright and provides Claude Code skills for financial analysis.

## Setup

```bash
cd plugins/financials/scripts
pip install -r requirements.txt
python -m playwright install chromium
```

## Skills

| Skill | Description |
|-------|-------------|
| `/pull-finances [bank]` | Pull 90 days of transactions. Optional: `truist`, `amex`, or `citi` |
| `/spending-summary [date]` | Monthly totals, top merchants, categories, per-person breakdown |
| `/spending-breakdown [date]` | Spending by category — no targets, just actuals |
| `/recurring-expenses [date]` | Bills, subscriptions, and regular transfers |
| `/cross-account [date]` | Net cash flow across all accounts |

## Data

Snapshots saved to `~/Documents/financials/snapshots/YYYY-MM-DD/`.

## First Run Notes

On first pull, check the downloaded CSVs for Truist and Citi to confirm the cardholder column name. Update `BANK_SCHEMA` in `scripts/lib/storage.py` if the column exists.
