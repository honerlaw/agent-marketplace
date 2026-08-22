# Followups: knowledge-lint-fix

## 2026-06-03

- **Phase C — synthesis / concept pages + `log.md`.** The last phase of the LLM-wiki
  effort. Roll the atomic `.minerva/knowledge/` entries up into higher-level
  concept/overview pages (a readable synthesis layer over the atoms), and optionally
  add a chronological `log.md` (ingest / lint / fix timeline). Most speculative of
  the phases; design it once the navigable + maintained wiki (Phases 1, B.1–B.3) has
  accreted more entries. Any edge-deriving tooling it adds must be fence-aware
  ([[2026-06-03-constraint-wiki-edge-derivation-fence-aware]]) and reuse the single-sourced
  span model ([[2026-06-02-constraint-knowledge-span-model-single-sourced]]).
- **Missing-catalog-line auto-fix (deferred from B.3).** The fixer leaves
  "entry has no catalog line" unrepaired because the catalog line needs a ≤15-word
  summary (a judgment call). A future LLM-assisted path could draft the summary and
  let the deterministic serializer insert the line; kept out of the deterministic
  fixer to preserve its testability.

## Backfill disposition (2026-08-22)

Triaged by `minerva:backfill-followups`. Every item above is unchanged; this section records where each one landed.

- **Phase C — synthesis / concept pages + `log.md`.** → shipped — `minerva:synthesize` exists
- **Missing-catalog-line auto-fix (deferred from B.3).** → shipped — `knowledge_fix` writes catalog lines from each entry's `**Summary**` field
