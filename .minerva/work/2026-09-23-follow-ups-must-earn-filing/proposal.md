# Proposal: follow-ups-must-earn-filing

**Date**: 2026-09-23
**Status**: Draft

## Goal

Make a filed follow-up rare. Fixing a defect **in the current unit** becomes the default
disposition, and a forward-looking item may become a tracker issue only when it clears **three**
conditions, not one:

1. **Defect** — a concrete failure scenario can be written (the existing bar, unchanged).
2. **Valuable** — it merits `critical` or `high` priority. `medium` is retired from the filing
   vocabulary, exactly as `low` was.
3. **Too large to absorb** — fixing it needs its own design/proposal, changes a public interface
   or cross-cutting contract, or would materially widen the PR's blast radius.

A defect that fails condition 3 is **fixed now**, even when it sits outside the diff. One that
fails condition 2 goes to a `reference` knowledge entry or is discarded. Filing is soft-capped at
**one issue per unit**; a second requires a logged justification.

## Why

The user reports that asking for one issue "almost always results in 2 or 3 follow-ups". The
2026-08-27 deferral bar asks only *is this a real defect?* — never *is it worth a tracker slot*
or *is it too big to just do now?* Two rules feed the flow:

- `minerva:review` triage makes a defect FIX only "if it belongs to this diff"; a defect in
  adjacent code becomes SUGGEST → TODO → issue regardless of fix size.
- `github-issues.md` defaults an item with no signal to `medium` ("we should eventually do
  this") — a level that files an issue for work nobody has committed to. Both open followup
  issues (#98, #113) are `priority: medium`.

## Approach

Single-sourced, per the bar's own rule: the conditions live only in
`plugins/minerva/skills/promote/references/deferral-bar.md`; consumers point at it.

- `deferral-bar.md` — restate the bar as three conditions; add a **Fix now** outlet ahead of
  the tracker (absorbable defects, including outside the diff, with a bound on what "absorbable"
  means); define the per-unit soft cap and its justification line.
- `github-issues.md` — two-level priority table (`critical`, `high`); drop the `medium` colour
  and the "default to medium" sentence; an item with no urgency signal fails condition 2.
- `review/references/protocol.md` — triage: a finding with a failure scenario is FIX unless it
  fails condition 3; drop the "belongs to this diff" restriction.
- `promote/references/modes.md`, the three `propose-ship-*` `phases.md`, and
  `using-minerva/references/guide.md` — update their summaries (priority lists, outlet lists) to
  match; keep them as pointers.
- `tests/test_deferral_bar.py` — vocabulary is exactly `{critical, high}`; the bar names the
  fix-now outlet.

Rejected: a hard numeric cap (a real critical defect would be dropped); keeping `medium` but
forbidding its use (a vocabulary level that must never be used is a trap).

## Success criteria

- [ ] `deferral-bar.md` states the three conditions, the fix-now outlet, and the one-per-unit soft cap.
- [ ] The priority table in `github-issues.md` has exactly `critical` and `high`; no skill prose uses `priority: medium`.
- [ ] Review triage no longer restricts FIX to the diff; absorbable defects outside it are FIX.
- [ ] Every consumer still points at `deferral-bar.md`; the bar's defining sentence appears only there.
- [ ] `pytest` passes.

## Open Questions

None.
