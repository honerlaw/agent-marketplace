# A tolerant reader without a boundary reads the neighbour

**Date**: 2026-08-11
**Type**: pattern
**Summary**: permissiveness and scope are separate dials; widening what a parser accepts without bounding where it looks turns a gap-filler into a false reading
**Context**: .minerva/work/2026-08-11-close-the-followups

## Context
`work_status.read_status` resolves a work unit's `**Status**` field, falling back to a
`## Status` heading for the one proposal in 53 that predates the inline field. The obvious
fallback — *take the next non-blank line after the heading* — has a failure a reviewer
constructed before it shipped:

```
## Status

## Goal
Shipped code already exists for the export path; this proposal only adds Y.
```

The author left `## Status` empty. The parser walks past the blank line, past the `## Goal`
heading, and returns `"Shipped code already exists…"`. `startswith("Shipped")` then reads a
**live draft as finished**, and the in-flight check that exists to stop two agents
colliding on one unit stops protecting it.

The same module had a second instance of the same shape, found by a later reviewer and
missed by three earlier ones. Neither `read_status` nor `is_post_promote` was fence-aware,
so a fenced example — `**Status**: Shipped` in a template, or the promote marker in any of
the several skills that document the convention — shadows the real declaration below it.
Again the dangerous direction: documentation making a live unit look finished.

## Finding
**Permissiveness and scope are independent dials, and widening the first without setting
the second is what turns a tolerant reader into a wrong one.** Both bugs came from the
same move — accept more forms — applied without asking *where the value is allowed to be*.

That is easy to miss precisely when you are being careful about tolerance. Reading
authored metadata from wherever the author put it is correct and well-established here
([[2026-08-09-pattern-read-authored-metadata-from-where-it-is]],
[[2026-08-11-pattern-the-enumeration-is-what-fails]]). This entry is that pattern's
counterweight: **"wherever the author put it" still means inside the region that belongs to
the value.** A markdown section ends at the next heading. A declaration is not inside a
code fence. Neither bound is optional, and neither is implied by tolerance.

Two rules that fall out:

- **Bound the search to the structure, not to a distance.** "The next non-blank line" is a
  distance and it does not know what a section is; "up to the next `#` line" is the
  structure. Where the boundary yields nothing, return absent — an empty section means the
  author did not state a value, which is information, not a reason to keep looking.
- **Pick the tolerant direction from the failure cost, then check the widening cannot flip
  it.** `is_post_promote` reads generously because a false negative re-runs a mutating
  pass. `read_status` feeds an in-flight check where the dangerous direction is the
  opposite — reading a live unit as finished — so its fallback is deliberately narrower
  than its sibling's. Same module, same author, opposite calls, because the costs differ.

## Implications
- A fallback chain needs a **scope** per link, not just an order. State where each link is
  allowed to look before stating which wins.
- Fence-awareness is not a nicety in this corpus: every skill documenting a convention
  contains a fenced example of it, so any scan over skill or record markdown must import
  the single-sourced grammar ([[2026-06-11-constraint-fence-scans-import-fence-re]]). This
  was violated by a reader written *while fixing a tolerant-reading bug*.
- When adding tolerance to a parser, write the adversarial input first: an empty section, a
  fenced example, a near-miss heading (`## Status quo`), the value absent entirely. All
  four were cheap fixtures and two of them caught real defects.
- Reviewers found both instances and rereading found neither — consistent with what the
  sibling entries record about hand-checking one's own recognizer.

## Related
- [[2026-08-09-pattern-read-authored-metadata-from-where-it-is]] — builds on
- [[2026-08-11-pattern-the-enumeration-is-what-fails]] — builds on
- [[2026-06-11-constraint-fence-scans-import-fence-re]] — see also
- [[2026-08-11-pattern-an-unenforced-constraint-is-aspirational]] — see also
