# Proposal: enforce-fence-aware-scans

**Date**: 2026-08-11
**Status**: Draft
**Base**: `origin/main`

## Goal

Make the fence-awareness constraint enforceable instead of aspirational, and fix the one
violation the enforcement finds.

## Why

[[2026-06-11-constraint-fence-scans-import-fence-re]] says any scan over markdown must
import the single-sourced `FENCE_RE` grammar. Nothing checks it, and it keeps being
violated: both readers in `work_status.py` shipped fence-blind — one of them in the unit
immediately before this — past three reviewers, in a repo where every skill documenting a
convention contains a fenced example of it. `2026-08-11-close-the-followups` recorded that
the constraint is prose with no test behind it.

**The enforcement finds a live defect immediately.** `knowledge_fix.plan_index` scans
`index.md` with a bare `old.splitlines()` while `knowledge_lint.parse_index` scans the same
file through `_strip_fences`. A fenced catalog line naming a real entry is therefore
invisible to the detector and a live line to the fixer — and `plan_index` **rewrites**
index.md from what it parses. Reproduced:

```
## Decisions

```· - [[2026-01-01-decision-real]] — QUOTED IN A FENCE, not the real summary ·```

- [[2026-01-01-decision-real]] — the real one
```

produces an index cataloguing that entry **twice**, one of them carrying the example's fake
summary, with zero refusals — while `knowledge_lint` reports the corpus clean, because its
own parse never saw the fenced line. Same detector-disagrees-with-editor shape as the
`## Related` edge model ([[2026-08-11-pattern-a-comment-cannot-enforce-a-shared-invariant]]),
in a writer.

## Approach

### 1. Fix `plan_index`

Route its catalog scan through `_strip_fences`, the same helper `parse_index` already uses,
so the two read `index.md` identically.

### 2. Enforce the constraint by asking the corpus, not by listing modules

`tests/test_fence_awareness.py` enumerates `plugins/minerva/scripts/*.py` and requires that
**any module calling `.splitlines()` references the shared fence grammar** (`FENCE_RE`,
`_strip_fences`, or a helper built on one). That invariant is currently 100% true of every
module once item 1 lands, so it starts with **zero exemptions**.

Deliberately **not** a curated list of "the markdown-scanning modules". A hand-maintained
list of which things need checking is the exact artifact
[[2026-08-11-pattern-the-enumeration-is-what-fails]] says decays — and it would decay in
the dangerous direction, since a module omitted from it is silently unchecked.

The escape hatch lives **at the site, not in the test**: a module that legitimately scans
non-markdown declares `# not-markdown: <reason>` on the scanning line. That keeps the
justification next to the code it excuses, and makes an unjustified exemption impossible to
add quietly. The test asserts any such marker carries a reason.

Paired with negative coverage — a fixture proving the check actually fires on a fence-blind
scan — in the style `tests/test_skill_budget.py` already uses for its strengthened checks.

## Success criteria

1. `knowledge_fix.plan_index` and `knowledge_lint.parse_index` agree on `index.md`: a fenced
   catalog line is a live line to neither.
2. A fenced catalog line naming a real entry no longer duplicates that entry in the
   rewritten index — verified against the reproduction above.
3. `tests/test_fence_awareness.py` fails when any `scripts/*.py` gains a `.splitlines()`
   scan without the fence grammar and without a reasoned `# not-markdown:` marker.
4. The check has negative coverage: a fixture proves it fires rather than passing vacuously.
5. Zero exemptions are needed today.
6. Bare `python3 -m pytest` passes (baseline 501) and `knowledge_lint` stays clean.

## Open questions

None.
