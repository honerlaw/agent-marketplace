# Proposal: skill-progressive-disclosure

**Date**: 2026-06-11
**Status**: Shipped (2026-06-11)

## Goal

Cut minerva's per-run token cost, behavior-neutrally, by restructuring the nine ≥10KB skills (`propose-ship-auto`, `using-minerva`, `promote`, `init`, `debug`, `ship`, `review`, `propose`, `round-table`) into thin SKILL.md cores (≤9KB each) with on-demand per-skill `references/` files, cache-aligning `round-table`'s panel prompts, and adding a CI byte-budget + reference-pointer-integrity guard.

This is unit 1 of a 3-part token-reduction program. Unit 2 (subagent phase isolation — running heavy lifecycle phases in subagents so their context dies with them) is deferred, gated on token measurements from a real run after this unit ships. Unit 3 candidates (frontmatter-description trimming, shared cross-skill references library) are noted under Open Questions.

## Why

A `propose-ship-auto` run chain-loads ~119KB (~30K tokens) of skill prose into the main-loop session — the 31.6KB orchestrator plus every delegated skill (`propose`, `grill-plan`, `work`, `review`, `promote`, `synthesize`, `ship`, `cleanup`, `round-table`). Main-loop context is re-billed on every subsequent API call, so accumulated prose costs multiplicatively over a long lifecycle session. The orchestrator additionally double-pays each phase: its own per-phase walkthrough section plus the delegated skill's full body covering the same phase.

On the panel side, `round-table`'s three prompt templates lead with role-specific framing ("You are the Proponent…"), so the bulky shared ARTIFACT and CONTEXT blocks sit *after* the divergence point and can never share prompt cache across the three agents. CONTEXT is also specified vaguely ("relevant `.minerva/knowledge/` entries…"), leaving panel input to ad-hoc judgment.

The savings model is **late loading**, not pure avoidance: in a full auto run every phase executes, so phase references are read eventually — but bytes that enter context at the turn they're needed stop being re-billed across all earlier turns. Content that many invocations never touch (debug's failure catalogs, init's legacy-migration path, edge-case appendices) is avoided outright. The 9KB cap is additionally an anti-regrowth forcing function independent of per-skill yield.

## Approach

What shipped (behavior-neutral: same gates, panels, quorums, and skip predicates; verbatim moves):

1. **Progressive disclosure across the nine skills.** Each ≥10KB SKILL.md was split into a thin core (frontmatter, protocol skeleton, hard rules/gates, mandatory read-before-step pointers) plus per-skill `references/*.md` holding the detail prose verbatim — propose-ship-auto (31.6KB→8.0KB; panel-protocol/phases/governance references), using-minerva (→8.4KB; guide), promote (→4.2KB; modes, wiki-maintenance), init (→3.5KB; steps), debug (→4.7KB; workflow), ship (→3.3KB; protocol), review (→3.1KB; protocol), propose (→5.9KB; on-approval), round-table (→7.7KB; briefs, caller-mode). The nine cores total 53.3KB vs 137.7KB before (−61%). Zero original lines were lost in eight skills; the anticipated orchestrator dedupe proved unnecessary (its inlined phases are the executable spec, so everything moved rather than deleted).

2. **Contract checker extension.** `tests/test_skill_contracts.py` gained the optional per-anchor `"file"` field (validated keys, dangling-target failure); 25 anchors were deliberately retargeted with rationale logged. Documented in `evals/README.md`, the format's source of truth.

3. **Byte-budget + pointer-integrity test.** `tests/test_skill_budget.py` enumerates all skill directories: SKILL.md ≤9216 bytes, every `references/*.md` mentioned from its core, every mention resolving. Wired into `.github/workflows/evals.yml`'s enumerated pytest list after the completion panel caught it missing (see replan.md).

4. **Round-table cache alignment** — the one sanctioned content edit: prompts now lead with a byte-identical shared ARTIFACT+CONTEXT block (role briefs trail, in `references/briefs.md`), and CONTEXT is an enumerated no-cap inclusion list (framed decision/goal, the unit's proposal.md when in context, session-cited knowledge entries, CLAUDE.md/AGENTS.md conventions).

5. **Recorded no-ops.** Ship's 270s CI-polling cadence was already cache-aligned; no catalog surfaces changed.

Knowledge promoted: [[2026-06-11-constraint-ci-test-enumeration-explicit]], [[2026-06-11-constraint-skill-progressive-disclosure]].

## Success criteria

- All nine SKILL.md files are ≤ 9216 bytes, enforced by the new test in CI.
- The pytest suite is green (excluding `tests/test_browser.py`, `tests/test_storage.py`, and `tests/test_pull.py`, broken on main by the deleted financials tooling — see replan.md); every pre-existing contract anchor passes — kept in the core or retargeted via the new `file` field with rationale logged in the work unit.
- The restructure diff satisfies the verbatim discipline: every deleted line has a surviving duplicate (in the delegated skill it restated, or in the moved reference text); all other moved content is byte-identical up to stitching.
- Every `references/*.md` is mentioned by name in its skill's core and every `references/` mention resolves — both directions test-enforced; in practice each core points at its references from mandatory read-before-step instructions (spot-checked, not test-enforced).
- For any given dispatch, the three round-table prompts share a byte-identical leading ARTIFACT+CONTEXT block (role-specific text only after it), and the CONTEXT inclusion list is enumerated in the skill text.
- No gate, panel, quorum, or skip-predicate semantics changed (checkable from the diff: those passages are either untouched or moved verbatim).
- `evals/README.md` documents the per-anchor `file` field.

## Open Questions

- Per-skill reference-file taxonomy (single `references/details.md` vs. topical files like `references/phases.md` + `references/failure-modes.md`) — decided per skill during work; the pointer-integrity test is agnostic.
- Frontmatter-description trimming (the every-session cost bucket — 19 descriptions, several near 1KB) — explicitly out of scope here; candidate for a later unit since descriptions are behavior-relevant (they drive skill triggering).
- Shared plugin-level references library to dedupe cross-skill prose (worktree mechanics, default-branch resolution) — deferred; revisit only if post-restructure numbers justify the coupling.
