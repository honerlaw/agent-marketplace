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

1. This script requires an interactive terminal because it pauses for login and 2FA. Ask the user to run it directly by typing into their Claude Code prompt (the `!` prefix runs in their shell):

   - All banks: `! python3 ~/.claude/plugins/financials/scripts/pull.py`
   - One bank:  `! python3 ~/.claude/plugins/financials/scripts/pull.py amex`

2. A browser window opens for each bank. The script pauses at login and 2FA — the user types credentials in the browser, then presses Enter in the terminal to continue.

3. Once the user shares the terminal output, report which banks succeeded, which (if any) errored, and the full path to the snapshot folder.
