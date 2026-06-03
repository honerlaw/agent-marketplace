# knowledge_edits.py was not fence-aware — promote/fixer crashed (or silently no-op'd) on any edge into entry 015

**Date**: 2026-06-03
**Type**: bug
**Context**: .minerva/work/027-related-backfill (see git history if the worktree has been cleaned up)

## Context

Unit 027's backfill added a `see also [[015]]` edge from its promote entry. The fixer's
reciprocal pass — the first edge ever written INTO entry 015 through the editors —
crashed: `AssertionError: ## Related must be the last section`. The fixer's
all-or-nothing pre-write validation meant zero damage, but the latent landmine had
existed since unit 023 shipped `scripts/knowledge_edits.py`.

## Finding

The editors scanned **raw splitlines** — not fence-aware — so entry 015's **fenced**
`## Related` convention example (body content illustrating the convention) was read as
structure. Three concrete defects, all reproduced:

- `body_complement` hit the fenced header first, then asserted no `## ` sections follow —
  but 015's real sections (including its real terminal `## Related`) do follow → **crash**.
  Consequence: promote/fixer could **never** add a reciprocal into 015, and any future
  entry linking 015 broke promote's own maintenance path.
- `_related_has_target` flipped `in_related` at the fenced header, so prose `[[…]]`
  mentions after it could **silently false-dedupe** a genuinely-needed edge — the
  asymmetric, no-gate-catches-it failure
  [[023-constraint-wiki-edge-derivation-fence-aware]] warns about.
- `add_related_link`'s header check matched the fenced line, so a hypothetical entry with
  a fenced example but **no real block** would get a malformed, header-less bare line
  appended at EOF (no such entry shape exists in-corpus today; verified dormant).

This is the **third instance** of the recurring trap 023 records (detector: fence-aware
from the start; the fixer's first cut: caught in review; the editors: caught here, in
production use). 023's Implications already mandated the fix: a tool that parses the
`## Related` block itself "must be fence-aware too."

**The fix** (unit 027, panel-approved replan): a shared `_fence_flags` helper (FENCE_RE
imported from `knowledge_spans.py` per
[[019-constraint-knowledge-span-model-single-sourced]]) makes header **location**
fence-aware in all three functions — with the load-bearing nuance that fenced lines are
**never dropped from `body_complement`'s output** (they are body content under the
byte-identity guard; a naive `_strip_fences`-style content filter would have gutted the
invariant for exactly the convention-doc entries this protects). Three regression tests
in `tests/test_promote_invariant.py` cover the crash, the false-dedupe, and the
fenced-only-header cases; the 7 existing property tests pass unchanged.

## Implications

- **One dormant variant remains, deferred deliberately (not silently):**
  `add_supersede_banner`'s insert-position scan (`first SECTION_RE match`) is also raw —
  a fenced `## ` example appearing *before* the first real section would misplace a
  banner. No in-corpus entry has that shape and no supersession targets a fenced-example
  entry; fix it via the same `_fence_flags` helper when supersession machinery is next
  touched.
- When writing a tool that touches entry structure, the checklist is now four-for-four:
  the detector, the fixer's edge parser, the editors, and (pending) the banner inserter
  all need fence-aware **location** — but only *location*; content surfaces (the
  complement, the diff) must keep fenced lines.
- A convention-documenting entry (like 015) that illustrates a span with a fenced example
  is the canonical fixture for this trap — test new structure-touching tools against a
  015-shaped entry before shipping.

## Related
- [[023-constraint-wiki-edge-derivation-fence-aware]] — builds on
- [[022-decision-knowledge-fix-two-safety-models]] — see also
