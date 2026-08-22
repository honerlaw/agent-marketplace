# Followups: knowledge-wiki-navigability-layer

## 2026-06-02

- **Phase B — `minerva:lint` health-check skill.** A read-mostly skill that
  health-checks `.minerva/knowledge/`: contradictions between entries, stale /
  superseded claims, orphans, `index.md` drift (watermark vs disk; missing/extra
  catalog lines), and broken `[[NNN]]` cross-ref links. Finding/triage format
  mirroring `minerva:review`; mutations gated. The navigability layer from this
  unit ([[2026-06-02-decision-knowledge-wiki-navigability-layer]]) is its prerequisite.
- **Phase C — synthesis / concept pages + `log.md`.** Roll atomic learnings into
  higher-level concept/overview pages; optional chronological ingest/lint `log.md`.
  Most speculative; design after a populated, linked index exists.
- **Full cross-reference backfill across the existing entries.** This unit seeded
  only the demo cluster (004↔010↔012) plus the 011↔017 / 012↔016 links. A
  judgment-heavy pass could add `## Related` blocks across the rest of the corpus.
  (Deferred Open Question from the proposal.)
- **Richer inverse vocabulary for `builds on`.** The closed cross-ref vocabulary
  has no inverse term for `builds on`, so its reciprocal is currently rendered as
  `see also` (see [[2026-06-02-constraint-knowledge-cross-reference-convention]]). A later
  phase could add a dedicated inverse term (e.g. `foundation for`) if the `see also`
  reciprocal proves lossy in practice.

## Backfill disposition (2026-08-22)

Triaged by `minerva:backfill-followups`. Every item above is unchanged; this section records where each one landed.

- **Phase B — `minerva:lint` health-check skill.** → shipped — `minerva:lint` exists
- **Phase C — synthesis / concept pages + `log.md`.** → shipped — `minerva:synthesize` and `overview.md` ship the synthesis half; the optional `log.md` was never pursued
- **Full cross-reference backfill across the existing entries.** → shipped — hand-authored, per `2026-06-03-decision-related-backfill-hand-authored-rename-redeferred`
- **Richer inverse vocabulary for `builds on`.** → open (low) — not filed at this pass; `knowledge_fix.py` still maps `builds on` → `see also` with a comment noting the missing inverse
