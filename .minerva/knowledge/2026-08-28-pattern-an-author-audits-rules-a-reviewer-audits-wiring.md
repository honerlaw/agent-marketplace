---
name: an-author-audits-rules-a-reviewer-audits-wiring
description: Use when deciding whether a self-review can substitute for an independent one — an author reliably catches violations of rules they can look up, and reliably misses whether the thing they just built is wired to anything and whether their own test tests it.
metadata:
  type: pattern
---

# An author's audit catches rule violations; only a reviewer catches dead wiring

**Date**: 2026-08-28
**Type**: pattern
**Summary**: Self-review finds lookup-able rule violations and misses orphaned code and toothless tests
**Context**: .minerva/work/2026-08-27-deferral-cost-model (see git history if the worktree has been cleaned up)

## The measurement

One changeset, two review lenses run within minutes of each other: a minerva audit by the author
(spec fidelity + knowledge compliance) and an independent fresh-context code review.

**The author's audit found exactly one thing** — a path that violated a documented
`.minerva/knowledge/` constraint. Real, high severity, and the kind of finding that comes from
holding a written rule against a diff.

**The reviewer found three the author did not**, none of which is subtle in hindsight:

- a function implemented, unit-tested, and documented — but **called by no workflow step**, so the
  safety property it existed to provide was unreachable;
- a parser that **truncated its output**, demonstrable on the author's own proposal, written an
  hour earlier;
- a **test that could not fail** the way its name claimed, written by the author the same day.

## Why the split is structural, not a competence gap

The author's audit is strong on *"does this violate something I can look up"* — that lens has an
external referent, so it works even on your own code.

It is weak on *"is this thing I just built actually connected, and does my test test it"* —
because both questions require **not already believing the answer**. The author wrote the
function, so the function feels used. The author wrote the test, so the test feels meaningful.
Neither belief survives contact with someone who did not write them, and neither is dislodged by
re-reading more carefully.

Note the shape of all three reviewer findings: **not one is a rule violation.** They are all
"this thing does not connect to that thing" — which is precisely the class no checklist catches,
because a checklist is a list of rules.

## What follows

- Spend independent review where wiring and test-adequacy matter — a new mechanism, a new
  predicate, a new test file. Do not spend it re-checking documented rules, which the author's own
  lens covers cheaply.
- Treat *"I wrote a test for it"* as no evidence at all, from oneself. The reviewer's finding here
  was that the test's assertion would pass with the rule stated backwards.
- A self-review that returns only rule violations has probably not failed — it has probably run
  the only lens it can run.

## Related
- [[2026-08-28-pattern-a-decider-and-an-executor-are-different-surfaces]] — see also: the orphaned-function finding is that pattern at function scope, and it took a reviewer to see it
- [[2026-08-28-pattern-a-presence-assertion-must-be-scoped-to-what-it-guards]] — see also: the toothless-test finding, generalised
- [[2026-06-29-decision-propose-ship-balanced-single-reviewer]] — see also: the orchestrator rung that spends exactly one independent reviewer at the high-signal gates; this is evidence for which gates those are
