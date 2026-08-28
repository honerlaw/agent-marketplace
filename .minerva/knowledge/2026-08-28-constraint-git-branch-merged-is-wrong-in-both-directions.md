---
name: git-branch-merged-is-wrong-in-both-directions
description: Use when deciding whether a work-unit or phase branch has shipped — `git branch --merged` misses a squash-merged branch AND reports a freshly created zero-commit branch as merged, so query the merged PRs first and never union the two sources.
metadata:
  type: constraint
---

# `git branch --merged` is wrong in both directions; query merged PRs first

**Date**: 2026-08-28
**Type**: constraint
**Summary**: It misses squash merges and counts a zero-commit branch as merged; a union inherits both errors
**Context**: .minerva/work/2026-08-28-workstream-status-skill

## The rule

To decide whether a branch has shipped, ask the tracker:

```bash
gh pr list --state merged --limit 200 --json headRefName -q '.[].headRefName'
```

Fall back to `git branch --merged <default>` **only** when `gh` is unavailable, unauthenticated,
or the repo has no GitHub remote. This is the order `minerva:cleanup` already documents under
"Merge detection"; what follows is why the fallback must stay a fallback rather than becoming a
second opinion.

## Both failure directions are live

**False negative — squash merges.** A squash-merged branch's commits are not ancestors of the
default branch, so `git branch --merged` cannot see it. Observed directly: with phase 1 of a
phased unit merged via PR, the git query reported it unmerged and `phase_progress` answered
`next_position: 1` for a phase that had already shipped.

**False positive — the empty branch.** A branch created from the default branch and not yet
committed to points at the same commit, so it *is* an ancestor, and `git branch --merged` lists
it. A brand-new phase branch therefore reads as already merged — the most dangerous reading
available, because it marks unstarted work as done.

## Do not union the two sources

The tempting repair is to take the union and treat any hit as merged. That inherits both errors
instead of cancelling them: the false positive is *in the git arm*, so unioning imports it while
adding nothing the PR query lacked. Precedence, not aggregation.

## Fetch first

Both arms read refs. A stale local ref reports a merged branch as unmerged, which is how a
teardown or a phase advance gets deferred forever on work that is actually finished.

## Related
- [[2026-08-24-pattern-a-lock-on-a-derived-name-does-not-cover-the-source]] — see also: another case of a branch-name-derived signal not meaning what its name suggests
- [[2026-08-22-pattern-a-value-written-before-its-evidence-needs-re-verifying]] — see also: a merged-ness answer is only as fresh as the fetch behind it
