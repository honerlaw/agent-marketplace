# A third orchestrator decides solo: propose-ship-quick has the main model adjudicate, escalating fail-closed

**Date**: 2026-06-16
**Type**: decision
**Context**: .minerva/work/042-add-propose-ship-quick (see git history if the worktree has been cleaned up)

## Context

`minerva:propose-ship` runs the lifecycle with human gates; `minerva:propose-ship-auto` replaces those gates with 3-agent `minerva:round-table` panels. Both are heavy for a small UI fix or bug fix: human gates stall, panels cost subagent dispatches and wall-clock. Work unit 042 added `minerva:propose-ship-quick`, a third orchestrator that runs the same lifecycle (propose → work → review → promote → synthesize → ship → cleanup) but has the **main model adjudicate every strategic/tactical decision directly** — no panel — for changes small enough that its own judgment suffices.

## Finding

The three orchestrators form a **ladder by adjudication cost**: `propose-ship` (human gates) · `propose-ship-quick` (main model decides) · `propose-ship-auto` (consensus panels). Pick by how much independent scrutiny the change warrants, not by lifecycle shape — the lifecycle is identical across all three.

The mechanism that distinguishes `-quick` is a **fail-closed escalation predicate** that is the *structural inverse* of `-auto`'s skip predicate (see [[014-decision-per-decision-skip-over-sizing-gate]]):

- `-auto`'s skip predicate is fail-open toward *deciding-without-a-panel*: the panel is the default, and the main LLM skips it only when every clause holds.
- `-quick`'s escalation predicate is fail-open toward *deciding-alone*: deciding directly is the default, and the main model escalates to the user only when a clause holds — genuine ambiguity (no dominant option), high blast-radius/irreversibility, an unfamiliar public interface/cross-cutting contract, or a `.minerva/knowledge/` conflict — or on any doubt.

Both fail toward the more conservative reviewer; they just start from opposite defaults. The user-escalation path is preserved in `-quick` exactly as panel-escalation works in `-auto` (same hardcoded triggers, same global escalation counter halting at 3), and the never-bypassed self-checks — completion verification, mid-work divergence confirmation, replan acceptance — are still performed, as main-model self-checks rather than panels. A **scope-fit escape** escalates with a recommendation to switch to `-auto`/`-ship` if the change proves not small.

**Rejected alternatives** (the durable payload; shipped mechanics live in the skill's own SKILL.md + references):

- **Reuse `-auto`'s reference files via cross-skill paths** — breaks minerva's self-contained-skill convention and the pointer-integrity infra in `tests/test_skill_budget.py` (each `references/<name>.md` pointer must resolve inside the skill's own dir); adds reader indirection. Same shape rejected for [[033-decision-panel-mechanics-extracted-to-round-table]]'s shared-reference option.
- **Parameterize `-auto` with a mode flag** — forbidden by the never-modify-an-existing-skill-at-run-time rule and would couple two protocols in one file.

The chosen path is a standalone clone, mirroring how `-auto` itself is a near-clone of `-ship` — lifecycle duplication across orchestrators is an accepted project pattern, traded for self-containment.

## Implications

- `-quick` never convenes a `minerva:round-table` panel — that is its defining difference from `-auto`. A future edit that reintroduces panel delegation would erase the distinction.
- New orchestrator-style skills that share the lifecycle clone it standalone (per the rejected-alternatives above and [[030-pattern-rejected-alternative-reinvented-at-runtime]]), rather than sharing references or adding mode flags.
- The fail-closed direction is the load-bearing invariant: under doubt, `-quick` escalates rather than guessing, so a wrong fast-path call is bounded to one extra question, never an undetected bad decision on an ambiguous change.

## Related
- [[014-decision-per-decision-skip-over-sizing-gate]] — builds on
- [[033-decision-panel-mechanics-extracted-to-round-table]] — see also
- [[030-pattern-rejected-alternative-reinvented-at-runtime]] — see also
- [[045-decision-propose-ship-balanced-single-reviewer]] — see also
