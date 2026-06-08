# To make a consensus/gate mechanism cheaper for small work, gate per-decision and fail closed — do not add an up-front whole-task "sizing" classifier

**Date**: 2026-05-31
**Type**: decision
**Context**: .minerva/work/019-auto-skip-predicate (see git history if the worktree has been cleaned up)

## Context

`minerva:propose-ship-auto` runs a 3-agent Proponent/Skeptic/Arbiter panel at ~8 decision points per run. The ask was to let it skip the panels "when the task is small enough." The shipped mechanism — a per-decision conjunctive fail-closed skip predicate — is fully documented in that skill's SKILL.md (`### Skip predicate`). This entry records the **rejected alternative and why**, which the shipped skill deliberately omits and which would otherwise be re-litigated by the next person trying to make a minerva gate cheaper.

## Finding

The first-drafted design was an **up-front whole-task "sizing gate"**: classify the run as `fast-lane` vs `standard` once (originally via a dedicated sizing panel + a `--fast` flag), then suppress downstream panels in fast-lane. The consensus panel rejected it on two structural grounds, and chose a **per-decision** predicate instead:

1. **A sizing gate is self-defeating.** Deciding whether to skip panels by *running a panel* (or any heavyweight up-front classifier) spends the cost you are trying to save, and does so unconditionally — worst in the small-task regime it targets. A `--fast` flag is worse still: it smuggles a human strategic risk-call into a skill whose identity is "no human gates."
2. **A whole-task classification is too coarse.** It judges on the seed description, before the risky decision exists. The dangerous task is the one that *looks* small but contains one load-bearing decision that only emerges mid-run (during approach selection or a mid-work divergence). An up-front verdict is structurally blind to it.

The **per-decision fail-closed predicate** dominates both: each decision applies a cheap conjunctive test (additive/low-blast-radius, mechanically verifiable, single-surface, no new interface, violates no known constraint, and for approach decisions an *action* check that ≥2 alternatives were enumerated and one is strictly dominant). Any unmet clause — or any uncertainty — convenes the panel at its existing quorum. Because it re-evaluates at every point, **late-emerging risk is handled structurally**: the decision that turns out load-bearing simply fails the predicate and gets its panel. That removes the need for a separate "escape hatch back to full panels," and with it the "the same LLM is both detector and suspect" problem an escape hatch reintroduces.

**Corollary — the never-skippable rule** (transferable to any future gated minerva flow): a panel whose **trigger precondition is "a load-bearing divergence/finding has already surfaced," plus the completion self-check, must never be skippable** — its precondition is the logical negation of the predicate's low-blast-radius clause, and its whole value is being an independent second pair of eyes on the main LLM's own self-assessment. In `propose-ship-auto` these are completion-verification, mid-work divergence-confirmation, new-plan acceptance, and Replan-vs-FIX.

## Implications

- When asked to make any minerva consensus/gate mechanism cheaper or faster, reach first for a **per-decision, conjunctive, fail-closed** skip — not an up-front task-size classifier or a mode flag. The fail-closed conjunction makes a wrong *skip* require every clause to wrongly pass (blast radius bounded to additive/single-surface/low-risk), while a wrong *non*-skip merely runs a panel you didn't strictly need — the correct asymmetry for an autonomous, human-out-of-loop flow.
- Make a skip predicate's self-referential clauses **action checks**, not self-judgments. "Did I enumerate ≥2 alternatives and is one dominant" is auditable; "no better alternative exists" is gameable by a model that never looked.
- Any new never-skippable panel must satisfy the corollary test (precondition = an already-surfaced divergence/finding, or it is the completion self-check). Mark it never-skippable in **both** the taxonomy table and the prose — a prior review round caught two such panels silently left skippable.
- Log each skip with the **concrete evidence** that satisfied the predicate, under the existing decision-log header, so a later review/promote pass can audit that skips are honest rather than rubber-stamped. Skips are promote-invisible by construction (no Skeptic → no durable-pattern channel), which is intended.

## Related
- [[025-decision-synthesize-wired-post-promote-self-gating]] — see also
- [[030-pattern-rejected-alternative-reinvented-at-runtime]] — see also
- [[031-decision-phase-handoff-rides-observable-intake]] — see also
