# Allocating an id for a new file must scan across branches — "allocated" means ever-added on any ref

**Date**: 2026-08-05
**Type**: constraint
**Summary**: new-file id collisions merge cleanly with no conflict, so the allocator is the only backstop
**Context**: .minerva/work/049-add-only-knowledge-writes (see git history if the worktree has been cleaned up)

## Context
`minerva:promote` allocated knowledge NNNs as `max+1` over the local
`.minerva/knowledge/` directory — one directory, in one worktree. Entries sitting on
other in-flight branches were structurally invisible to it.

`minerva:propose` had already solved the same problem one layer up: it computes a work
unit's NNN by scanning local work dirs, local branches **and** remote branches,
explicitly "so parallel work in worktrees and remotes doesn't collide." Because a unit's
branch is *named* `NNN-slug` and pushed, every in-flight unit broadcasts its number.
Nothing equivalent existed one layer down.

The failure this produces is uniquely quiet. A knowledge entry is a **new file**, so when
two units pick the same number git merges both cleanly — there is no conflict to notice.
A near-miss was observed: two units independently selected 546, caught *only* because
their `index.md` appends happened to land on adjacent lines. Had they landed in different
Type sections, the duplicate would have shipped silently.

## Finding
**When ids name new files, allocation is the only thing standing between two concurrent
producers and a silent duplicate** — because the merge that would otherwise reveal the
collision succeeds. That makes the allocator safety-critical, which is why it lives in a
tested script (`scripts/knowledge_next_nnn.py`) rather than prose bash a skill describes.

It unions two sources:

1. the working tree's knowledge directory, **including entries not yet committed**;
2. every entry ever *added* along the history of any ref —
   `git log --all --diff-filter=A --name-only` over the knowledge path. One
   path-limited command rather than a per-ref `git ls-tree`, and strictly safer
   semantics: an entry whose file was later renamed or deleted still holds its number.

"Ever added on a **reachable** ref" is the precise contract. It excludes commits
reachable only from the reflog — an abandoned, force-deleted branch — because those never
shipped, and because reflogs are local and expiring, so honouring them would make
allocation differ between machines.

**Failures are loud.** A git error while scanning history raises rather than returning an
empty set, because an empty set is indistinguishable from "no entries" and would silently
collapse the whole thing to the unsafe local-only scan. The one deliberate exception is
`--fetch`, which only ever *widens* the scan, so a network failure leaves the result no
worse than not fetching.

## Implications
- Skipping a number costs nothing; reusing one is the entire bug. Bias every ambiguous
  case toward over-allocating.
- Resolve the corpus path from the repo root, never from the process CWD. A CWD-relative
  default returns `001` with exit 0 when run from a subdirectory — a silent under-count,
  which is the exact failure mode being defended against.
- Pass `-c core.quotePath=false` when parsing `git log --name-only`. Git C-quotes paths
  containing non-ASCII bytes, and the trailing quote defeats a `.md` end-anchor — dropping
  precisely the entries the working-tree scan *does* count.
- This generalises past knowledge entries: any scheme where concurrent producers mint ids
  for new files (migrations, fixtures, ADRs) has the same blind spot, and the same absence
  of a conflict to catch it.

## Related
- [[052-decision-promote-add-only-reconcile-on-default]] — builds on
- [[054-constraint-nnn-keyed-lookups-hide-duplicates]] — see also
- [[057-pattern-deferred-work-needs-a-trigger-not-an-assumption]] — the cataloguing half of the same concurrency story
