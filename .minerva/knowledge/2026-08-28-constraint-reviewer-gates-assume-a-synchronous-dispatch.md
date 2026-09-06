---
name: reviewer-gates-assume-a-synchronous-dispatch
description: Use when a minerva skill's dispatch instruction pins `run_in_background: false` — some Claude Code builds expose no such parameter on the Agent tool, so the pin cannot be honored and the gate parks the run despite passing its enforcing test.
metadata:
  type: constraint
---

# The `run_in_background: false` pin is unsatisfiable where the Agent tool does not expose it

**Date**: 2026-08-28
**Type**: constraint
**Summary**: Dispatch pin can be absent from the Agent tool schema, so gates park despite the enforcing test passing
**Context**: .minerva/work/2026-08-28-observable-orchestrator-mode (see git history if the worktree has been cleaned up)

## Context

[[2026-07-27-constraint-agent-dispatch-pins-execution-mode]] fixed a real defect: skill text that
dispatched a subagent without pinning execution mode let the model background it, and across 105
runs 54% of dispatches backgrounded, parking 95 runs mid-lifecycle. The remedy was to pin
`run_in_background: false` in every dispatch instruction, enforced by `tests/test_skill_dispatch.py`
over five registered sites.

That remedy rests on a premise: **the `Agent` tool accepts the parameter.**

In the Claude Code build this was observed on, it does not. The tool's schema exposes exactly
`description`, `isolation`, `model`, `prompt`, `subagent_type` — no execution-mode property. Two
dispatches made from `propose-ship-balanced`'s reviewer gates both returned an agent id and a
notice that the agent is working in the background, and each parked the run until its task
notification arrived.

## Finding

**A prose pin can only bind a parameter the tool actually has.** Where the `Agent` schema omits
execution mode, `run_in_background: false` is unsatisfiable text: the dispatch backgrounds, the
gate cannot arbitrate "inline, in this same turn" as three separate protocols require, and the run
ends its turn holding a handle.

The enforcing test cannot detect this. It reads skill prose and asserts the pin is *written* — it
has no way to check that the pin is *accepted*, so it stays green while the behavior it exists to
guarantee does not occur. The gate is blind to what it checks
([[2026-08-11-pattern-a-gate-blind-to-what-it-checks]]), and the symptom is the one the 2026-07-27
entry describes: an orchestrator that "sometimes stops and says it's waiting."

## Implications

- **Do not read a green `test_skill_dispatch.py` as evidence that dispatches are synchronous.** It
  proves the instruction is present, nothing more. Confirm against the `Agent` tool's actual schema
  in the running harness.
- Protocols that arbitrate a dispatch "in the same turn" should be written to survive the parked
  case: dispatch, end the turn, resume on the notification, then arbitrate. That ordering is correct
  whether or not the pin binds, so it removes the dependency instead of asserting it.
- The cost scales with dispatch count: `propose-ship-auto` convenes 3-agent panels at most gates,
  so it parks far more often than `propose-ship-balanced`'s single reviewer.
- **Do not skip a reviewer gate to avoid the park.** Completion verification, divergence
  confirmation and new-plan acceptance are documented as never-skipped; a parked run is recoverable,
  an unverified completion is not.

## Related
- [[2026-07-27-constraint-agent-dispatch-pins-execution-mode]] — refines
- [[2026-08-11-pattern-a-gate-blind-to-what-it-checks]] — builds on
- [[2026-08-07-pattern-deferred-work-needs-a-trigger-not-an-assumption]] — see also
- [[2026-06-10-decision-panel-mechanics-extracted-to-round-table]] — see also
- [[2026-09-05-decision-balanced-rechecks-its-folds]] — see also
