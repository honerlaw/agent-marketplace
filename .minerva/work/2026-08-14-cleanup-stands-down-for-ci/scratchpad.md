# Scratchpad: cleanup-stands-down-for-ci

## Quick decisions 2026-08-14

- [decided] scope: single unit — one reference file plus a paragraph in SKILL.md; no script,
  no new phase, no public interface change.
- [decided] approach: detect a CI reconciler by grepping `.github/workflows/` for
  `knowledge_fix.py` and stand down, plus widen the outstanding-PR probe to a prefix match.
  Dominant over a declared marker file (needs per-repo setup; forgetting it reproduces the
  bug) and over widening the probe alone (leaves cleanup opening PRs CI would open anyway).
- [decided] soundness: behaviour change is gated on the presence of the workflow, so repos
  without a CI reconciler are untouched. The reference's "why cleanup owns this" rationale
  argues from "no CI workflow to install in each consumer repo" — a reason for the default,
  not a prohibition, and inapplicable once a repo has installed one.
