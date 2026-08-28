---
name: a-decider-and-an-executor-are-different-surfaces
description: Use when adding a new state, mode, or vocabulary term to an existing system — teaching the place that DECIDES it does not teach the places that CONSUME it, and the gap is silent. Enumerate consumers from the definition, and prefer a test that derives the legal set from the definition site.
metadata:
  type: pattern
---

# Teaching a system where a state is decided does not teach it where the state is consumed

**Date**: 2026-08-28
**Type**: pattern
**Summary**: A new state's decider and its executors are separate surfaces; updating one leaves the others silently wrong
**Context**: .minerva/work/2026-08-27-deferral-cost-model (see git history if the worktree has been cleaned up)

## Two instances, one work unit

Adding plan-level phasing meant teaching four orchestrators that a work unit can declare
`## Phases`. That was done at the **scope check** — the step where phasing is *chosen*. Every
scope check got the new rule; the change looked complete and the whole suite passed.

The orchestrators' **cleanup gate** — where phases are *executed* — was untouched. Its behavior
on a phased unit: ship phase 1, poll the PR, see `MERGED`, invoke cleanup (which correctly defers
teardown, being phase-aware), then **report success and exit**. Phases 2..N never ship. The unit
stalls at a report that says it finished. Caught only by running an orchestrator against the unit
that introduced the feature.

The same unit hit the shape a second time, at a different scale. Retiring the `low` priority tier
edited the **definition site** — the vocabulary table — and the table-counting test went green
immediately. Two live **use sites** in the same file survived: a label colour and a worked
example still saying `priority: low`. Both were found by hand.

## The shape

A concept has a place where it is **defined or decided**, and places where it is **consumed**.
They are different surfaces, and a change to the first produces no signal at the second. This is
distinct from ordinary "I missed a caller": the decider's own tests pass, the feature demos
correctly, and the consumer's failure only appears on a path nobody exercises until the feature
is used for real.

It is worse than a missed caller in one specific way: a missed caller usually throws. A missed
*executor* often has a perfectly reasonable default behavior for the old world — "report and
exit" was correct for every unphased unit — so it fails by doing the wrong sensible thing.

## What to do

- **Enumerate consumers from the definition, not from memory.** When adding a state, grep for
  every site that branches on the thing the state modifies, and list them before editing any.
- **Prefer a test that derives the legal set from the definition site.** For the `low` retirement
  the durable fix was not "assert `low` is absent" — which is both unmaintainable and wrong,
  since prose legitimately discusses a retired tier — but: read the vocabulary out of the
  definition table, then assert every *use* of that vocabulary anywhere in the corpus is a member.
  Adding or removing a term then needs no test edit, and the enforcement cannot drift from the
  thing it enforces.
- **For an executor gap, assert the required reference, not the prose.** Three orchestrators
  phrase their gates differently on purpose; a wording assertion would either force false
  convergence or false-negative. Requiring each to point at the single-sourced protocol is a
  check with no variants.

## The tell

You added a concept and every place you edited was a place that *chooses* the concept. Ask where
the concept is *read* — and note that the answer is rarely the same file.

## Related
- [[2026-07-21-pattern-catalog-semantic-drift-recurs]] — builds on: the same definition-site / use-site split, there across catalog surfaces
- [[2026-08-11-pattern-the-enumeration-is-what-fails]] — see also: why the fix derives the legal set instead of listing it
- [[2026-08-07-pattern-deferred-work-needs-a-trigger-not-an-assumption]] — see also: the executor gap here produced exactly that failure — a next phase with no trigger, and a report that omitted it
- [[2026-08-11-pattern-a-gate-blind-to-what-it-checks]] — see also: a green check whose model of its subject is narrower than the subject
- [[2026-08-28-pattern-a-presence-assertion-must-be-scoped-to-what-it-guards]] — see also
- [[2026-08-28-pattern-an-author-audits-rules-a-reviewer-audits-wiring]] — see also
