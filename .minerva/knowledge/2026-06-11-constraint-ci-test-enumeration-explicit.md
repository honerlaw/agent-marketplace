# New test modules are invisible to CI until appended to the enumerated pytest list

**Date**: 2026-06-11
**Type**: constraint
**Context**: .minerva/work/2026-06-11-skill-progressive-disclosure


<!-- superseded-by: 2026-08-11-decision-ci-runs-the-whole-suite -->
> **Superseded by [[2026-08-11-decision-ci-runs-the-whole-suite]]** (2026-08-11) — CI now runs `pytest tests/`; the enumerated list is gone, so a new module
> cannot be dark to CI. The three files that forced the list tested a plugin
> deleted in `20d32e0` and were removed.

## Context
Work unit 035 added `tests/test_skill_budget.py` and claimed its success criterion "enforced in CI" once the test passed locally. The completion-verification panel failed the unit on its first vote (1/3 accept) because the test was not running in CI at all, forcing a replan.

## Finding
CI (`.github/workflows/evals.yml`) runs an **explicitly enumerated** list of test modules, not a bare `pytest`. A new `tests/*.py` does not run in CI until appended to that list — and the failure mode is **silent**: the module simply never runs, nothing goes red, and no CI failure teaches the lesson. A new test passing locally proves nothing about CI.

Why the list is enumerated — pre-existing broken financials modules abort bare-pytest collection — is documented in the workflow's own scope note and in this unit's `replan.md`; cite those, don't re-derive.

## Implications
- **Adding any test module**: append it to the workflow's pytest enumeration in the same change, and confirm CI coverage equals the local run.
- **Claiming "enforced in CI"** in a success criterion or completion checklist requires reading the workflow, not just a green local run.

## Related
- [[2026-06-11-constraint-skill-progressive-disclosure]] — see also
