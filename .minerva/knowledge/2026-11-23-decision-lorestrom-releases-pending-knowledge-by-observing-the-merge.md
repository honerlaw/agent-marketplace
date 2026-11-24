---
name: lorestrom-releases-pending-knowledge-by-observing-the-merge
description: Use when changing lorestrom's cleanup, reconcile or orchestrator cleanup gates — new knowledge is held on the unit's Lorestrom gate and released only on observed merge evidence; --yes never confirms and orchestrators never abandon.
metadata:
  type: decision
---

# lorestrom releases a unit's pending knowledge only on observed merge evidence

**Date**: 2026-11-23
**Type**: decision
**Theme**: lifecycle
**Summary**: held writes release on recorded-head merge evidence; unproven merges ask the user; nothing auto-abandons
**Context**: .minerva/work/2026-11-22-lorestrom-backend (see git history if the worktree has been cleaned up)

## Context

minerva's records ride in the PR with the code, so merging the PR is what makes knowledge
current. Lorestrom is live and unbranched and never talks to git or GitHub. A unit's records are
not committed, so a fresh unit branch equals the default branch and `git branch --merged` reads
it as merged.

## Finding

- **Pending is a held write.** A unit is a `minerva:work_unit` doc with its own gate. A new entry
  is created `draft` with a held `set_status current` on that gate; cleanup releases the gate when
  the merge is observed, and repairs a failed flip only on an entry still `draft`.
- **Evidence is a recorded head.** ship records each phase's branch, PR and pushed head (again
  after every later push). The helper's `reconcile` returns `release`, `confirm`, `abandon` or
  `wait` from that record plus live git evidence; only 40-hex shas reach git, and the default
  branch is found, never taken from input. No recorded head, or one equal to the base, waits.
- **release:** every phase has a MERGED PR or a recorded head that is an ancestor of the default
  branch. A fast-forward merge with no PR record releases: git cannot tell a fast-forwarded head
  from a mainline commit, but ship records a head only for a branch with its own commits. A
  review fix that made this case ask the user was reverted for silently changing the plan's rule.
- **confirm:** no PR evidence, but merging the head changes nothing (a squash merge `gh` cannot
  see). The user's yes travels in the request (`userConfirmed`), counts only for phases the same
  evidence lists in `phasesToConfirm`, and must reach the release step: re-running `reconcile`
  without it asks the same question again. `--yes` never confirms.
- **abandon:** a CLOSED PR whose head is not merged, or an explicit `--abandon`. A sweep never
  abandons without a per-unit yes, and the orchestrators never abandon at all; an unproven merge
  at their cleanup step is a user question, counted as an escalation in the autonomous one.

## Implications

- Pending can lag a merge until some clone runs cleanup; status says so and shows ages.
- Tests for this table run in real temporary git repositories (squash, `--no-ff`, fast-forward,
  conflict), because the fresh-branch and fast-forward cases are exactly where intuition fails.

## Related
- [[2026-11-23-decision-lorestrom-is-a-separate-lorestrom-only-plugin]] — builds on: the plugin whose release this is
- [[2026-10-01-decision-knowledge-aggregates-are-derived-on-read]] — relates to: minerva needs no post-merge pass because its knowledge ships in the PR; lorestrom's cleanup is that pass
