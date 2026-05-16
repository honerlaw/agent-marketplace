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

1. Check the user's message for a bank name argument. If present, pass it to the script. Otherwise omit it to pull all three.

2. Run the pull script:
   ```bash
   cd ~/.claude/plugins/financials/scripts && python pull.py [bank_name]
   ```

3. A browser window will open for each bank. The script will pause at each 2FA prompt and print instructions to the terminal. Tell the user to watch the browser window — they'll complete 2FA there, then press Enter in the terminal to continue.

4. When complete, report which banks succeeded, which (if any) errored, and the full path to the snapshot folder.
