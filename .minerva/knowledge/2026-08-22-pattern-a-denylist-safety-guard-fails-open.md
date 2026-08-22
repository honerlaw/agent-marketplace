# A safety guard written as a denylist fails open on everything its author did not recall

**Date**: 2026-08-22
**Type**: pattern
**Summary**: enumerate what is SAFE, not what is dangerous — a denylist's gaps are invisible by construction

**Context**: .minerva/work/2026-08-22-close-open-issue-backlog (see git history if the worktree has been cleaned up)

## Context

`tests/test_skill_snippets.py` extracts fenced blocks from `SKILL.md` files and **executes**
them. That was safe only because every block it happened to extract was read-only — a
property nothing enforced, and one that stopped holding once `minerva:promote` documented
`gh label create` / `gh issue create`. A guard was added inside `fenced_blocks()` so every
extraction inherits it, checking the body against a list of mutating commands.

The guard shipped as a **denylist**: `gh issue create`, `gh label create`, `gh pr create`,
`git push`, and a handful more.

## Finding

Review found ten real gaps in that list on first inspection: `gh issue reopen`,
`gh pr edit`, `gh pr comment`, `gh pr review --approve`, `gh workflow run`,
`gh label delete`, `git rm`, `git reset --hard`, `git clean -f`, `git tag -d` — plus
`gh api graphql -f query='mutation {...}'`, which carries no `-X`/`--method` flag and so
bypassed the REST checks entirely. Any of these, in an extracted block, would have executed
against whatever repo the CI runner was authenticated to.

Inverted to an **allowlist** — read-only `gh` verbs (`list`, `view`, `status`, `diff`,
`log`, `checks`, `search`, `browse`), with any other `gh <resource> <verb>` flagged and
`gh api` judged separately — all ten close by construction. Verified both directions: every
read-only `gh` command in the corpus still passes, and each of the ten is now caught.

## Implications

For a guard whose failure mode is "executes something destructive", the denylist shape is
the wrong one and its inadequacy is **unobservable**: you cannot notice the entry you did
not think of, and the surface it guards (a third-party CLI) grows subcommands independently
of the list. An allowlist fails closed — a new read-only verb costs a red test, which is the
cheap direction, while a new mutating verb is refused by default.

The general rule: enumerate the safe set when the unsafe set is open-ended or externally
controlled. Enumerate the unsafe set only where it is small, stable and yours — `git`'s
mutating verbs qualify; another tool's subcommands do not.

## Related
- [[2026-08-22-pattern-verifying-a-side-effecting-snippet-mutates-real-state]] — builds on
- [[2026-08-11-pattern-an-unenforced-constraint-is-aspirational]] — see also
