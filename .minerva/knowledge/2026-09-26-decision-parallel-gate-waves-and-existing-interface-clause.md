# Independent gates run as waves, and only a change to an existing interface convenes a panel

**Date**: 2026-09-26
**Type**: decision
**Summary**: propose-ship-auto dispatches independent gates together and narrows the interface panel clause to existing, consumed interfaces
**Context**: .minerva/work/2026-09-26-parallel-gates-narrow-panel-predicate (see git history if the worktree has been cleaned up)

## Context
`scripts/run_trace.py --all` over the six propose-ship-auto runs of 2026-09-23..26
([[2026-09-26-decision-trace-orchestrator-time-from-transcripts]]) found three sources of waiting:

- **Serial propose gates.** Propose took 12–39 min per run, and only about 7 min of that was the
  main model working. The rest was waiting on the scope → approach → whole-proposal gates, one
  after another.
- **Panels convened far more than the "reviewer is the default" rule suggests.** Approach,
  whole-proposal and completion each went to a panel in 5 of 6 runs. In 9 of the 11 panels the
  predicate convened, the cited clause was **public interface**, mostly for a *new* MCP tool
  surface that nothing consumed yet. Completion then re-fired the same clause on the interface
  the proposal's panels had just approved.
- **Completion and code review ran back to back.** Verify showed about 48 s of work against
  19 min of waiting, summed over the six runs.

## Finding
- **Gate waves.** `references/phases.md` Phase 1 runs steps 4–6 as one wave:
  - All three decisions are drafted and routed in gate order.
  - First-wave agents go out in one message.
  - Scope and approach reconcile first. Whole-proposal is **held** until both are final, then
    gets one restart check (approach pick changed, structure changed, or Goal/Success criteria
    rewritten).
  - Fold-audits go out together.

  Completion verification also dispatches Phase 3's code review alongside it. Those findings
  are provisional, and are discarded (together with the audit's) only if a failed completion
  leads to a changed diff.
- **Existing-interface clause.** The panel clause now fires only when a decision changes an
  **existing** interface or contract that consumers outside the unit rely on. Introducing one
  goes to a reviewer, because the solo predicate still denies a new interface.
  - A clause fires once per **approved** change. Completion re-fires it only for a change
    beyond what the proposal approved.
  - Doubt about *this* clause routes to a reviewer seeded with the author's doubt. The Skeptic
    answers it in `## Panel warranted?`, and an evidenced clause the author cannot rule out is
    a third upward-move event.
  - Doubt about ambiguity, blast radius or knowledge tension still convenes a panel.
- **Rejected alternatives.** A 2-agent mini-panel tier was rejected: the problem was routing,
  not panel size. Parallelizing only scope and approach was rejected because it leaves the long
  pole, whole-proposal, serial.

## Implications
- This narrows [[2026-09-23-decision-one-orchestrator-picks-each-decisions-tier]]'s
  "both predicates fail closed" rule for the interface clause only. The second look there is now
  an independent Skeptic, not an automatic panel. The *Re-measure* section asks whether that
  let anything through.
- A wave has several dispatch handles outstanding at once. Each is resumed on its notification,
  and a wave never reconciles on a partial set. That extends
  [[2026-08-28-constraint-reviewer-gates-assume-a-synchronous-dispatch]]. Several synchronous
  dispatches in one message already run concurrently
  ([[2026-07-27-constraint-agent-dispatch-pins-execution-mode]]), so the wave needs no new host
  capability.
- `run_trace.py` reports the designed verify/review overlap as an "out-of-order signal". That is
  expected now, not a tracer defect.
- **Scope any new upward-move event to the rows that can actually move up.** The first cut of
  `## Panel warranted?` fired on every reviewer at a reviewer-capped row (triage, partition, TODO).
  Those rows reach the reviewer *because* a panel clause holds, so every such dispatch would have
  escalated to the user and burned the global escalation counter. Code review caught this. The
  event now ignores capped rows, and ignores the clause that caused the routing. A new escape arm
  needs checking against every row's ceiling, not just the row it was designed for.
- Measure the effect with `run_trace.py --all` against the 2026-09-26 baseline before tuning
  further.

## Related
- [[2026-09-26-decision-trace-orchestrator-time-from-transcripts]] — builds on
- [[2026-09-23-decision-one-orchestrator-picks-each-decisions-tier]] — refines
- [[2026-08-28-constraint-reviewer-gates-assume-a-synchronous-dispatch]] — see also
- [[2026-07-27-constraint-agent-dispatch-pins-execution-mode]] — see also
