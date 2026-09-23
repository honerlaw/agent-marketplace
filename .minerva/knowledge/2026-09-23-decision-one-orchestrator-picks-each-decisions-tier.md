# One autonomous orchestrator picks each decision's adjudication tier

**Date**: 2026-09-23
**Type**: decision
**Summary**: propose-ship-auto routes each decision solo/reviewer/panel and escalates up a tier; quick and balanced deleted
**Context**: .minerva/work/2026-09-23-adaptive-propose-ship-auto (see git history if the worktree has been cleaned up)

## Context
Three autonomous orchestrators shared one lifecycle and differed only in adjudication:
`propose-ship-quick` (main model alone), `propose-ship-balanced` (one reviewer at fixed gates) and
`propose-ship-auto` (3-agent panels). Picking one was a whole-run sizing call made by the user
before the risky decision existed. Quick and balanced also had a **scope-fit escape**: when a
change looked bigger than the rung, the only move was to stop and recommend a sibling. The user
reported that balanced runs "very often" stopped to ask to switch to auto.

## Finding
`propose-ship-auto` is now the only autonomous orchestrator. Quick and balanced were deleted
without aliases, and minerva went to 2.0.0. The main model **drafts each decision, then routes it**
(`references/decision-protocol.md`):

1. Hardcoded triggers go to the user.
2. The **panel predicate** convenes a panel: ambiguity, blast radius, interface change or knowledge
   tension. This is quick/balanced's former *user*-escalation predicate.
3. The strict conjunctive **solo predicate** allows solo. This is auto's former skip predicate.
4. Everything else gets a **reviewer**: balanced's Skeptic, plus one fold-audit re-check after a fold.

Per-row floors and ceilings clamp that choice:
- **Panel floor:** divergence, new-plan acceptance and replan-vs-FIX.
- **Reviewer floor:** completion. The Verifier stays asymmetric, with no fold-audit and no upward
  move.
- **Reviewer ceiling:** triage, partition and TODO disposition. These are solo by default and
  never reach a panel.

Uncertainty moves a decision **up**, never sideways:
- An unadjudicable critique (`[reviewed — escalated]`) or a failed fold-audit goes to a panel.
- A panel that fails quorum twice goes to the user.

Everything logs under one dated `## Decisions YYYY-MM-DD` header, each line naming its tier.

## Implications
- This is not a whole-run sizing gate. Tier is chosen per decision on that decision's evidence,
  which keeps [[2026-05-31-decision-per-decision-skip-over-sizing-gate]] intact. Do not add an
  intake size estimate or a mode flag. That was floated for this unit and rejected on those grounds.
- The up-arm keys only on the two reviewer events that used to go to the user, never on a Skeptic
  `revise`. That is what separates it from the arm
  [[2026-09-05-decision-balanced-rechecks-its-folds]] rejected. Its real trigger rate is
  unmeasured. `decision_telemetry.py` tallies tier lines, and the protocol's *Re-measure* section
  asks for a revisit after ~10 runs, including whether the propose-phase abort has gone inert.
- **A renamed or retired caller must be canonicalized everywhere it is compared, not just where
  it is rendered.** The first cut mapped legacy `quick`/`balanced` checkpoints to `propose-ship-auto`
  only in the resume prompt. The "caller cannot change" validator then rejected the very resume the
  prompt asked for. A code reviewer caught it; `minerva_runtime.canonical_caller()` now serves both.

## Related
- [[2026-06-16-decision-propose-ship-quick-main-model-adjudication]] — supersedes
- [[2026-06-29-decision-propose-ship-balanced-single-reviewer]] — supersedes
- [[2026-09-05-decision-balanced-rechecks-its-folds]] — builds on
- [[2026-05-31-decision-per-decision-skip-over-sizing-gate]] — builds on
- [[2026-09-23-pattern-a-unanimous-quorum-deadlocks-on-write-up-fixes]] — the vote rule adopted alongside
- [[2026-09-23-reference-compatibility-evals-exercise-only-the-verifier-tier]] — see also
