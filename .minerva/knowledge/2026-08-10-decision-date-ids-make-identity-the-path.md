# Entry ids are dates, and identity is the path — so git enforces uniqueness

**Date**: 2026-08-10
**Type**: decision
**Summary**: an unallocated id plus full-stem identity turns silent duplicate-merges into loud add/add conflicts
**Context**: .minerva/work/2026-08-09-date-prefixed-identity

## Context
`NNN` was a scarce, globally-ordered id, so allocating it correctly was a distributed
consensus problem. `knowledge_next_nnn.py` existed solely to solve it, scanning
`git log --all --diff-filter=A` across local and remote refs with an optional `--fetch`.

It had to, because the failure was silent. Two branches picking `057` produce
`057-pattern-foo.md` and `057-pattern-bar.md` — **different paths**, so git merges both
cleanly and a duplicate id ships with nothing to catch it
([[2026-08-05-constraint-knowledge-allocation-scans-across-branches]]). One consumer
corpus accumulated 63 such collisions across 629 entries.

## Finding
**Stop allocating the id, and make identity the path.** An entry is
`YYYY-MM-DD-<type>-<slug>`; the date is read off the clock, so nothing coordinates.

The guard does not disappear — it moves into the filesystem. Two branches producing an
identical stem produce the **same path**, which is an add/add conflict git refuses to
merge. The failure mode inverts from silent to loud, and the allocator becomes dead
weight rather than the only backstop.

This does not weaken [[2026-08-05-constraint-knowledge-allocation-scans-across-branches]]'s
reasoning — it removes its premise. That entry is correct about *numbers*: while an id is
scarce, a cross-branch scan really is the only thing standing between two producers and a
silent duplicate.

**Several entries sharing a date is ordinary, not a defect.** Anything that treats a
shared leading token as a collision is now wrong — which is why the duplicate-id check and
its blanket quarantine were deleted rather than adapted
([[2026-08-05-constraint-nnn-keyed-lookups-hide-duplicates]] documents what that
quarantine cost when ids collided by accident; under dates it would fire constantly).

## Implications
- Never add a disambiguating suffix to "avoid" a shared date. Two entries with the same
  date, type and slug are the same entry and want merging.
- Any lookup keyed on the leading token is a bug. Key on the full stem.
- A date is **not totally ordered**, so no scalar floor over ids can express progress —
  see [[2026-08-05-constraint-reconciliation-state-is-not-a-scalar]], whose conclusion
  this makes structural rather than merely advisable.
- Sorting needs a composite key: legacy ids zero-padded to the corpus's own widest token,
  then dates. Plain lexicographic reintroduces `"1000" < "999"`.
- The dual-accepting grammar is permanent, not transitional: a consumer corpus migrates on
  its own schedule, and a filename outside `ENTRY_RE` is invisible to every wiki tool at
  once.

## Related
- [[2026-08-05-constraint-knowledge-allocation-scans-across-branches]] — supersedes
- [[2026-08-05-constraint-nnn-keyed-lookups-hide-duplicates]] — builds on
- [[2026-08-05-constraint-reconciliation-state-is-not-a-scalar]] — builds on
- [[2026-08-10-bug-absolute-path-guard-matches-everything-inside-a-worktree]] — see also
- [[2026-08-10-bug-git-follow-and-diff-filter-a-cancel-out]] — see also
- [[2026-08-10-pattern-presence-assertions-rot-into-green-lies]] — see also
