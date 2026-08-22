# Followups: enforce-fence-aware-scans

## 2026-08-11

- **The fence gate is per-module, not per-scan.** A fence-blind `.splitlines()` added to a
  module that already references the grammar elsewhere still passes. Per-scan checking needs
  real dataflow (does *this* iteration read markdown; does it go through a helper defined
  elsewhere), and a static approximation would fire on the fence helper's own `splitlines()`.
  Documented in the test rather than left implicit. **Trigger:** a violation that lands
  inside an already-aware module — that is the case this granularity cannot catch.

- **The two other follow-ups from `2026-08-11-close-the-followups` remain open**: the stale
  ~60-item backlog across 22 `followups.md` files with nothing marking items done, and the
  `unit_state` state-reader/policy split (a no-action note unless a fifth consumer wants a
  different notion of "in progress"). Neither was in scope here — this unit took the single
  small follow-up that fit `propose-ship-quick`.

## Backfill disposition (2026-08-22)

Triaged by `minerva:backfill-followups`. Every item above is unchanged; this section records where each one landed.

- **The fence gate is per-module, not per-scan.** → open (low) — not filed at this pass; the stated trigger is a violation landing inside an already-aware module
- **The two other follow-ups from `2026-08-11-close-the-followups` remain open** → not-an-item — a cross-reference to another file's items, dispositioned there
