# Followups: skill-best-practices-audit

Mechanism findings and deferred items from `findings.md` — seeds, not commitments.

## Mechanism seeds (from the audit, not built in this unit)

1. **[M1, high] Rendered-listing description drop.** `minerva:lint` and
   `minerva:lint-fix` render as bare names (no description) in live session skill
   listings despite valid frontmatter everywhere on disk; one session also observed
   `minerva:replan` bare. A bare name cannot win an ambient trigger decision.
   Diagnose the listing/registration pipeline (cache invalidation, listing budget,
   frontmatter handling — formatting is byte-identical in kind to skills that render
   fine, so simple YAML issues are ruled out) and add a contract test that renders
   the plugin's skill listing and asserts every description survives non-empty.
   Until fixed, the corrected lint/lint-fix descriptions cannot take effect.
2. **[M2] Six-block target-resolution duplication.** The 5-step target-resolution
   block is copy-pasted across work/replan/review/promote/ship/cleanup with sync
   maintained only by a "keep all six blocks in sync" plea (and wording has already
   drifted). Extract to a shared reference or add a normalized-diff contract test.
3. **[M3] Cross-skill step-number coupling.** quick's and balanced's `phases.md`
   reference sibling skills by internal step numbers ("per `minerva:propose` steps
   8–9, 11", "Hard gate #1/#2"); renumbering a sibling silently breaks them. Prefer
   named anchors plus a contract test asserting referenced sections exist.
4. **[M4] Description ≤1024-char contract test.** Three descriptions were over the
   documented frontmatter limit (fixed in this unit as prose); a mechanical test
   keeps the ceiling from regressing.
5. **Handoff-phrasing contract test.** This unit standardized every skill-to-skill
   handoff on "invoke X via the `Skill` tool (+ argument)". Nothing enforces the
   pattern for future skills — the recurrence risk documented in
   [[030-pattern-rejected-alternative-reinvented-at-runtime]] applies. A lint over
   `minerva:<name>`-mentioning imperative sentences could hold the line.
6. **Ambient-trigger enforcement layer.** The audit's prose fixes improve the odds,
   but ambient triggering still rides on the harness surfacing descriptions.
   Evaluate a SessionStart-hook layer (as superpowers uses) and/or init-template
   Routing-section changes — the latter explicitly scoped out of this unit because
   the Routing section is a template-of-record with distribution-wide blast radius.
7. **Empirical validation of the triggering diagnoses.** Both anchor diagnoses are
   analytic (confidence labels in `findings.md`). Validate against captured session
   transcripts / PostHog LLM analytics: measure ambient-trigger hit rate before/after
   this unit's description changes.
8. **Mechanized rubric checks.** The audit's deterministic census (invokes-first
   ordering, description length, body line counts) could run in CI — the
   "approach 3" idea deliberately deferred at proposal time.

## Declined in this unit (recorded, low priority)

- **C11 TOC pass** over 8 >100-line reference files — all are under read-in-full
  contracts or mapped from their SKILL.md; batch change judged diff-noise. Optional.
- **C12 governance/protocol dedup** in quick + balanced (triple-stated triggers /
  counter / scope-fit escape, already drifting) — structural refactor touching byte
  budgets and contract anchors; do as its own unit.
- **ScheduleWakeup portability note** — the reviewer claim that the tool is missing
  was wrong for this harness, but orchestrators could state a fallback (background
  poll with the same retry cap) for harnesses that lack it.
- **Internal script docstrings carry old phase vocabulary** (`scripts/knowledge_lint.py` "Phase B.2", `scripts/knowledge_fix.py` "(Phase B.3)") — not user-facing catalog surfaces, but the same retired vocabulary this unit scrubbed elsewhere; scrub opportunistically.
