# Repeated blocks that look like copy-paste may be deliberate divergence

**Date**: 2026-08-22
**Type**: pattern
**Summary**: read the copies before choosing the invariant — a byte-identity test over intentionally-divergent blocks either cannot pass or passes vacuously

**Context**: .minerva/work/2026-08-22-close-open-issue-backlog (see git history if the worktree has been cleaned up)

## Context

Six skills (`work`, `replan`, `promote`, `cleanup`, `review`, `ship`) each carry a
`## Target resolution` block, kept in sync only by the sentence **"Keep all six blocks in
sync if you edit one."** — a plea with nothing enforcing it, and the wording had already
diverged. The obvious repair, and the one a consensus panel approved, was a normalized-diff
test: strip the per-file sibling enumeration, assert the remainder is byte-identical.

## Finding

The six blocks are **not copies**, and the divergence is deliberate:

| block | steps | why it differs |
|---|---|---|
| `cleanup` | 3 | its no-argument mode means "all merged worktrees", not a single target |
| `review` | 5 | step 5 = no minerva context, skip to code review, **do not stop** |
| `ship` | 5 | step 5 = **bare mode**, ship from git state alone |
| `promote` | 5 | extra paragraph for Mode B |
| `work` / `replan` | 5 | one verbose with a worked example, one terse |

Normalizing enough to make `cleanup`'s three steps match `work`'s five would have erased
everything the test was supposed to check — a test that cannot fail, dressed as a strict one.

What is genuinely shared, exact, and load-bearing turned out to be narrower: each block
names its five siblings, and each states both lookup rules (scan `.minerva/work/*/` **and**
`.minerva/worktrees/*/`; match both the `YYYY-MM-DD-<slug>` and legacy `NNN-<slug>` id
forms). The second is not stylistic — a digit-anchored glob silently skipping date-named
units is a bug this repo has already shipped and fixed.

## Implications

"N copies of a block plus a comment asking them to stay in sync" reads as pure duplication
and invites a byte-identity check. Read the copies first. When they differ on purpose, the
enforceable invariant is the intersection — the specific clauses whose absence causes bugs —
not the whole text. Choosing byte-identity anyway forces one of two bad outcomes: the test
cannot pass, or the normalization is loosened until it passes and checks nothing.

Extraction to a single shared file is the other instinct, and it was rejected here for the
same reason: with six genuinely different blocks there is no single block to extract.

## Related
- [[2026-08-11-pattern-a-comment-cannot-enforce-a-shared-invariant]] — builds on
- [[2026-08-10-pattern-presence-assertions-rot-into-green-lies]] — see also
