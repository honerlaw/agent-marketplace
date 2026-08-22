# Followups: close-silent-reference-gaps

## 2026-08-11

- **A slug-first resolver for bare `[[NNN]]` shorthand.** This unit COUNTS bare shorthand
  and refuses to resolve it, because resolving by number alone is wrong often enough to
  matter: in one 637-entry corpus, of 23 cases where a number named exactly one entry, ~6
  meant something else — usually the same-numbered *work unit*, one literally annotated
  "(work unit)" in the prose. A resolver that matches on the **slug** first, falls back to
  the number only when the slug agrees, and refuses the rest could convert some of the 563
  observed references into real links. That is a new capability with its own accuracy
  question, not a defect fix. **Trigger to revisit:** a corpus where the shorthand count
  this unit now reports is large enough that hand-resolution is impractical.

- **Two stale `Draft` work units.** `.minerva/work/2026-05-19-add-review-skill/` and
  `.minerva/work/2026-06-12-run-context-footprint-estimator/` still carry
  `**Status**: Draft`. The first is plainly shipped — `minerva:review` exists and is
  documented — so its status is simply wrong; the second describes a run-analyzer /
  benchmark harness whose `scripts/run_analyzer.py` and `tests/test_run_analyzer.py` DO
  exist, so it is at least partly shipped too. Noticed during this unit's pre-flight
  in-flight-collision check, where both register as live work. Not touched here because
  deciding "shipped vs abandoned" per unit is a judgment call about someone else's work.
  **Trigger to revisit:** the next time an orchestrator's pre-flight has to reason about
  in-flight collisions, or before any tooling starts trusting `Status`.

- **A calendar-invalid but date-shaped work dir still re-migrates.** `2026-13-45-foo`
  fails `is_date_id`, so the idempotency guard does not skip it. Identical to the entry
  branch's long-standing behaviour, so it is a property of the shared guard rather than
  something this unit introduced — recorded so it is not later mistaken for a gap in the
  work-dir fix.

## Backfill disposition (2026-08-22)

Triaged by `minerva:backfill-followups`. Every item above is unchanged; this section records where each one landed.

- **A slug-first resolver for bare `[[NNN]]` shorthand.** → open (low) — not filed at this pass; a new capability with its own accuracy question, and its stated trigger (an impractically large shorthand count) has not fired
- **Two stale `Draft` work units.** → shipped — both now carry `Shipped` with a retroactive-closure note
- **A calendar-invalid but date-shaped work dir still re-migrates.** → open (low) — not filed at this pass; recorded so it is not mistaken for a gap, and it is a property of the shared guard
