# Size a wait to what is actually being awaited — and prefer the tool's own blocking primitive

**Date**: 2026-07-28
**Type**: pattern
**Context**: .minerva/work/2026-07-29-right-size-lifecycle-waits

## Context
`minerva:ship` polled CI on a hardcoded 270s cadence, justified as "stays under the 5-minute prompt-cache TTL". The premise expired (this session type uses a 1-hour TTL), leaving a constant with no reasoning behind it — and one that was wrong at both ends: measured CI is ~10-26s in a docs/tests-only repo and ~1000s for a full suite, so it idled minutes on one and burned wake-ups on the other. Four orchestrator skills carried the same shape at `delaySeconds: 300` for their PR-merge poll.

The obvious fix — estimate the duration from `gh run list` history and poll on that — was drafted, reviewed, and **rejected during the run**. Its bound `MAX_POLLS = min(120, ceil(2 × estimate / 30))` had no floor: at a 10s estimate it evaluated to a single immediate poll, so the watcher exited instantly and the run fell through to a 1200s fallback. The replacement was worse than the constant it replaced, in exactly the fast-repo case it targeted.

## Finding
Two rules, learned in that order.

**1. A wait's shape must match what is actually being waited on.** The same "poll for a while" code served two different waits, and one rule could not fit both:
- *CI completion* is duration-shaped and varies by two orders of magnitude across repos — so no constant is defensible, and the wait must come from the state itself.
- *Auto-merge landing* is queue-shaped: CI is already green, and the PR is behind a required review or a merge queue. Sizing it by "remaining CI time" collapses toward zero, and a retry cap built on it degrades from a ~1 hour wall-clock bound to ~12 minutes.

So the merge poll **keeps** its constant — a constant is the right answer when the wait is not proportional to anything you can measure — and what it was missing was the *rationale*, not a formula.

**2. Prefer the tool's own blocking primitive over a hand-rolled poll loop.** `gh pr checks <pr> --watch --fail-fast` blocks until checks settle and returns on the first failure. Run detached, it resumes the run when CI genuinely settles. It deletes an entire class of self-inflicted bugs at once: no interval to choose, no bound arithmetic to get wrong, no rate-limit exposure, no zero-checks edge case. Every one of those had to be *designed around* in the hand-rolled version, and one of them (the missing floor) shipped a regression past a reviewer.

Corollary on the fallback: a long `ScheduleWakeup` stays armed underneath, and it is a **re-arming keep-alive, not a budget** — each firing that still finds work pending schedules the next. That is what preserves "the session can end and be re-entered" without capping how long a slow repo may take.

## Implications
- Before writing a poll loop, check whether the CLI already blocks (`--watch`, `--wait`, `--follow`). Reach for a loop only when it does not.
- When a constant is genuinely right, say **why** it is right in the text next to it. The defect here was never the number 300; it was that nothing explained it, so the next reader could not tell a considered choice from a leftover.
- A stale premise ages worse than a stale value: "stays under the 5-minute TTL" read as a *reason* long after it stopped being one, which is what let the number survive unexamined.
- Check-state vocabulary for `gh pr checks` is `bucket` (`pass`/`fail`/`pending`/`skipping`/`cancel`). There is no `conclusion` field — requesting it is a hard error — and `state` carries `SUCCESS`/`FAILURE`, never `COMPLETED`. Two long-standing instructions in `ship` named fields that do not exist; nothing caught them because prose is not executed until it is.
- An always-armed fallback needs an exit: a wake-up firing after the work already shipped must recognize that and stop, or it re-enters a lifecycle that has finished.

## Related
- [[2026-07-27-constraint-agent-dispatch-pins-execution-mode]] — builds on
- [[2026-05-19-constraint-skills-must-call-tools-not-prose]] — builds on
- [[2026-06-06-pattern-rejected-alternative-reinvented-at-runtime]] — see also
