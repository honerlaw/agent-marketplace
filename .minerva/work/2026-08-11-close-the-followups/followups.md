# Followups: close-the-followups

## 2026-08-11

- **The repo's followup backlog is largely stale and nobody knows which parts.** 22
  `followups.md` files hold roughly 60 items; a triage during this unit's scoping found
  much of it already shipped — the Phase B `minerva:lint` skill, the slug-first shorthand
  resolver, the calendar-invalid work-dir case, the two stale Draft units. Nothing marks a
  followup as done, so every future scoping pass re-reads all 22 files to find the same
  answer. **Likely shape:** a triage pass that annotates each item `shipped (<unit>)` /
  `still open` / `obsolete`, then a second unit that closes what survives. The user chose
  the five-item scope over this sweep when asked, so it is recorded, not deferred silently.
  **Trigger:** the next time someone scopes work from followups.

- **`unit_state` is half state-reader, half policy.** `in_flight` is the orchestrators'
  pre-flight rule living in a module that otherwise returns raw facts. Deliberate — four
  consumers share one predicate — and the docstring says so, but if a fifth consumer wants
  a different notion of "in progress", split the policy out rather than widening this one.

- **Nothing enforces that a new markdown scan is fence-aware.** Both readers in
  `work_status.py` shipped without it, one of them in the unit immediately before this,
  past three reviewers — despite
  [[2026-06-11-constraint-fence-scans-import-fence-re]] existing precisely to prevent that.
  The constraint is prose; there is no test that a module scanning `.md` imports `FENCE_RE`.
  **Likely shape:** a test enumerating modules that read markdown and asserting each
  imports the shared grammar — the same enumerating-test approach
  `tests/test_skill_contracts.py` already uses. **Trigger:** the third occurrence, or the
  next reader added to a scanning module.

## Backfill disposition (2026-08-22)

Triaged by `minerva:backfill-followups`. Every item above is unchanged; this section records where each one landed.

- **The repo's followup backlog is largely stale and nobody knows which parts.** → shipped — by this run. This item proposed exactly this tool, and its predicted disposition vocabulary (`shipped` / `still open` / `obsolete`) is the one `minerva:backfill-followups` implements
- **`unit_state` is half state-reader, half policy.** → open (low) — not filed at this pass; explicitly a no-action note unless a fifth consumer wants a different notion of 'in progress'
- **Nothing enforces that a new markdown scan is fence-aware.** → shipped — `tests/test_fence_awareness.py` exists and caught a live defect on its first run
