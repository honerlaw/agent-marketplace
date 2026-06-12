# Proposal: skill-progressive-disclosure

**Date**: 2026-06-11
**Status**: Draft

## Goal

Cut minerva's per-run token cost, behavior-neutrally, by restructuring the nine ≥10KB skills (`propose-ship-auto`, `using-minerva`, `promote`, `init`, `debug`, `ship`, `review`, `propose`, `round-table`) into thin SKILL.md cores (≤9KB each) with on-demand per-skill `references/` files, cache-aligning `round-table`'s panel prompts, and adding a CI byte-budget + reference-pointer-integrity guard.

This is unit 1 of a 3-part token-reduction program. Unit 2 (subagent phase isolation — running heavy lifecycle phases in subagents so their context dies with them) is deferred, gated on token measurements from a real run after this unit ships. Unit 3 candidates (frontmatter-description trimming, shared cross-skill references library) are noted under Open Questions.

## Why

A `propose-ship-auto` run chain-loads ~119KB (~30K tokens) of skill prose into the main-loop session — the 31.6KB orchestrator plus every delegated skill (`propose`, `grill-plan`, `work`, `review`, `promote`, `synthesize`, `ship`, `cleanup`, `round-table`). Main-loop context is re-billed on every subsequent API call, so accumulated prose costs multiplicatively over a long lifecycle session. The orchestrator additionally double-pays each phase: its own per-phase walkthrough section plus the delegated skill's full body covering the same phase.

On the panel side, `round-table`'s three prompt templates lead with role-specific framing ("You are the Proponent…"), so the bulky shared ARTIFACT and CONTEXT blocks sit *after* the divergence point and can never share prompt cache across the three agents. CONTEXT is also specified vaguely ("relevant `.minerva/knowledge/` entries…"), leaving panel input to ad-hoc judgment.

The savings model is **late loading**, not pure avoidance: in a full auto run every phase executes, so phase references are read eventually — but bytes that enter context at the turn they're needed stop being re-billed across all earlier turns. Content that many invocations never touch (debug's failure catalogs, init's legacy-migration path, edge-case appendices) is avoided outright. The 9KB cap is additionally an anti-regrowth forcing function independent of per-skill yield.

## Approach

Behavior-neutral by construction: same gates, panels, quorums, and skip predicates; **verbatim moves only**.

1. **Progressive disclosure across the nine skills.** Each SKILL.md keeps: frontmatter, the protocol skeleton (numbered steps as one-liners with their tool calls), hard rules and gates, and explicit pointers of the form "before step N, read `references/<file>.md`". Detail prose — templates, edge-case catalogs, failure-mode appendices, worked examples, historical sections (e.g. the orchestrator's "Panel decisions 2026-05-21" log) — moves verbatim to `references/*.md` inside the same skill directory (shipped automatically with the plugin cache). Light stitching (headings, transition lines) is allowed; rewording is not. Outright deletion is permitted only for true duplicates: text that restates content which remains loaded at the same point — chiefly the orchestrator's per-phase walkthroughs that duplicate the delegated skill invoked at that phase, which shrink to invoke-and-gate.

2. **Contract checker extension.** `tests/test_skill_contracts.py` (and the contract format) gains an optional per-anchor `"file"` field, defaulting to `SKILL.md`. Each existing anchor is either kept in the thin core or deliberately retargeted to its reference file, with the rationale recorded in this unit's scratchpad. The format change is documented in `evals/README.md`, the contract format's source of truth.

3. **Byte-budget + pointer-integrity test.** A new enumerating test (same pattern as `test_skill_contracts.py`) asserts for every skill directory: (a) SKILL.md ≤ 9216 bytes; (b) every `references/*.md` file is mentioned by name in its SKILL.md; (c) every `references/` mention in SKILL.md resolves to an existing file.

4. **Round-table cache alignment.** The Proponent/Skeptic/Arbiter templates are reordered so a byte-identical shared block (ARTIFACT + CONTEXT) leads and role-specific instructions trail. CONTEXT becomes an enumerated inclusion list codifying current intent, with no size cap: the artifact under review, the framed decision, the work unit's `proposal.md` when one is in context, knowledge entries already cited this session, and repo conventions from `CLAUDE.md`/`AGENTS.md`. Savings come from prompt ordering, not from withholding input.

5. **Recorded no-ops.** Ship's CI-polling cadence (`delaySeconds: 270`) is already under the 5-minute prompt-cache TTL — confirmed, no change. No skill names change, so the catalog surfaces from [[010-constraint-minerva-skill-catalog-sync]] and [[034-constraint-site-fourth-catalog-surface]] need no edits (verified by their existing tests).

## Success criteria

- All nine SKILL.md files are ≤ 9216 bytes, enforced by the new test in CI.
- The full pytest suite is green; every pre-existing contract anchor passes — kept in the core or retargeted via the new `file` field with rationale logged in the work unit.
- The restructure diff satisfies the verbatim discipline: every deleted line has a surviving duplicate (in the delegated skill it restated, or in the moved reference text); all other moved content is byte-identical up to stitching.
- Every `references/*.md` is pointed to from a specific step in its skill's core, and every pointer resolves — both directions test-enforced.
- For any given dispatch, the three round-table prompts share a byte-identical leading ARTIFACT+CONTEXT block (role-specific text only after it), and the CONTEXT inclusion list is enumerated in the skill text.
- No gate, panel, quorum, or skip-predicate semantics changed (checkable from the diff: those passages are either untouched or moved verbatim).
- `evals/README.md` documents the per-anchor `file` field.

## Open Questions

- Per-skill reference-file taxonomy (single `references/details.md` vs. topical files like `references/phases.md` + `references/failure-modes.md`) — decided per skill during work; the pointer-integrity test is agnostic.
- Frontmatter-description trimming (the every-session cost bucket — 19 descriptions, several near 1KB) — explicitly out of scope here; candidate for a later unit since descriptions are behavior-relevant (they drive skill triggering).
- Shared plugin-level references library to dedupe cross-skill prose (worktree mechanics, default-branch resolution) — deferred; revisit only if post-restructure numbers justify the coupling.
