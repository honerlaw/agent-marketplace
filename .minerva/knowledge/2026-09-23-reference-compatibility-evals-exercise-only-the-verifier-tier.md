# The compatibility evals exercise only the Verifier tier of propose-ship-auto

**Date**: 2026-09-23
**Type**: reference
**Summary**: Both auto eval scenarios use a trivial fixture; no eval reaches the reviewer-default or panel tier
**Context**: .minerva/work/2026-09-23-adaptive-propose-ship-auto (see git history if the worktree has been cleaned up)

## Context
`scripts/run_compatibility_evals.py` has two `propose-ship-auto` scenarios, `auto` and
`auto-small`. Both run against the same one-line calculator fixture and both check for at least one
independent dispatch. The adaptive orchestrator routes a provably small decision solo, so on that
fixture the only guaranteed dispatch is the completion Verifier, which has a reviewer floor.

## Finding
No compatibility eval exercises a reviewer-default decision (a Skeptic at scope, approach or
whole-proposal) or a panel-tier decision. A regression that stopped the orchestrator from ever
leaving solo, apart from the completion floor, would pass both scenarios. Closing this takes a
fixture whose change is not provably small: multi-file, or with two plausible approaches.

## Implications
- A green compatibility run is evidence for the lifecycle and the Verifier floor, not for tier
  selection. Tier selection is covered by prose contracts and the telemetry tests only.
- When a non-trivial fixture exists, raise the `auto` scenario's dispatch floor above 1.

## Related
- [[2026-09-23-decision-one-orchestrator-picks-each-decisions-tier]] — the tiering this eval does not reach
