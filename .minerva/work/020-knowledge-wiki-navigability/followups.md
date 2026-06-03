# Followups: knowledge-wiki-navigability-layer

## 2026-06-02

- **Phase B — `minerva:lint` health-check skill.** A read-mostly skill that
  health-checks `.minerva/knowledge/`: contradictions between entries, stale /
  superseded claims, orphans, `index.md` drift (watermark vs disk; missing/extra
  catalog lines), and broken `[[NNN]]` cross-ref links. Finding/triage format
  mirroring `minerva:review`; mutations gated. The navigability layer from this
  unit ([[017-decision-knowledge-wiki-navigability-layer]]) is its prerequisite.
- **Phase C — synthesis / concept pages + `log.md`.** Roll atomic learnings into
  higher-level concept/overview pages; optional chronological ingest/lint `log.md`.
  Most speculative; design after a populated, linked index exists.
- **Full cross-reference backfill across the existing entries.** This unit seeded
  only the demo cluster (004↔010↔012) plus the 011↔017 / 012↔016 links. A
  judgment-heavy pass could add `## Related` blocks across the rest of the corpus.
  (Deferred Open Question from the proposal.)
- **Richer inverse vocabulary for `builds on`.** The closed cross-ref vocabulary
  has no inverse term for `builds on`, so its reciprocal is currently rendered as
  `see also` (see [[015-constraint-knowledge-cross-reference-convention]]). A later
  phase could add a dedicated inverse term (e.g. `foundation for`) if the `see also`
  reciprocal proves lossy in practice.
