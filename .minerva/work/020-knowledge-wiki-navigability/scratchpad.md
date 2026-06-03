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

## Implementation log 2026-06-02

- promote/SKILL.md: added `## Related` + banner to the knowledge template; narrowed the "never overwritten" idempotency line to body-append-only with `## Related`/banner the sole mutable surfaces; added a "Wiki maintenance (index + cross-references)" section (canonical skeleton, recall-complete corpus-scan discovery with index-as-pre-filter-when-watermark-fresh, coupled reciprocal approval, NNN-keyed idempotency); wired it into Mode A (gate step 6 / write step 7) and Mode B (gate step 4 / write step 5, scoped to the single entry).
- init/SKILL.md: Step 1 scaffolds index.md (canonical skeleton, watermark 000) + `.minerva/reference/`+.gitkeep; knowledge `.gitkeep` only when index.md absent; added Step 1b index-backfill offer (idempotent mode); Routing template mentions index.md + reference/; detection window 4→6; commit-offer + status-block updated.
- using-minerva/SKILL.md: persistence hierarchy gains the reference tier + the navigable-knowledge-wiki paragraph (index, `## Related`, vocab, banners, inline coexistence).
- evals/init/contract.json: +anchors `.minerva/reference/`, `index.md`, `index-watermark`, any_of[backfill]. evals/promote/contract.json: +anchors `## Related`, `index-watermark`, `[[`, any_of[cross-reference/wiki maintenance].
- tests/test_promote_invariant.py: reference span-editor (add_related_link / add_supersede_banner / body_complement) + 6 property tests proving body-complement byte-identity + idempotency + already-linked zero-diff. Added to the evals.yml CI gate.
- Dogfood: .minerva/knowledge/index.md generated (watermark 014, 14 entries); seeded 004↔010↔012 `## Related` cluster (builds on / see also).

### Implementation note (not a load-bearing divergence)
- minerva skills are prose executed by an LLM, not Python — so #8's "byte-guard test" can't invoke a `promote()` function. Implemented it as a reference span-editor + property tests serving as the executable spec the SKILL.md prose mirrors. Satisfies the criterion's substance (mechanical enforcement of the narrowed invariant). The SKILL.md is the runtime contract; the test is the spec-of-record for the span boundaries.
- Relationship vocab is not fully symmetric: `supersedes`↔`superseded by` is the directional pair, `contradicts`/`see also` are symmetric, but `builds on` has no inverse term — reciprocal of a `builds on` edge is rendered as `see also` (used in the 004 dogfood). Acceptable; noted in case a future entry wants a richer inverse.
- Pre-existing: tests/test_browser.py + tests/test_storage.py fail collection (`No module named 'lib'`); known on main, CI (evals.yml) deliberately scopes around them. Untouched by 020.

## Panel decisions 2026-06-02 (continued)

- [3/3 accept] completion verification: all 9 success criteria honestly met; both panelists + arbiter independently ran the gated suite (95 passed) and re-proved the invariant guard is non-vacuous (body-tamper detected, anchors load-bearing)
- [skipped — small] review triage: all 3 review findings LOW severity (evidence: reviewer rated each low; actionable ones touch only tests/test_promote_invariant.py — additive, no new interface, no knowledge-constraint violation) → main LLM triaged directly without a panel

## Review finding 2026-06-02

Review ran 3 lenses; spec-fidelity + knowledge-compliance clean, 3 LOW quality findings:
1. body_complement assumed `## Related` is terminal without asserting it → FIXED: added an assertion + `test_related_must_be_terminal_section` so the guard can't go vacuous if a future entry puts a body section after `## Related`.
2. add_supersede_banner on a (degenerate) entry with no `## ` section omits a blank separator → documented out of scope (real entries always have `## Context`; the template guarantees it).
3. demo cluster reciprocal labels asymmetric (`builds on` ↔ `see also`) → IGNORE: intentional; the vocab has no inverse for `builds on`, reciprocal rendered as `see also`. Carried as a Phase-B consideration (richer inverse vocab).
