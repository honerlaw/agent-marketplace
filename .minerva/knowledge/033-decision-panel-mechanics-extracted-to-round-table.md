# Panel mechanics were extracted to minerva:round-table; orchestrators delegate and keep policy

**Date**: 2026-06-10
**Type**: decision
**Context**: .minerva/work/033-extract-round-table (see git history if the worktree has been cleaned up)

## Context

`minerva:propose-ship-auto` inlined the full 3-agent Proponent/Skeptic/Arbiter consensus-panel protocol, making it reachable only by running the entire auto lifecycle. Work unit 033 extracted it into the standalone `minerva:round-table` skill — a pure, behavior-preserving move (byte-identical agent briefs; diff-confined changes) — so any decision can convene a panel: ad-hoc judgment calls, drafted-artifact review, or another skill's decision points. The approach (full protocol move + thin delegation) was **user-decided before the auto run began**, over two rejected alternatives.

## Finding

The extraction line is **mechanism vs. policy**. `minerva:round-table` owns the mechanism: dispatch, the three agent briefs, vote semantics against a caller-specified quorum (2/3 when none is given), the revision round (two votes max), escalation-to-user composition, and the panel log-line format with an observable logging signal (the work unit's scratchpad when one is in-flight in the working tree, conversation-only otherwise). Callers own the policy: whether to convene at all (skip predicates), the per-decision quorum taxonomy, escalation counters/budgets, and all run-level state. Invoking round-table always convenes a panel.

**Rejected alternatives** — the durable payload; the shipped mechanics are fully documented in the two SKILL.md files:

- **Shared reference file** (both skills consume a common `references/panel-protocol.md`): zero drift risk, but an indirection layer no other minerva skill uses, and ad-hoc invocation would load a pointer instead of a protocol.
- **Thin wrapper** (round-table pointing back at the orchestrator's inlined text): inverted dependency — ad-hoc users would load a giant orchestrator skill to run one panel.

Caller mode is a composition device distinct from the [[031-decision-phase-handoff-rides-observable-intake]] inline-arg handoff: the orchestrator invokes the skill **once** at its first panel-worthy decision, leading with a standing instruction (quorum source, log destination, auto-mode behavior), then applies the loaded protocol at each subsequent decision point without re-invoking the Skill tool.

## Implications

- A future orchestrator-style skill with decision points delegates to `minerva:round-table` rather than re-inlining or wrapping the protocol; the rejected designs are also prohibited where they'd be reinvented — in the two skills' own text — per [[030-pattern-rejected-alternative-reinvented-at-runtime]].
- `minerva:round-table`'s standalone 2/3 default never applies inside an orchestrator that declares its own taxonomy (`minerva:propose-ship-auto` states this on both sides of the boundary).
- The skip predicate stays caller-side by construction — "whether to convene" is policy, which keeps [[014-decision-per-decision-skip-over-sizing-gate]]'s fail-closed, per-decision gating intact without round-table needing to know it exists.

## Related
- [[030-pattern-rejected-alternative-reinvented-at-runtime]] — builds on
- [[031-decision-phase-handoff-rides-observable-intake]] — builds on
- [[014-decision-per-decision-skip-over-sizing-gate]] — see also
- [[042-decision-propose-ship-quick-main-model-adjudication]] — see also
