# Proposal: reconcile-never-strands-entries

**Date**: 2026-08-07
**Status**: Draft
**Base**: `origin/main` @ `0a87d13`

## Goal

Stop `minerva:cleanup`'s knowledge reconciliation from silently stranding a work
unit's entries when another reconciliation PR is already open.

## Why

Unit 049 made `minerva:promote` add-only and moved cataloguing into `minerva:cleanup`,
which is what stopped concurrent work-unit PRs conflicting on `index.md`. That design
is right. It has one gap, and it fired **six times in two days** on a single project
before anyone noticed — every occurrence found by accident rather than by a signal.

The mechanism:

```
reconcile PR opens   → reads the default branch
another unit merges  → its entries are not in that PR
PR merges            → those entries are still uncatalogued
```

`references/reconciliation.md` Step 2 currently says: if a reconciliation PR is open,
*"report `reconciliation: PR #N already open, skipping` and stop. Anything pending is
simply picked up by the next run after that PR lands."*

**That last sentence is false in the common case.** Cleanup runs once per work unit, so
"the next run" is whenever someone next finishes a unit — days away, or never. Meanwhile
the entry files sit on the default branch **present but uncatalogued**: absent from
`index.md`, invisible to anyone reading the wiki, which is most of what an entry is for.
Nothing reports it, because the run that skipped considered itself successful.

Observed instances: entries 580/581 stranded by a PR opened six minutes before their
unit merged, and 584 by one opened eleven minutes before. Both were only recovered
because a human happened to ask whether everything had landed.

## Approach

Two changes to `plugins/minerva/skills/cleanup/`, both prose — the skill is instructions
to an agent, not code.

### 1. Step 2 waits instead of abandoning

An open reconciliation PR still means **at most one outstanding at a time** — that rule
is load-bearing and unchanged, because two would edit `index.md` concurrently and
recreate the conflict this design removes.

What changes is what happens next. Instead of stopping, the run **waits for the open PR
to merge, then re-runs Step 1's signal against the updated default branch and reconciles
whatever remains**. Re-running the signal matters: the merged PR may already have
catalogued some of what was pending, so the second pass must ask again rather than
assume.

This is exactly the manual recovery that worked twice on the observing project. It is
also bounded: if the open PR does not merge — CI red, auto-merge declined, human review
pending — the run does **not** wait indefinitely and does **not** force a second PR.

### 2. A strand can never be silent

When the wait is abandoned, the pending entries are named in the final report under a new
`Pending, NOT catalogued` line, with their NNNs. "The next run picks them up" becomes a
true statement precisely because the report has told someone.

The same line covers any other reason entries remain pending, so the report can no longer
describe a run as clean while leaving entries invisible.

`SKILL.md` gains this as a third binding rule alongside the two already there
(never commit to the default branch; never force-merge a rejected auto-merge), because
it is the failure the whole reconciliation step exists to prevent.

### Rejected alternatives

- **Reconcile at merge time rather than at cleanup.** Closes the race at the source, but
  needs a trigger that does not exist — cleanup is the post-merge phase every
  orchestrator already calls, and adding a CI workflow puts per-repo installation back
  on every consumer, which unit 049 deliberately avoided.
- **Let the next run pick it up, but say so loudly.** Half the fix: reporting without
  waiting still leaves the entries uncatalogued for an unbounded time. Reporting is the
  fallback here, not the remedy.
- **Allow two concurrent reconciliation PRs.** Recreates the `index.md` conflict unit 049
  removed.

## Success criteria

1. Step 2 instructs a wait-then-continue, not a stop, and says to re-run the Step 1
   signal after the open PR merges.
2. The false claim that the next run picks pending entries up is gone, with the reason it
   is false stated so it is not reintroduced.
3. The bounded-give-up path is explicit: no indefinite wait, no second concurrent PR.
4. The final-report template carries `Pending, NOT catalogued` with NNNs.
5. `SKILL.md` names it as a binding rule.
6. The at-most-one-outstanding rule and the push-is-the-lock reasoning survive unchanged.

## Open Questions

- Whether the wait should have a stated ceiling. Left to the caller: cleanup is invoked
  both interactively and from wake-up loops, and a fixed number here would be the kind of
  guessed interval unit 048 removed elsewhere.
