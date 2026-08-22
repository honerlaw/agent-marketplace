# A just-written index is not a read-back guarantee

**Date**: 2026-08-22
**Type**: pattern
**Summary**: guard a retry with the local record; an eventually-consistent index misses what you just wrote

**Context**: .minerva/work/2026-08-22-followups-become-github-issues (see git history if the worktree has been cleaned up)

## Context

`minerva:promote` gained the ability to file kept TODO items as GitHub issues. Issue
creation is the only externally-visible side effect promote has, and a duplicate is a
notification on someone's repository — so the design needed the same
check-before-write that `minerva:ship` uses (`gh pr view` before `gh pr create`).

The first draft guarded it with a repository search:

```
gh issue list --state all --search '"<date-slug>" in:body'
```

which reads GitHub's **search index**. That index is not updated synchronously with
issue creation: an issue filed seconds ago is frequently not yet searchable.

## Finding

The guard was strongest exactly where it was needed least and weakest exactly where it
was needed most. A re-run days later — when nothing is likely to be duplicated anyway —
searches a fully-indexed corpus and works. A retry seconds after a partial failure — the
one scenario the guard exists for — searches an index that has not caught up, finds
nothing, and files the duplicate it was written to prevent.

The general shape: **when a write and its guard go through different consistency
domains, the guard is silently weakest in the window right after the write.** A search
index, a CDN, a read replica, and a cache all behave this way. Code that writes and then
re-reads through the slower path to decide "did I already do this?" is asserting a
read-back guarantee the system never offered.

The fix is not a longer timeout or a retry loop. It is to check the source you control
first, and demote the eventually-consistent one to a backstop for the cases only it can
see. Promote now checks, in order: the run's own record of what it just created, the
unit's `proposal.md` `## Deferred work` section (local, exact, instant), and only then
the repository search — which now covers just the genuinely remote case, a re-run from a
different clone or session.

## Implications

- Any future minerva step that creates a remote artifact and guards against duplicates
  must record what it created **locally**, and treat a remote query as a backstop rather
  than the authority. `## Deferred work` in `proposal.md` exists for this reason as much
  as for the durable record.
- When reviewing a check-before-write, ask which consistency domain the check reads from
  and whether it is the same one the write lands in. If not, the correct question is not
  "is this check correct?" but "how stale can it be, and is that the window I care about?"
- This is why the record is written as a historical fact (*this unit deferred that item
  to that issue*) rather than as live state. A historical fact is safe to read back
  immediately and never needs invalidating.

## Related
- [[2026-08-05-pattern-read-then-act-is-not-a-lock]] — the adjacent failure: there, a read-then-act gap between two writers; here, a read-back gap between one writer and its own guard
- [[2026-07-29-pattern-wait-shape-matches-what-is-awaited]] — same root discipline: match the mechanism to what is actually being waited on or read
