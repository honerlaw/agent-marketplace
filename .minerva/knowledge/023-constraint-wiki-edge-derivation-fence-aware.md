# Any tool that derives knowledge-wiki cross-reference edges must be fence-aware — a fenced `## Related` example is not a real edge

**Date**: 2026-06-03
**Type**: constraint
**Context**: .minerva/work/023-knowledge-lint-fix (see git history if the worktree has been cleaned up)

## Context

Knowledge entries cross-reference each other via `[[NNN-type-slug]]` links in a
`## Related` block ([[015-constraint-knowledge-cross-reference-convention]]). But
entries — especially convention/documentation entries like 015 itself — contain
**fenced code examples** that show a `## Related` block and example `[[…]]` links.
Those fenced examples are illustrations, not real edges.

## Finding

**Every tool that derives the cross-reference *edge graph* from entry text must be
fence-aware**: lines inside a ```` ``` ```` / `~~~` code fence are ignored, and only
the *last non-fenced* `## Related` block counts. A fenced `## Related` example must
never be read as a real forward edge.

This is a recurring trap, which is why it's a standing constraint rather than a
one-off fix:

- The read-only detector (`scripts/knowledge_lint.py`) was made fence-aware from the
  start (`_strip_fences`; unit 021).
- The first cut of the Phase-B.3 *fixer* re-introduced the bug: its `_forward_related`
  edge parser read raw lines, so a fenced `## Related` example (e.g. in entry 015)
  would have produced a **spurious** supersession banner / reciprocal `## Related`
  line on the referenced entry — a mutation on a corpus the detector reports clean.
  Caught in review and fixed by importing `_strip_fences` from the (frozen) detector.

## Implications

- A new edge-deriving tool (the Phase-C synthesis/`log.md` tooling will be the next
  one) must reuse the detector's fence-aware parsing (`_strip_fences`) or consume the
  detector's already-fence-stripped output — never re-derive the edge graph from raw
  `splitlines()`.
- The hazard is asymmetric and silent: a non-fence-aware *reader* sees edges the
  gated detector doesn't, so it can diverge from a "clean" corpus without any gate
  catching it. Match the detector's edge model exactly.
- The detector exposes `parse_entry(...).related_out` (fence-aware, NNN-keyed) but
  drops relationship *labels*; a tool that needs labels still parses the `## Related`
  block itself — and that parser must be fence-aware too.

## Related
- [[015-constraint-knowledge-cross-reference-convention]] — builds on
- [[022-decision-knowledge-fix-two-safety-models]] — see also
- [[024-decision-synthesis-layer-separate-file-advisory]] — see also
- [[028-bug-knowledge-edits-not-fence-aware]] — see also
