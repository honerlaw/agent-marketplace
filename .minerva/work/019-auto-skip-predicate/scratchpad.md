# Scratchpad: auto-skip-predicate

Live working notes for this unit. Promoted to durable knowledge (or discarded) at `minerva:promote`.

## Decisions

## Surprises

## Open threads

## Panel decisions 2026-05-31

- [3/3 accept] scope check: single work unit (in-skill edit + conditional contract/catalog satellites are same-commit by knowledge 010/012; no independently-shippable seam)
- [1/3 accept → revised → 3/3 accept] approach selection: option A′ (in-skill per-decision skip predicate). Round 1 rejected the original (Phase 0 sizing panel + dual-mode + `--fast` flag) as self-defeating (a panel to decide whether to skip panels) and too coarse; folded toward a per-decision cheap predicate that fails closed into the existing panel.
- [2/3 accept → revised → 3/3 accept] whole-proposal acceptance. Round 1 Skeptic surfaced two load-bearing gaps (New-plan acceptance + Replan-vs-FIX rows omitted from the "Skippable?" enumeration, contradicting the every-row criterion); revised to a unified never-skippable rule covering all four post-divergence/self-check panels, plus rejected-alternatives logging and the promote-invisibility statement.

### Work-phase notes carried from the panels
- Arbiter (whole-proposal): the skip is a **main-LLM unilateral judgment** — the one decision in the taxonomy with no second agent checking it. Mitigated by the "mechanical evidence" clause, but each skip line MUST record its concrete evidence string so a later review/promote can audit that the predicate is honored, not rubber-stamped.
- Approach clause must be written as an **action** ("did I enumerate ≥2 viable approaches, one strictly dominant") not a self-judgment ("no alternative exists") — the latter reintroduces the detector==suspect gameability.
