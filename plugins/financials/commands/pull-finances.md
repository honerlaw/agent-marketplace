---
description: Pull 90 days of transaction CSVs from Truist, Amex, and Citi. Run all three banks or name one: truist, amex, or citi.
---

Pull financial transactions from bank accounts and save a dated snapshot locally.

## Usage

- `/pull-finances` — pull all three banks in sequence
- `/pull-finances amex` — pull only Amex
- `/pull-finances truist` — pull only Truist
- `/pull-finances citi` — pull only Citi

## Steps

1. Build the command based on the argument (or omit bank name for all three):
   ```
   python3 ~/.claude/plugins/financials/scripts/pull.py [bank_name]
   ```

2. Run it in the **background** (Bash tool with `run_in_background=true`).

3. Wait ~4 seconds, then read `/tmp/financials-status` to see the current state.

### Login / 2FA pauses

When status contains `WAITING_LOGIN` or `WAITING_2FA`, tell the user which bank needs attention. When they say they're done:
```bash
touch /tmp/financials-continue
```
Then read status again to see what happened.

### Agent navigation loop

After login, the script enters an agent loop. It will:
- Take a screenshot → `/tmp/financials-screenshot.png`
- Write a JSON status to `/tmp/financials-status` containing: `url`, `title`, `elements` (all links/buttons on the page), `screenshot` path

**Your job**: read the screenshot (use the Read tool on the image path — Claude can view images), look at what's on the page, and decide the next navigation step. Then write a command to `/tmp/financials-command.json`:

```json
{ "action": "click",    "selector": "text=Download Transactions" }
{ "action": "goto",     "url": "https://..." }
{ "action": "fill",     "selector": "#startDate", "value": "02/15/2026" }
{ "action": "select",   "selector": "select#format", "value": "csv" }
{ "action": "download", "selector": "text=Download" }
```

Selector tips:
- Prefer text selectors: `text=Download Transactions` or `button:has-text('Export')`
- Fall back to IDs/classes from the `elements` list in the status JSON
- Use `goto` to jump directly to a known URL (faster than clicking through menus)

The script executes the command and immediately takes a new screenshot for the next step. Repeat until you issue a `download` action, which saves the file and moves on to the next bank.

### Completion

When all banks finish, the background task completes. Report which banks succeeded, which errored, and the snapshot folder path from the output.
