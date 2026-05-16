# Financial Aggregator Plugin — Design Spec
**Date:** 2026-05-16
**Status:** Approved

## Overview

A personal Claude Code plugin marketplace, starting with a `financials` plugin. The marketplace lives in a single GitHub repository. Each plugin is a self-contained subdirectory with its own skills and scripts. Plugins are installed by cloning the repo and running `./install.sh <plugin-name>`, which symlinks the plugin into `~/.claude/plugins/` and registers it in `~/.claude/settings.json`.

The `financials` plugin uses Python + Playwright to pull transaction CSVs from Truist, Amex, and Citi via headless browser automation with a manual 2FA pause, saves timestamped snapshots locally, and exposes Claude Code skills for financial analysis.

---

## Repository Structure

```
claude-marketplace/                  # GitHub repo root
├── README.md
├── install.sh                       # installs any plugin by name
├── .claude/
│   └── settings.json                # dev settings for working on the marketplace
└── plugins/
    └── financials/
        ├── plugin.json
        ├── README.md
        ├── skills/
        │   ├── pull-finances.md
        │   ├── spending-summary.md
        │   ├── spending-breakdown.md
        │   ├── recurring-expenses.md
        │   └── cross-account.md
        └── scripts/
            ├── pull.py              # main runner, sequences all 3 banks
            ├── banks/
            │   ├── truist.py
            │   ├── amex.py
            │   └── citi.py
            └── lib/
                ├── browser.py       # shared Playwright setup, 2FA pause logic
                └── storage.py       # snapshot folder creation, CSV normalization
```

---

## Install Flow

```bash
git clone https://github.com/<user>/claude-marketplace
cd claude-marketplace
./install.sh financials
```

`install.sh financials` does three things:
1. Creates `~/.claude/plugins/financials` as a symlink to `plugins/financials/`
2. Adds the plugin entry to `~/.claude/settings.json`
3. Prints confirmation and lists available skills

Updates: `git pull` in the cloned repo — symlink keeps the plugin live immediately.

---

## Data Pull Flow

**Trigger:** `/pull-finances` (or `/pull-finances truist` for a single bank)

```
/pull-finances
    ├── truist.py
    │   ├── Open headless Chromium → truist.com login
    │   ├── Detect 2FA → surface browser window, pause terminal
    │   ├── User completes 2FA → presses Enter
    │   ├── Navigate to Transaction History → Export
    │   ├── Set date range: today - 90 days
    │   └── Save → ~/Documents/financials/snapshots/2026-05-16/truist_checking.csv
    ├── amex.py   (same pattern)
    │   └── Save → ~/Documents/financials/snapshots/2026-05-16/amex_credit.csv
    └── citi.py   (same pattern)
        └── Save → ~/Documents/financials/snapshots/2026-05-16/citi_credit.csv
```

Each run creates a new dated folder. Previous snapshots are never modified.

---

## CSV Normalization

`lib/storage.py` normalizes all bank CSVs to a standard schema:

| Normalized Field | Truist        | Amex          | Citi                  |
|-----------------|---------------|---------------|-----------------------|
| `date`          | `Date`        | `Date`        | `Transaction Date`    |
| `amount`        | `Amount`      | `Amount`      | `Debit` / `Credit`    |
| `description`   | `Description` | `Description` | `Description`         |
| `type`          | `Type`        | `Type`        | `Transaction Type`    |
| `person`        | *(verify)*    | `Card Member` | *(verify)*            |

The `person` field is sourced directly from the downloaded CSV — no manual config. Exact Truist and Citi column names for cardholder are confirmed on first pull and wired into the mapping.

---

## Skills

### `/pull-finances [bank?]`
Runs `scripts/pull.py`. Pulls all three banks in sequence (or one if specified). Prints per-bank status. Pauses with clear instructions when 2FA is needed. Reports final snapshot path on completion.

### `/spending-summary [YYYY-MM-DD?]`
Reads latest snapshot (or a specified date). Produces:
- Monthly totals for the last 3 months
- Top 10 merchants by spend
- Spend breakdown by category (Claude infers category from the `description` field — no static keyword list)
- Month-over-month delta
- Per-person spending breakdown (sourced from `person` field in CSV)

### `/spending-breakdown [YYYY-MM-DD?]`
Shows what was spent, organized by category/area — no targets or comparisons. Claude infers categories from the `description` field (groceries, dining, travel, gas, subscriptions, medical, entertainment, etc.) — no keyword list to maintain. Useful for understanding spending patterns without a predefined budget.

### `/recurring-expenses [YYYY-MM-DD?]`
Scans transactions across all accounts for recurring patterns (same merchant + similar amount on a monthly cadence). Buckets results into:
- **Bills** — utilities, insurance, mortgage/rent
- **Subscriptions** — streaming, SaaS, memberships
- **Regular transfers** — recurring but non-vendor transactions

### `/cross-account [YYYY-MM-DD?]`
Nets all transactions across Truist + Amex + Citi:
- Total income vs. total outflow for the period
- Spend distribution across accounts
- Credit card balance trends vs. checking outflows

---

## Key Constraints & Decisions

- **No credentials stored in repo** — login is always manual; Playwright navigates after the user authenticates
- **Snapshots are immutable** — each run creates a new dated folder, nothing is overwritten
- **Person attribution from data** — `person` field comes from the bank CSVs directly, no config file needed
- **Python throughout** — consistent language for both automation (Playwright) and analysis layers
- **Symlink-based install** — `git pull` updates the plugin immediately, no reinstall step
