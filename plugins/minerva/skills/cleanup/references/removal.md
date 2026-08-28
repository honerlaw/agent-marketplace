# cleanup — the removal protocol

Runs once the [Confirmation gate](../SKILL.md#confirmation-gate) has passed. Every step here is
deliberately conservative: cleanup's failure mode is destroying unmerged work, so each operation
prefers to refuse and surface than to force.

For each confirmed worktree:

1. **Remove the worktree** — `git worktree remove .minerva/worktrees/<date-slug>`.

   If this fails because the worktree has uncommitted changes, **surface the error and skip**.
   Do not force-remove without explicit user direction: uncommitted changes sitting in a
   worktree whose branch is *merged* are a contradiction worth showing the user, not a
   formality to override.

2. **Delete the branch** — `git branch -d <date-slug>`.

   `-d` (safe delete), never `-D` (force). If `-d` refuses because git thinks the branch is not
   merged — rare after a PR merge, and usually a squash-merge artifact — fall back to
   `git branch -D <date-slug>` **only** if the merged-PR check in step 2 of
   [Merge detection](../SKILL.md#merge-detection-per-worktree) passed.

   Squash-merging leaves a different commit hash on the default branch, so local `git branch -d`
   genuinely cannot tell a squashed merge from an unmerged branch. That is why the override is
   gated on the *PR* evidence rather than on the local ref: one of the two sources knows the
   answer, and it is not git.

3. **Phased unit only** — prune the unit's other merged `<date-slug>-phase-N` branches the same
   way, with the identical `-D` fallback and the identical per-phase precondition. Resolve every
   name through `phase_branch()` in `scripts/work_status.py` rather than rebuilding the string.
   Full rules in [phased-units.md](phased-units.md).

4. **Prune metadata** — `git worktree prune`, which cleans up any stale worktree entries left by
   a directory someone removed by hand.

After all removals: `git worktree list`, to show the final state.
