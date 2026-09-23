# A unanimous quorum deadlocks on write-up fixes the panel agrees don't change the decision

**Date**: 2026-09-23
**Type**: pattern
**Summary**: 3/3 panels escalated decisions all panelists agreed on; round-table gained an accept-with-fixes verdict
**Context**: .minerva/work/2026-09-23-adaptive-propose-ship-auto (see git history if the worktree has been cleaned up)

## Context
The `propose-ship-auto` run that designed this unit convened three 3/3-quorum propose panels:
scope, approach and whole-proposal. **All three escalated to the user.** That tripped the
propose-phase abort and then the three-escalation halt. Every panelist agreed on each decision
itself (one PR; approach A; the proposal as a whole). The `revise` votes asked for:
- a corrected test citation;
- a relabelled line count;
- a rationale that used the right phasing test;
- clarifying sentences, then small carve-outs the decision already implied.

Under a unanimous quorum, one such `revise` fails the vote exactly as "this decision is wrong" would.

## Finding
A verdict vocabulary of `accept / revise / reject` cannot tell *the decision should change* apart
from *the decision is right but the write-up needs fixing*. A unanimous quorum then turns every
precision nit into a revision round, and a second one into a user escalation. This is the same
"runs keep stopping to ask me" symptom the orchestrator collapse was addressing, arriving through a
different mechanism.

`minerva:round-table` now has a fourth verdict, **`accept with fixes`**. It counts toward quorum; the
main model folds the listed fixes without a re-vote and logs each one verbatim. `revise` is reserved
for decision-changing objections. The reclassification fails closed: if the main model finds a
listed fix that would change the decision, **or is unsure whether it would**, the vote counts as
`revise`.

## Implications
- Measure panel deadlocks by what the `revise` votes asked for, not by the vote count. A vote tally
  cannot distinguish a wording nit from a real objection.
- The reviewer tier keeps three verdicts on purpose. It has no quorum to protect, and the main
  model already arbitrates each critique item as load-bearing or not.
- Not every late objection in that run was cosmetic. The final whole-proposal round's Skeptic
  caught two real gaps: the Verifier's asymmetry, and a capped row reaching a panel. Folding fixes
  does not mean waving objections through.

## Related
- [[2026-09-23-decision-one-orchestrator-picks-each-decisions-tier]] — the change whose design run exposed it
- [[2026-06-10-decision-panel-mechanics-extracted-to-round-table]] — builds on
