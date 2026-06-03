# The knowledge-wiki synthesis layer is a SEPARATE `overview.md` with a new-scope-only watermark; its content is advisory (never CI-gated)

**Date**: 2026-06-03
**Type**: decision
**Context**: .minerva/work/024-synthesize-skill (see git history if the worktree has been cleaned up)

## Context

Phase C of the LLM-wiki effort ([[017-decision-knowledge-wiki-navigability-layer]]) adds
the **synthesis layer** Karpathy's pattern calls concept/overview pages — an LLM-owned
read *across* entries that surfaces cross-cutting themes. Unit 024 shipped the
`minerva:synthesize` capability (a deterministic `scripts/synthesis_status.py` signal +
the self-gating skill) and dogfooded it to produce the first `overview.md`. This entry
records the design decisions; the un-synthesized-scope mechanics live in the script and
the skill, not here.

## Decision

**The synthesis layer is a SEPARATE `.minerva/knowledge/overview.md` file — never a
section inside `index.md`.** A `## Themes`-in-`index.md` design was rejected: the fixer
(`scripts/knowledge_fix.py`) rebuilds `index.md` from only its four `## Decisions /
## Bugs / ## Patterns / ## Constraints` sections, so an embedded synthesis section would
be silently clobbered. A separate file that does **not** match `ENTRY_RE` is invisible to
both the frozen detector and the fixer, so the synthesis layer adds nothing to the CI
floor and **unfreezes no shipped tool**.

**`overview.md` carries a `<!-- synthesis-watermark: NNN -->` that is a deterministic,
NEW-SCOPE-ONLY signal**, distinct from `index.md`'s `index-watermark` (which must always
equal max NNN — an integrity invariant). The synthesis watermark deliberately *lags* max
NNN; the lag (entries with `NNN > watermark`) is the "un-synthesized scope" the LLM uses
to decide **IF** a (re)synthesis is warranted. It is a *floor*, not the whole staleness
story: it detects **added** entries, not in-place `## Related` / banner / body edits to
already-synthesized entries (that drift is a judgment call for the skill), and it attests
synthesis **intent, not body content**.

**The overview's content is advisory — never CI-gated** ([[013-decision-behavioral-evals-provisional]]).
Theme grouping and narrative are LLM-judged. The one mechanical part — `[[NNN-type-slug]]`
**link-rot** (a link whose NNN matches no live entry) — *is* deterministic and is the same
class of defect the detector CI-gates for entry `## Related` links, so it could in
principle be gated; it is **deliberately kept advisory** (surfaced by the skill, repaired
on the next synthesis) because the overview is a navigation aid, not a corpus-integrity
invariant. 013's mechanical-vs-judged exemption *permits* gating it — leaving it advisory
is a deliberate scoping choice, not a 013 prohibition.

## Implications

- Keep synthesis confined to the `overview.md` file. A future synthesis that **rewrites
  entry bodies** would reintroduce the [[016-constraint-promote-narrowed-never-overwrite]]
  never-overwrite hazard; `overview.md` escapes 016 only because it is a brand-new owned
  file that is regenerated wholesale, not an existing entry.
- The synthesis tooling is an edge-deriving reader, so it obeys
  [[023-constraint-wiki-edge-derivation-fence-aware]]: `synthesis_status.py` reuses the
  detector's `_strip_fences` / `ENTRY_RE` / `WIKILINK_RE` and enumerates entries via the
  `ENTRY_RE` glob — **not** `parse_index`, which reads only `index.md`'s Type-section
  catalog and would report a *false* clean against a theme-grouped overview.
- `minerva:synthesize` is currently a manually invoked maintenance skill; wiring it into
  `minerva:propose-ship` / `minerva:propose-ship-auto` as a self-gating post-promote step
  is a deferred follow-up unit.

## Related
- [[017-decision-knowledge-wiki-navigability-layer]] — builds on
- [[013-decision-behavioral-evals-provisional]] — see also
- [[023-constraint-wiki-edge-derivation-fence-aware]] — see also
- [[025-decision-synthesize-wired-post-promote-self-gating]] — see also
- [[029-decision-routing-section-is-the-wiki-reading-protocol]] — see also
