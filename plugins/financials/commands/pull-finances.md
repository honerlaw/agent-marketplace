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

1. Check the user's message for a bank name. Build the command:
   - All banks: `python3 ~/.claude/plugins/financials/scripts/pull.py`
   - One bank:  `python3 ~/.claude/plugins/financials/scripts/pull.py <bank>`

2. Run the script in the **background** using the Bash tool with `run_in_background=true`.

3. Wait ~3 seconds, then tell the user: "A browser window is opening for [bank]. Log in with your credentials, then come back here and tell me when you're done."

4. When the user says they're logged in (or done with 2FA), signal the script to continue:
   ```bash
   touch /tmp/financials-continue
   ```
   Then read the status to see what happened next:
   ```bash
   cat /tmp/financials-status
   ```

5. If the status says `WAITING_2FA`, tell the user to complete 2FA in the browser and wait for them again. When ready, `touch /tmp/financials-continue` again.

6. Repeat for each bank in sequence. The script processes them one at a time.

7. When complete (you'll receive the background task notification), report which banks succeeded, which errored, and the snapshot folder path.
