# A read-then-act check is not a lock — make the atomic primitive the lock

**Date**: 2026-08-05
**Type**: pattern
**Summary**: gate concurrency on an atomic operation's own success, not on a preceding "is it taken?" read
**Context**: .minerva/work/049-add-only-knowledge-writes (see git history if the worktree has been cleaned up)

## Context
`minerva:cleanup`'s reconciliation must not run twice concurrently: two passes editing
`index.md` at once would conflict with each other, recreating the exact problem the
add-only design removes ([[052-decision-promote-add-only-reconcile-on-default]]).

The first design enforced that with a check:

```bash
gh pr list --head minerva/reconcile --state open   # if one exists, skip
```

which reads plausible and is not a lock at all. Two cleanups running at once — a manual
invocation racing a scheduled orchestrator wake-up is entirely realistic — both see no
open PR, both proceed, both push the same branch.

## Finding
**A read followed by an act is not mutual exclusion, no matter how correct the read is.**
The check-then-act window is always there; a busier system just finds it more often.

The fix is to identify the operation that is *already* atomic and let its success be the
lock. Here that is the git ref update: a **non-forced** `git push` to a fixed branch name
is atomic, so of two concurrent pushes exactly one succeeds and the other is rejected as
non-fast-forward. The loser treats rejection as the serialization signal — reports
"another run is in flight", cleans up, and exits 0. That is a correct outcome, not a
failure: both runs computed their edits from the same default-branch corpus, so the
winner's pass covers the loser's work.

The original read stays, demoted to what it actually is — a cheap early-out that avoids
pointless work in the common case, explicitly documented as *not* the lock.

## Implications
- `--force` and `--force-with-lease` are forbidden on such a branch. Forcing converts the
  lock back into a race, and worse, lets a second run overwrite the first's branch out
  from under its already-open PR.
- Look for the atomic primitive before writing a guard: an exclusive file create, a unique
  index insert, a compare-and-swap, a ref update. Most systems already have one, and using
  it costs less than the check it replaces.
- When a check is genuinely only an optimisation, say so in the code. The failure mode of
  a check-then-act guard is that it *looks* sufficient, so the next reader extends it
  rather than replacing it.
- Cost of getting this wrong is asymmetric here: the guard protects the one file whose
  conflicts this entire work unit exists to eliminate.

## Related
- [[052-decision-promote-add-only-reconcile-on-default]] — builds on
- [[057-pattern-deferred-work-needs-a-trigger-not-an-assumption]] — the sibling hazard: that one is two runs racing, this one is no second run existing
