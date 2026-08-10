# Followups: minerva-lint-skill

## 2026-06-03

- **Phase B.3 — the gated, span-confined, idempotent fix-applier.** The mutating
  half deferred from B.2 (see [[2026-06-03-decision-minerva-lint-read-only]]). Likely an
  extension of `minerva:lint` (or a sibling) that, behind a confirmation gate,
  applies the mechanical repairs the detector surfaces — index repair (missing
  catalog line / watermark / Type-section) and missing-reciprocal `## Related`
  insertion — editing only within the `## Related` / banner spans per
  [[2026-06-02-constraint-promote-narrowed-never-overwrite]]. It must import the span
  constants from `scripts/knowledge_spans.py`
  ([[2026-06-02-constraint-knowledge-span-model-single-sourced]]), follow the
  importable-API + `git rev-parse --show-toplevel` anchoring rule
  ([[2026-06-03-constraint-skill-wraps-script-via-importable-api]]), and **amend** (not
  rewrite) `evals/lint/contract.json`. Judged (advisory) findings stay
  never-auto-applied per [[2026-05-31-decision-behavioral-evals-provisional]].
- **Duplicate-NNN detection in the detector** (carried from unit 021's followups) —
  still open; can't occur in a promote-managed corpus, so low priority.
