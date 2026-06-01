# Scratchpad: auto-skip-predicate

Live working notes for this unit. Promoted to durable knowledge (or discarded) at `minerva:promote`.

## Decisions

- Resolved the `description:` open question to **yes, light touch + catalog sync** (the proposal's lean) — added one sentence to the frontmatter and synced all three catalog rows (plugin README, using-minerva matrix, root README) per knowledge 010. Discoverability of a user-facing capability won over minimal-diff.
- Triage skip bar resolved to **any medium+ forces the panel** (the stricter fail-closed reading), baked into the taxonomy row.
- Defined the skip predicate **once** in the Panel protocol section (it is "used at every strategic/tactical decision point") rather than editing each of Phases 1–4 — honors the no-logic-duplication ethos and avoids bloating every phase. The taxonomy `Skippable?` column is the canonical per-decision reference.

## Surprises

- None load-bearing. Implementation matched the approved proposal exactly; no divergence, no replan triggered.
- `tests/test_browser.py` and `tests/test_storage.py` fail to collect (`No module named 'lib'`) — pre-existing environment issue unrelated to this markdown-only change. Skill-relevant suites (test_skill_contracts, test_minerva, test_skill_evals) all pass (89).

## Open threads

## Panel decisions 2026-05-31

- [3/3 accept] scope check: single work unit (in-skill edit + conditional contract/catalog satellites are same-commit by knowledge 010/012; no independently-shippable seam)
- [1/3 accept → revised → 3/3 accept] approach selection: option A′ (in-skill per-decision skip predicate). Round 1 rejected the original (Phase 0 sizing panel + dual-mode + `--fast` flag) as self-defeating (a panel to decide whether to skip panels) and too coarse; folded toward a per-decision cheap predicate that fails closed into the existing panel.
- [2/3 accept → revised → 3/3 accept] whole-proposal acceptance. Round 1 Skeptic surfaced two load-bearing gaps (New-plan acceptance + Replan-vs-FIX rows omitted from the "Skippable?" enumeration, contradicting the every-row criterion); revised to a unified never-skippable rule covering all four post-divergence/self-check panels, plus rejected-alternatives logging and the promote-invisibility statement.

### Work-phase notes carried from the panels
- Arbiter (whole-proposal): the skip is a **main-LLM unilateral judgment** — the one decision in the taxonomy with no second agent checking it. Mitigated by the "mechanical evidence" clause, but each skip line MUST record its concrete evidence string so a later review/promote can audit that the predicate is honored, not rubber-stamped.
- Approach clause must be written as an **action** ("did I enumerate ≥2 viable approaches, one strictly dominant") not a self-judgment ("no alternative exists") — the latter reintroduces the detector==suspect gameability.
