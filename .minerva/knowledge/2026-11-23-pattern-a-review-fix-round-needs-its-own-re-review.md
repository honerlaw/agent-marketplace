---
name: a-review-fix-round-needs-its-own-re-review
description: Use after applying a batch of review fixes — send only the fix commits to a fresh reviewer before shipping; fixes introduce defects of their own, including silent changes to the approved plan.
metadata:
  type: pattern
---

# A review fix round needs its own fresh re-review before it ships

**Date**: 2026-11-23
**Type**: pattern
**Theme**: silent-success
**Summary**: every fix round re-reviewed found new medium defects, one silently changing the approved plan
**Context**: .minerva/work/2026-11-22-lorestrom-backend (see git history if the worktree has been cleaned up)

## Context

Each lorestrom phase went through a Verifier and code review, and every finding was fixed with a
test that fails when the fix is reverted. All gates were green after each round. The fix
commits were then sent alone to a fresh reviewer.

## Finding

Both re-reviews found defects the fixes had introduced, none caught by the green gates or the
revert checks:

- **0.2.0:** the fix that let a user's confirmation reach `reconcile` was dropped one step later,
  because the release step re-ran `reconcile` without it, so the user would be asked twice. A
  hardening fix made fast-forward merges ask instead of release, silently changing the plan's
  release rule while the triage said "no replan". Resurrecting a unit failed when its local branch
  still existed.
- **0.3.0:** the Verifier's diff was fixed in one file but its brief in another still used the
  committed-only diff; a new "wait for the final phase" check, read literally, refused promote
  forever on an unphased unit.
- **0.4.0:** the fix that made every cleanup check who opened a unit, so `--yes` acts only on
  one's own, left the autonomous orchestrator facing a question it neither expected nor counted
  when it resumed a colleague's unit.

The revert checks prove each fix is tested, not that the fix is consistent with the steps around
it: most fix tests pin new text, so a flow that contradicts itself across two files passes them.

## Implications

- After a fix round, review `git diff <before-fixes>..HEAD` with a fresh reviewer told what each
  fix was meant to do, and ask explicitly whether any fix changed an approved rule.
- A fix that changes behaviour the plan states is a plan change: amend the plan or revert the fix.

## Related
- [[2026-08-28-pattern-an-author-audits-rules-a-reviewer-audits-wiring]] — builds on: fixes are checked against rules by their author and miss the wiring between steps
- [[2026-09-23-pattern-a-unanimous-quorum-deadlocks-on-write-up-fixes]] — relates to: another place where fixing review findings needed its own path
