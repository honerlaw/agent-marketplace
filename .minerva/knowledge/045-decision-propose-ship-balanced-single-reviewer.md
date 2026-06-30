# A fourth orchestrator splits the difference: propose-ship-balanced runs one advisory reviewer at the high-signal gates

**Date**: 2026-06-29
**Type**: decision
**Context**: .minerva/work/045-add-propose-ship-balanced (see git history if the worktree has been cleaned up)

## Context

The lifecycle orchestrators sat at two extremes of adjudication cost: `minerva:propose-ship-quick` has the main model decide every gate solo (no independent scrutiny), and `minerva:propose-ship-auto` convenes a 3-agent `minerva:round-table` panel at ~9 gates (thorough but structurally slow — Proponent+Skeptic in parallel *then* a sequential Arbiter, each gate possibly doubled by a revision round, even after unit 039 moved the panelists to Sonnet and trimmed CONTEXT). Nothing fit a *medium* change: bigger than a one-file tweak, wanting an independent set of eyes, but not ambiguous/high-stakes enough to justify a panel arguing every gate. Work unit 045 added `minerva:propose-ship-balanced` to fill that gap.

## Finding

The ladder now has **four rungs by adjudication cost**: `propose-ship` (human gates) · `propose-ship-quick` (main model solo) · `propose-ship-balanced` (one reviewer at the high-signal gates) · `propose-ship-auto` (consensus panels). The lifecycle is identical across all four; pick by how much independent scrutiny the change warrants.

`-balanced` is `-quick`'s engine (the main model decides every gate directly, with the same fail-closed escalation predicate; see [[042-decision-propose-ship-quick-main-model-adjudication]]) plus **one** addition: at a **fixed taxonomy of high-signal gates** it dispatches a **single fresh-context advisory reviewer** (`subagent_type: general-purpose`, `model: sonnet`) after deciding, and the main model arbitrates that critique inline.

Two design choices are the durable payload:

- **Gate selection is telemetry-driven, not uniform.** A cross-tab of past `-auto` runs' `## Panel decisions` logs showed the panel budget was mostly spent where it changed nothing: completion-verification was ~90% first-vote unanimous (its value is independent *reproduction*, not debate), approach-selection was where independent review actually revised the outcome, scope misses were rare-but-expensive, and triage/partition/TODO were mostly skipped or low-blast-radius. So a reviewer fires only at scope check, approach selection, and completion-verification every run (plus the never-elide divergence / replan-acceptance / replan-vs-FIX gates when they trigger); all other gates are solo. This is a per-decision-**type** policy, not an up-front whole-run sizing classifier — the distinction that keeps it compatible with [[014-decision-per-decision-skip-over-sizing-gate]].
- **One advisory reviewer, arbitrated inline — not a panel.** The main model plays Proponent+Arbiter on warm cache; the single dispatched agent is the Skeptic (a Verifier at completion, which reproduces each success criterion against the diff rather than critiquing prose). There is **no** sequential Arbiter and **no** consensus revision-round re-dispatch — at most one dispatch per gate. To stop the inline-Arbiter collapsing into self-confirmation, "load-bearing critique" is defined **behaviorally** (a violated constraint/criterion, a missed dependency, an overlooked scope surface, a strictly-dominant alternative, an unmet criterion — not restyling or re-weighting already-considered tradeoffs), with an **anti-circularity escape**: if folding would require a materially different decision and the main model cannot confidently tell whether the reviewer is right, that is genuine ambiguity → escalate to the user, never self-confirm.

**Rejected alternatives** (shipped mechanics live in the skill's own SKILL.md + references):

- **Extend `minerva:round-table` with a 1-agent mode and delegate to it** — a single advisory reviewer is not a 3-agent consensus panel (no quorum, no Proponent/Arbiter), so it is not the "panel mechanics" [[033-decision-panel-mechanics-extracted-to-round-table]] keeps in round-table; forcing a degenerate 1-agent path would bloat round-table's identity and raise blast radius on a shared skill.
- **A `--verify` flag on `propose-ship-quick`** — forbidden by the never-modify-an-existing-skill rule and couples two protocols in one file; the same grounds [[042-decision-propose-ship-quick-main-model-adjudication]] rejected "parameterize `-auto` with a mode flag."

The chosen path is a standalone clone of `-quick`, consistent with the project's accepted lifecycle-duplication-for-self-containment pattern.

## Implications

- `-balanced` never convenes a `minerva:round-table` panel; its independent review is always a single advisory reviewer the main model arbitrates. A future edit that reintroduces panel delegation would erase the rung's distinction from `-auto`.
- The gate taxonomy is the load-bearing, revisable knob: it is grounded in run-log telemetry and can be re-tuned via `minerva:replan` if a benchmark later shows a solo gate is missing real defects, or a reviewer gate never changes outcomes.
- Choosing among the four orchestrators is now a four-way call; the `using-minerva` decision matrix and the routing prose carry the discriminators (one-file tweak → quick; medium with a clear-ish approach → balanced; ambiguous/high-stakes/unfamiliar-contract → auto; stay-in-the-loop → propose-ship).

## Related
- [[042-decision-propose-ship-quick-main-model-adjudication]] — builds on
- [[033-decision-panel-mechanics-extracted-to-round-table]] — see also
- [[014-decision-per-decision-skip-over-sizing-gate]] — see also
- [[030-pattern-rejected-alternative-reinvented-at-runtime]] — see also
