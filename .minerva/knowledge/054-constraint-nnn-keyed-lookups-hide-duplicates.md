# An id-keyed dict makes duplicate ids unrepresentable — group first, then quarantine

**Date**: 2026-08-05
**Type**: constraint
**Summary**: `{id: record}` silently drops duplicates; build `{id: [records]}` and exclude dupes from every derived edit
**Context**: .minerva/work/049-add-only-knowledge-writes (see git history if the worktree has been cleaned up)

## Context
Both wiki tools built their lookup the same way:

```python
entries = {ENTRY_RE.match(p.name).group(1): (p, parse_entry(p)) for p in entry_paths}
```

A dict comprehension keyed on NNN. When two entry files share a number, the later one
silently overwrites the earlier, and every check downstream sees one entry where two
exist. `knowledge_lint` therefore reported a **clean NNN↔file bijection** over a corpus
containing duplicates — the defect was invisible by construction, in the one tool whose
job is detecting exactly that defect. A consumer repo carries **65 such groups** on its
default branch today.

`knowledge_fix` had the identical shape, which is worse because it *mutates*: on a
duplicate it collected both catalog lines (both match the single surviving entry) and
bucketed both under the survivor's declared type — misfiling the loser's line. The first
automatic reconciliation run would have misfiled up to 65 lines.

## Finding
**Group by id before keying on it**, so a duplicate is representable and reportable:

```python
by_nnn = {}
for p in entry_paths:
    by_nnn.setdefault(ENTRY_RE.match(p.name).group(1), []).append(p)
```

Then report any group with more than one member as an error — and **quarantine those ids
from every downstream check and edit**. Quarantine is the part that is easy to miss. The
surviving member of a group is arbitrary, so anything derived from it is attributed to
the wrong file: a type-mismatch finding names the wrong entry, a relocation misfiles the
other's catalog line, a reciprocal back-link lands in whichever file won the lookup.

Quarantine deliberately mirrors the conservative shape the fixer already used for
unrecognized types — *left where it is, never dropped, recorded as a refusal* — rather
than inventing a new failure mode. That is what lets the whole design land on a corpus
with 65 legacy duplicate groups on day one, without renumbering anything first
(renumbering would break every `[[NNN-...]]` link, which needs a rename-apply tool this
project has deferred).

## Implications
- Any id-keyed map over user- or agent-authored filenames needs this treatment. The
  failure is silent, and it is silent *specifically in the tool meant to catch it*.
- A duplicate id is an **error**, not a warning, even on a corpus that already has 65 of
  them — the repos with legacy duplicates do not run the lint, and the repo that does run
  it is clean, so erroring costs nothing today and stays loud for a fresh collision.
- Report duplicates **first**. Every other check is id-keyed, so its output is untrustworthy
  while a duplicate exists; leading with the duplicate points the reader at the real problem.
- Widen the id pattern past its current width (`\d{3,}`, not `\d{3}`) and compare with
  `int()`. A fixed-width regex silently stops matching at the boundary, which would make
  the 1000th entry invisible to the allocator **and** to this duplicate check
  simultaneously — both backstops failing at the same moment.

## Related
- [[052-decision-promote-add-only-reconcile-on-default]] — see also
- [[055-constraint-knowledge-allocation-scans-across-branches]] — see also
