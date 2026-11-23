# Merge detection per worktree

`<date-slug>` is a checked id: see the runtime contract's "Names are data". For each `.lorestrom/worktrees/<date-slug>/` candidate, determine if its branch (`<date-slug>` by convention) has been merged into the default branch:

1. **Branch exists?** `git rev-parse --verify --quiet "refs/heads/<date-slug>"` — if the branch is already gone (was deleted upstream and locally), the worktree is orphaned and can be removed.
2. **Merged via PR (preferred)** — `gh pr list --head <date-slug> --state merged --json number,mergedAt --limit 1`. If a merged PR exists, the work is shipped.
3. **Merged locally** — `: "${BASE:?}" && git branch --merged "${BASE:?}" --format='%(refname:short)' | grep -Fqx -- "<date-slug>"` (an exact, fixed-string match; `BASE` from the default-branch snippet in the same call). Catches the case where the branch was merged locally or where `gh` isn't available.
4. **Neither** — branch is **not** merged. Skip. Do not remove an unmerged worktree (the user's in-progress work would be lost).
5. **Phased unit?** If the candidate's proposal record declares `## Phases`, a merged phase-1 branch means that *phase* shipped, not the unit. Teardown waits for the final phase. **Read [references/phased-units.md](references/phased-units.md)** before tearing anything down. No-op for unphased units.

This decides worktree **teardown**. The unit's gate is decided separately, by the helper's
`reconcile` on the unit's recorded heads (`references/release.md`): a merged branch is evidence
for it, never a substitute.

Report each candidate's state. For `--dry-run`, stop here.
