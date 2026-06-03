# The knowledge-wiki fixer uses two safety models, one per object type — entry byte-identity vs index skeleton-preservation

**Date**: 2026-06-03
**Type**: decision
**Context**: .minerva/work/023-knowledge-lint-fix (see git history if the worktree has been cleaned up)

## Context

Phase B.3 added `minerva:lint-fix` — the gated, mutating companion to the read-only
`minerva:lint` ([[020-decision-minerva-lint-read-only]]) — which applies the
mechanically-repairable findings the detector surfaces (index watermark, stale
catalog line, wrong Type section, missing reciprocal). All mutation lives in a
deterministic, unit-tested script (`scripts/knowledge_fix.py`); the skill only
orchestrates and gates (Bash-only, no `Edit`/`Write`) — chosen over an LLM-`Edit`
fixer (untestable span-confinement) and over a `--fix` mode on read-only `lint`
(would violate 020). Completing that loop surfaced a non-obvious design point worth
recording.

## Finding

**The fixer needs two *different* safety models because its edits span two object
types, and a single "span-confined" guard is incoherent across them:**

- **Entry edits** (the missing-reciprocal fix, which adds a `## Related` line and/or
  a supersession banner) are guarded by **`body_complement` byte-identity**: every
  byte outside the `## Related` block and the banner span is unchanged
  ([[016-constraint-promote-narrowed-never-overwrite]]). Validated for *every* entry
  edit **before any write**, so a bad edit aborts the run with nothing on disk.
- **Index edits** (watermark / stale-line removal / wrong-Type relocation) touch
  `index.md`, which has **no** `## Related`/banner spans — so `body_complement` does
  not apply. They are guarded instead by a **skeleton-preserving canonical
  serializer**: the `# Knowledge index` H1, the four Type headers (including the
  deliberately-empty `## Patterns`), and ascending-NNN order are all preserved; no
  entry file is touched. The serializer never drops a catalog line it can't confidently
  place (an unknown declared-type is left in place and refused, never deleted) and
  refuses to fabricate a hollow index from a missing/empty one (it has no summaries
  to author — that's `minerva:promote`'s / a human's job).

The original framing tried to call the whole fixer "span-confined"; that was
incoherent for the index families and had to be split into these two guards.

## Implications

- Any future wiki *mutator* must pick the right guard per object type: entry edits →
  `body_complement` byte-identity; `index.md` edits → skeleton/NNN-order
  preservation. Don't apply the entry span model to the index.
- The fixer **recomputes the edit batch from the live corpus at apply time** (not
  from a stale dry-run plan), applies atomically after pre-write validation, then
  re-runs the detector to verify clean.
- The span *editors* (`add_related_link` / `add_supersede_banner` / `body_complement`)
  were single-sourced into `scripts/knowledge_edits.py` so the fixer and the
  promote-invariant guard share one implementation — an application of
  [[019-constraint-knowledge-span-model-single-sourced]], not a new rule. The
  genuinely new seam: **index-editing logic lives in `scripts/knowledge_fix.py`
  (fixer-specific), not in the entry-span-scoped `knowledge_edits.py`** — only the
  fixer mechanically rewrites `index.md`.
- Phase B (detect → report → fix) is complete; only Phase C (synthesis / concept
  pages + `log.md`) remains.

## Related
- [[020-decision-minerva-lint-read-only]] — builds on
- [[023-constraint-wiki-edge-derivation-fence-aware]] — see also
- [[028-bug-knowledge-edits-not-fence-aware]] — see also
