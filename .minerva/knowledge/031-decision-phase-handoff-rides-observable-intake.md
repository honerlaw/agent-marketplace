# Phase-to-phase skill handoffs ride an observable intake, never a self-judged "did the prior phase converge?" predicate

**Date**: 2026-06-07
**Type**: decision
**Context**: .minerva/work/031-add-explore-skill (see git history if the worktree has been cleaned up)

## Context

Adding `minerva:explore` — a divergent, commitment-free brainstorming phase upstream of `minerva:propose` — raised the question of how one lifecycle skill should hand off to the next. `explore` writes no file and lives entirely in the conversation; when the user converges on a direction, `propose` must pick up without re-running its own divergent intake over the same chat. The tempting mechanism was to have `propose` *detect* "an exploration converged earlier this session" and skip its divergence. (Background on the two skills: `explore` diverges on the *problem / direction* axis — what or whether to build — while `propose` diverges on the *implementation-approach* axis — how to build the chosen direction; because they diverge on different axes the handoff is not redundant.)

## Finding

A handoff between two phased skills should ride an **existing, observable intake signal**, not a self-judged predicate about the prior phase's state.

`explore` hands off via an explicit `Skill`-tool call `minerva:propose "<direction>"`, passing the converged direction as propose's **inline argument** — reusing propose's already-tested inline-arg intake path. The alternative — `propose` scanning the session to judge "did an exploration converge?" — was explicitly rejected: it is the gameable kind of self-assessment that misfires on stale, unrelated, dropped, or reframed explorations in the same session. "An inline argument was passed" is observable; "the prior phase converged" is an opinion. That is the same action-vs-self-judgment distinction [[014-decision-per-decision-skip-over-sizing-gate]] draws for skip predicates, applied to handoffs.

## Implications

- When wiring any future minerva phase-to-phase handoff, prefer an **observable signal** (an argument that was/wasn't passed, a file's presence, a marker) over a free-form history scan or a "did X happen?" self-judgment.
- The explore/propose boundary is documented **in propose's own skill text** (a "Convergent step — relationship to `minerva:explore`" note) and **test-anchored** by a `minerva:explore` must-contain anchor in `evals/propose/contract.json`, so the rejected predicate isn't left only in knowledge to be re-invented at runtime — the lesson [[030-pattern-rejected-alternative-reinvented-at-runtime]] paid for.
- `explore` is the divergent pre-`propose` phase (it may legitimately end in drop / reframe / ready) and writes nothing; it is upstream of `minerva:grill-plan`, which stress-tests an already-drafted plan. The three do not overlap.

## Related
- [[030-pattern-rejected-alternative-reinvented-at-runtime]] — builds on
- [[014-decision-per-decision-skip-over-sizing-gate]] — see also
- [[006-decision-review-lens-ownership]] — see also
- [[007-constraint-skills-must-call-tools-not-prose]] — see also
- [[033-decision-panel-mechanics-extracted-to-round-table]] — see also
- [[049-constraint-handoffs-name-skill-tool]] — see also
