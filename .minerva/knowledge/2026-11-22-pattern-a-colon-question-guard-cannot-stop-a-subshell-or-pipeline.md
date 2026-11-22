---
name: a-colon-question-guard-cannot-stop-a-subshell-or-pipeline
description: Use when a shell snippet relies on `${VAR:?}` to stop when a required variable is unset — inside `$(…)` or one stage of a pipeline it only ends that subshell, and the outer command runs on with an empty value.
metadata:
  type: pattern
---

# A `${VAR:?}` guard cannot stop a call from inside `$(…)` or a pipeline

**Date**: 2026-11-22
**Type**: pattern
**Theme**: silent-success
**Summary**: `:?` exits only the subshell it is in; put `: "${VAR:?}" &&` first on such a line
**Context**: .minerva/work/2026-11-22-untrusted-ref-names (see git history if the worktree has been cleaned up)

## Context

The 4.0.1 default-branch snippet sets `BASE`, and every use is `"${BASE:?}"` so a call that
skipped the snippet stops instead of running on an empty value. Review found
`git diff "$(git merge-base "${BASE:?}" HEAD)"...HEAD`: with `BASE` unset the substitution's
subshell printed an error and exited, the outer `git diff` ran as `git diff ...HEAD`, produced an
empty diff and exited 0, and the review step concluded there was nothing to review. The same
holds in bash and zsh, and for a stage of a pipeline (`git show "${BASE:?}:f" | grep -q x` simply
reads as "no match").

## Finding

`${VAR:?}` makes the *shell that expands it* exit. In `$(…)` and in a pipeline stage that shell is
a subshell, so the failure is reduced to an empty output or a false result: success-shaped. Put
the guard where the calling shell expands it — `: "${BASE:?}" && <the line>` — or restructure so
no guarded expansion sits inside a substitution (three-dot `git diff A...B` already diffs from
the merge base).

## Implications

- `tests/test_untrusted_names.py` flags `${BASE:?}` inside `$(…)` and a piped line without the
  leading `: "${BASE:?}" &&`.
- Any "fail loudly if unset" convention needs the same check wherever the variable can land in a
  substitution or a pipe.

## Related
- [[2026-11-22-decision-skills-treat-branch-and-ref-names-as-data]] — refines: why its snippet's uses carry a leading guard on piped lines
