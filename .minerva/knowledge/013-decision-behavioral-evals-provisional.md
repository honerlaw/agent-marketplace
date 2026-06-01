# Behavioral skill-value evals are PROVISIONAL — don't CI-gate them, don't trust the deltas until the validation spike returns "go"

**Date**: 2026-05-31
**Type**: decision
**Context**: .minerva/work/018-behavioral-skill-value-runner (see git history if the worktree has been cleaned up)

## Context
The skill-eval mechanism has two tiers (see [[012-constraint-skill-structural-contracts]]): the deterministic structural floor (`contract.json`) and a behavioral "does this skill add value" tier. Unit 018 built the behavioral runner — `scripts/run_skill_evals.py`, reading sibling `evals/<skill>/behavioral.json` cases — which runs a task with a skill vs without (control) and reports a `treatment − control` value-delta.

## Decision
The behavioral tier ships, but **its output is not yet trustworthy** — two standing rules:

- **Don't CI-gate it.** It's on-demand: non-deterministic and it costs API. (Its *deterministic* layers — parse/plan/score/report — are stub-tested in `tests/test_skill_evals.py`; only the live `claude -p` path is non-deterministic.)
- **Don't trust the reported deltas** until the **mandatory validation spike** returns "go". Two things are unsolved: cleanly suppressing one auto-discovered skill as a control (the current control is a best-effort stub), and whether the delta is real signal vs. run-to-run noise. A no-go forces a runner replan. See `.minerva/work/018-behavioral-skill-value-runner/followups.md`.

The format, run commands, and corrected prior-art framing live in **`evals/README.md`** — the source of truth; not restated here. This entry exists to carry the cross-cutting judgment (don't gate, don't trust yet) that a contributor needs *before* acting on any behavioral-eval output, which README reference docs don't guarantee surfacing.
