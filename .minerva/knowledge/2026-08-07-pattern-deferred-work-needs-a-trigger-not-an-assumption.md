---
name: deferred-work-needs-a-trigger-not-an-assumption
description: Use when writing a step that skips work and defers it. "The next run will pick it up" is only true if something schedules a next run — and if the deferral is silent, nobody learns it was wrong. Wait, or report; never assume.
metadata:
  type: pattern
---

# Deferred work needs a trigger, not an assumption

**Date**: 2026-08-07
**Type**: pattern
**Context**: .minerva/work/2026-08-07-reconcile-never-strands-entries

## The shape

`minerva:cleanup`'s reconciliation step had a skip: if a reconciliation PR is already
open, stop, because two would conflict on `index.md`. The rule was right. The sentence
after it was not:

> Anything pending is simply picked up by the next run after that PR lands.

There is no next run. Cleanup fires once per work unit, so "the next run" is whenever
someone next finishes a unit — days away, or never. Nothing schedules one, and nothing
watches the pending set in the meantime.

The result: a reconciliation PR opened minutes before another unit merged could not
contain that unit's entries, and those entries sat on the default branch **present but
uncatalogued** — in the corpus, absent from the index, invisible to anyone reading the
wiki. Six occurrences in two days on one project. Every one found by accident, because
the run that skipped reported itself successful.

## The two failures, and they compound

1. **The deferral had no trigger.** "Later" was an assumption about someone else's
   behaviour, not a mechanism.
2. **The deferral was silent.** The final report had no line for "entries exist that I
   did not catalogue", so a run could be clean-looking and wrong at the same time.

Either alone is survivable. Together they are undetectable: the work never happens and
nothing says so.

## The rule

When a step declines to do work it has identified:

- **Prefer waiting** over deferring, when the blocker is short-lived and observable. The
  fix here was to wait for the open PR to merge, re-run the signal, and reconcile the
  remainder — which is exactly what a human did by hand, twice, to recover.
- **If you must defer, name what you deferred**, item by item, in whatever the step's
  output is. A report that omits skipped work is a report that lies by omission.
- **Re-derive after waiting.** The thing you waited on may have done part of the job;
  the second pass has to ask again rather than assume its own earlier snapshot.

The tell that this class is present: a comment or doc that says *"the next run"*,
*"picked up later"*, or *"eventually"* without naming what causes the next run.

## Related

- [[2026-08-05-decision-promote-add-only-reconcile-on-default]] — the design this gap lived inside, which is otherwise sound and unchanged
- [[2026-08-05-pattern-read-then-act-is-not-a-lock]] — the sibling hazard in the same step: that one is about two runs racing, this one about no second run existing
- [[2026-08-05-constraint-knowledge-allocation-scans-across-branches]] — the allocation half of the same concurrency story
- [[2026-08-11-pattern-a-gate-blind-to-what-it-checks]] — see also
