# Scratchpad: knowledge-wiki-navigability-layer

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `minerva:promote`: significant items get promoted to
> `.minerva/knowledge/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.

## Panel decisions 2026-06-02

- [escalated to user] pre-flight: in-flight unit 015-init-content-backfill (promoted, never merged) overlaps init/Routing/catalog surfaces → user chose "abandon 015, absorb reference-dir scaffolding into Phase 1"; 015 branch tag-archived as `archive/015-init-content-backfill`, worktree+branch removed.
- [2/3 accept, skeptic dissented → revise] scope check r1: single unit (skeptic: `.minerva/reference/` scaffolding looked like a foreign concern)
- [3/3 accept] scope check r2: single unit (added provenance note tying reference scaffolding to entry-011/unit-014 followup + user-directed 015 absorption)
- [1/3 accept → revise] approach selection r1: approach X (index-mediated cross-refs) — skeptic+arbiter: index recall hole (index.md doesn't exist yet → zero recall), breaks promote:82 never-overwrite, forks live `[[NNN]]` convention
- [3/3 accept] approach selection r2: approach X′ — grep-all corpus scan is the recall floor (index = optional pre-filter via watermark, not a gate); never-overwrite narrowed to body-append-only with idempotent `## Related`/banner edits; reuse `[[NNN]]` keyed on stable NNN; +max-NNN watermark, NNN-dedup, coupled reciprocal approval
- [1/3 accept → revise] whole-proposal r1: skeptic+arbiter: line-53 gate anchor is Mode-A-only/fragile; two index.md creators lack a shared skeleton; Mode B behavior unspecified; never-overwrite invariant doc-only/unguarded
- [2/3 accept] whole-proposal r2: skeptic raised new MEDIUM #A (byte-guard test needs two delimited spans, not one) + LOW B/C/D — all folded into proposal; proponent+arbiter accept, escalation trigger (≤1/3) not met → accepted

## Concerns carried forward (from panels)

- Guard test must delimit BOTH mutable spans (banner span via `<!-- superseded-by: NNN -->`; `## Related`→EOF) and assert byte-identity of the complement, incl. a Mode-A-over-already-linked-pair zero-diff case. (folded into proposal §5)
- index.md has two creators (init scaffold, promote create-if-absent) — both MUST emit the single canonical skeleton verbatim. (folded into proposal §Approach)
