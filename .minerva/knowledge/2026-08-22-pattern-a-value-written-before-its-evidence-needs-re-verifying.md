# A value written before its evidence exists must be re-verified by every consumer, not the nearest one

**Date**: 2026-08-22
**Type**: pattern
**Summary**: a field authored ahead of its evidence is a claim; re-verify it at every consumer, not just the nearest
**Context**: .minerva/work/2026-08-22-intake-matches-open-issues (see git history if the worktree has been cleaned up)

## Context

`proposal.md`'s `**Closes**: #NN` field closes a GitHub issue when the PR merges. It was designed
under one implicit precondition: only `minerva:promote` ever wrote it, at end-of-work, by an agent
that had just read the finished diff. Every downstream consumer could therefore treat a present
value as already verified. `minerva:ship` does exactly that — it reads the field and emits one
`Closes #N` line per entry, and its own text forbids it to look at the diff ("authored, never
inferred", because a wrong auto-close destroys a real record).

Adding an intake step that adopts an open issue moved the authoring point earlier: the field is now
written at propose time, before a single line of the diff exists. The value's *format* did not
change, so nothing broke visibly and every test stayed green.

## Finding

Moving the authoring point turned the field from a fact into a **claim**, and the claim can go stale
in the ordinary course of the work — a replan, a narrowed scope, an abandoned half — with nothing in
the pipeline positioned to notice.

The fix that first suggested itself was to patch the nearest consumer, `minerva:promote`, and stop.
That is wrong, and the reason generalizes: **`minerva:promote` is not on the critical path.**
`minerva:ship` documents that it only nudges, and that "the user can ship and skip — strict ordering
is not enforced". A unit can go propose → work → ship and never pass the consumer that was patched.
The autonomous orchestrators make it sharper still: they auto-accept ship's PR-body gate, which is
the one remaining place a human would have read the `Closes` line before it took effect.

So both consumers were changed, in deliberately asymmetric directions:

- `**Closes**` — **amend-or-drop.** Re-verify each entry against the real diff; remove what it no
  longer resolves.
- `**Linked**` (the sibling field recording an issue matched but *not* adopted) — **add-if-warranted.**
  Nothing was promised, so nothing needs dropping; promote it into `**Closes**` only if the diff
  turned out to resolve it.

Dropping an unverified claim is not the same act as inferring one. The prohibition on inference
guards against *adding* issues the author never listed; dropping runs the other way, toward the
cheap failure. A stale-open issue lingers; a wrong auto-close destroys a record.

## Implications

- When you move where a value is authored, the value's **contract** changes even when its format
  does not. Ask what each consumer was entitled to assume under the old authoring point, and which
  of those assumptions you just invalidated.
- Enumerate consumers by what the pipeline *permits*, not by what it recommends. A skill that says
  "consider running X first" is telling you X is skippable, so any invariant enforced only inside X
  is not enforced. This is the same shape as
  [[2026-08-07-pattern-deferred-work-needs-a-trigger-not-an-assumption]]: a step that "will happen
  later" only happens if something makes it happen.
- Where a claim and a fact share one field, say which direction each consumer may move it. Collapsing
  amend-or-drop and add-if-warranted into a single "re-check the field" rule reads fine and
  implements two different behaviors.
- An auto-accepted gate is not a gate. When an orchestrator accepts a confirmation step on the user's
  behalf, every check that step was carrying has to exist somewhere else.

## Related
- [[2026-08-07-pattern-deferred-work-needs-a-trigger-not-an-assumption]] — same shape: a later step that nothing schedules is not a step
- [[2026-08-11-pattern-an-unenforced-constraint-is-aspirational]] — a rule living only in the skippable consumer enforces nothing
- [[2026-08-22-pattern-a-ledger-line-is-not-a-resolution]] — a record marking work handled must distinguish decided-and-done from decided-to-wait
