# Scratchpad: derive-knowledge-aggregates

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `minerva:promote`: significant items get promoted to
> `.minerva/knowledge/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.

## Decisions 2026-10-01
- [solo] pre-flight: no collision — no in-flight units, no open PRs/issues; feat/codex + stale local minerva/reconcile unrelated (tier: hardcoded check, clean)
- [reviewed — folded] scope check: one unit, one PR, no phases; folded size/risk-tradeoff rationale, 3.0.0 + COMPATIBILITY.md deprecation story, reconciliation-era entry supersession list (tier: reviewer — not provably small; parallel wave; Skeptic's "Panel warranted?" named interface/blast-radius clauses, which were the approach panel's surface, and ambiguity on phasing, ruled out: phasing adds a throwaway intermediate state and does not reduce deletion/migration risk)
- [rechecked — residual folded] scope check: items 3 (old/new plugin coexistence) and 4 (supersedes double-edge, slug collision) partially addressed — residual not load-bearing for the one-PR decision; folded date-keyed lint enforcement + mixed-version statement + awk test
- [panel — 3/3 accept, 3 with fixes] approach: option A — derive every aggregate on read, Theme on the entry, delete reconcile/synthesize/lint-fix (tier: panel — existing interface change: removes skills, cleanup behaviour, routing contract; knowledge tension: supersedes 2026-08-05/2026-06-02/2026-06-03 decisions; parallel wave)
    - fix: criterion 4 vs step 7 — knowledge_fix.py becomes a non-zero-exit tombstone; 3.0.0 + COMPATIBILITY.md
    - fix: supersession = union of supersedes edges, legacy superseded-by edges, legacy banners
    - fix: Theme/Summary error for new entries, warning for older; singleton-theme warning; --themes at promote
    - fix: measured catalog size (119 lines, 23.4 KB, ~5.9k tokens)
    - fix: Theme normalisation (single-valued kebab-case), backfill idempotent, migrate detects migrated state
    - fix: stale-reference test covers .minerva/reference/ if present; consumer fallout in PR body + COMPATIBILITY.md; legacy reconciliation phase read kept
- [reviewed — clean] whole-proposal (first wave): discarded as stale — restart (tier: reviewer; parallel wave)
- [reviewed — folded] whole-proposal (restart): approach/scope folds rewrote Success criteria; re-reviewed accept; folded knowledge_rename.py legacy handling, migration_status polarity inversion, both plugin manifests, awk-vs-catalog test (tier: reviewer — interface/knowledge clauses already approved by the approach panel)
- [rechecked — clean] whole-proposal: fold-audit addressed 1–8; new concerns (cutoff date source, mixed-version wording) folded as clarifications
