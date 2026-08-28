# Merge detection per worktree

For each `.minerva/worktrees/<date-slug>/` candidate, determine if its branch (`<date-slug>` by convention) has been merged into the default branch:

1. **Branch exists?** `git rev-parse --verify <date-slug>` — if the branch is already gone (was deleted upstream and locally), the worktree is orphaned and can be removed.
2. **Merged via PR (preferred)** — `gh pr list --head <date-slug> --state merged --json number,mergedAt --limit 1`. If a merged PR exists, the work is shipped.
3. **Merged locally** — `git branch --merged <default> | grep -q "^[* ] <date-slug>$"`. Catches the case where the branch was merged locally or where `gh` isn't available.
4. **Neither** — branch is **not** merged. Skip. Do not remove an unmerged worktree (the user's in-progress work would be lost).
5. **Phased unit?** If the candidate's `proposal.md` declares `## Phases`, a merged phase-1 branch means that *phase* shipped, not the unit. Teardown waits for the final phase; reconciliation never does. **Read [references/phased-units.md](references/phased-units.md)** before tearing anything down. No-op for unphased units.

Report each candidate's state. For `--dry-run`, stop here.
