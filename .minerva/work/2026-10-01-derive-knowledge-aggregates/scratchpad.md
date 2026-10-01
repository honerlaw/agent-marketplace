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
- [reviewed — clean] completion verification: Verifier reproduced all 12 criteria (1079 tests pass); noted the stale-reference regex is deliberately narrower than the proposal's `reconcil|synthesi[sz]` wording (generic "design synthesis"/"reconcile the wave" are not knowledge reconciliation) (tier: reviewer floor — no interface change beyond what the approach panel approved)
- [solo] review triage: 9 FIX / 0 SUGGEST / 0 IGNORE (tier: default-solo row — every finding had a writable failure scenario and an absorbable fix; none had two defensible dispositions. #3 (late-upgrader errors) considered code-change vs docs-accuracy: the date key was a panel-approved choice, so correcting the docs' over-promise is dominant)

## Work notes 2026-10-01
- overview.md was corrupted on main: a "Silent success" paragraph had been pasted into the intro mid-sentence (`see \`Three later findings…`), leaving 9 entries linked from no theme section. Backfill reported them unthemed; assigned `silent-success` by hand (their prose is that cluster). Evidence for the decision entry: a wholesale LLM rewrite of a shared aggregate rots silently.
- Theme names after backfill shortened by hand: lifecycle-and-its-automation→lifecycle, skills-plugins-and-catalogs→skills-and-catalogs, git-worktrees-and-promote-scratchpad-mechanics→worktrees-and-promote. 7 themes, 119 entries, catalog ~24.7 KB.
- Own mistake: a hand-assign loop used `open(p,'w').write(f(open(p).read()))` — the write-open truncates before the read, wiping 9 files. Restored from `git show HEAD:` and redone. Pattern-worthy? It is a generic Python footgun, not minerva knowledge — discard.
- init routing template now nests a ```sh block, so the template's own fence became `~~~markdown` (an inner ``` line at ≤3-space indent would close an outer ``` fence).
- migration_status found this repo's AGENTS.md still routed to overview/index — updated to the template (copy of CLAUDE.md).
- knowledge_edits.py was also used by test_promote_invariant's editor property tests; those tests went with it (the editors have no caller once entries are write-once).
- compatibility eval scenario `reconciliation` repurposed as `merged-cleanup` (worktree removed, no reconcile PR, shipped entry preserved, no legacy aggregates).

## Review triage 2026-10-01
Independent diff review (9 findings), all FIX:
1. [medium] catalog marked live 2026-06-13 constraint superseded by OLDER 06-10 (mislabelled `supersedes`) → relabelled 06-10's edge `superseded by:`; catalog ignores an inverted `supersedes` (`inverted_supersedes`), lint warns (`supersession` family). Tests added.
2. [medium] routing one-liner blind to supersession → awk now marks `(superseded)` from all three sources with the same inverted guard; parity test pinned on a fixture exercising each source.
3. [medium] date cutoff errors on a late-upgrading 2.x consumer's post-cutoff entries; docs claimed "stays green" → docs corrected (upgrading.md, COMPATIBILITY.md, lint SKILL) and lint message points at migrate-fix / hand-writing. Behaviour kept (loud by design, panel-approved key).
4. [low] backfill inserted above frontmatter → inserts after closing `---`. Test.
5. [low] backfill rewrote CRLF → newline="" + file's own EOL. Test.
6. [low] gate asked to show derived themes the dry run never printed → dry run prints heading→theme map (shared `_overview_sections`). Test.
7. [low] zsh aborts on empty glob; awk read theme as $2; CRLF → `find … -exec awk … {} +`, whole-line theme, `\r` stripped. Tests (sh+zsh empty corpus; CRLF + multi-word theme in parity fixture).
8. [low] cleanup advised `git branch -d minerva/reconcile` (refuses on squash-merge) → check no open PR, then `-D`.
9. [low] stale prose: knowledge_rename docstring (lint-fix), lint SKILL "stale-slug" example → fixed.
