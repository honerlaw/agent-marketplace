# `minerva:lint` ships read-only; the gated fix-applier is a separate deferred unit

**Date**: 2026-06-03
**Type**: decision
**Context**: .minerva/work/2026-06-03-knowledge-lint-skill (see git history if the worktree has been cleaned up)

## Context

[[2026-06-02-decision-phase-b-deterministic-lint-detector]] recorded the first Phase-B cut —
the deterministic detector (B.1) shipped; the LLM-judged interactive `minerva:lint`
skill (B.2) was deferred — but it described B.2 as one future unit bundling
*LLM-judged detection + interactive gated fixes*. When B.2 came up for build, that
bundle was decomposed further.

## Finding

`minerva:lint` ships as a **read-only** skill (Phase B.2). It runs the frozen
detector for mechanical findings, adds the LLM-judged **advisory** dimensions
(orphans, contradictions, stale/superseded claims), and presents everything in
`minerva:review`'s finding format. It **performs no file mutation** — the gated,
span-confined fix-applier is split into a separate deferred unit (Phase B.3).

The cut is along the **read-only-vs-corpus-mutating** seam: a mutating fix-applier
is a second writer of knowledge files alongside `minerva:promote`, bound by the
span invariant in [[2026-06-02-constraint-promote-narrowed-never-overwrite]] and the span
module in [[2026-06-02-constraint-knowledge-span-model-single-sourced]]. Per
[[2026-05-31-decision-behavioral-evals-provisional]] the judged dimensions are provisional
— so building an auto-fixer on top of unvalidated judgment was deemed premature;
ship the read-only advisory pass first, validate the judged dimensions are worth
acting on, then build B.3.

## Implications

- A red knowledge-lint CI check (the B.1 gate) is now *actionable* via `minerva:lint`
  — but the skill only reports; durable repairs are made by hand or by the deferred
  B.3 gated path, never by `minerva:lint` and never via `minerva:promote` (which is
  work-unit/scratchpad-bound and has nothing to consume for a standalone corpus lint).
- **Read-only is enforced by declaration, not by the contract floor.** The skill's
  `allowed-tools:` frontmatter omits `Edit`/`Write`/`MultiEdit` (the runtime gate)
  plus a body directive. The structural-contract harness
  ([[2026-05-31-constraint-skill-structural-contracts]]) can only *witness* this via
  positive substring anchors (an `allowed-tools` frontmatter check + a `read-only`
  anchor) — it **cannot prove** a mutating tool is absent. Any future read-only
  skill relies on the same declaration-level guarantee.
- B.3 (the gated fix-applier) is the remaining Phase-B work; it consumes the same
  frozen detector and the [[2026-06-02-constraint-knowledge-span-model-single-sourced]]
  span module.

## Related
- [[2026-06-02-decision-phase-b-deterministic-lint-detector]] — builds on
- [[2026-06-03-constraint-skill-wraps-script-via-importable-api]] — see also
- [[2026-06-03-decision-knowledge-fix-two-safety-models]] — see also
- [[2026-06-03-decision-migration-check-read-only-entry-re-blindspot]] — see also
