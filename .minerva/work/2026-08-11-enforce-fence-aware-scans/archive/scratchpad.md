# Scratchpad: enforce-fence-aware-scans

## Quick decisions 2026-08-11
- [decided] scope: the seed "followup" (singular) under `quick` resolves to ONE of the three
  open follow-ups. The backlog triage is ~60 items across 22 files and would trip the
  scope-fit escape immediately; the `unit_state` half-policy note is explicitly no-action.
  The fence-awareness test is the only one that is genuinely small, so it is dominant given
  the orchestrator chosen — decided rather than escalated.
- [decided] scope widened by evidence, still small: the enforcement finds a real defect on
  first run (`knowledge_fix.plan_index` scans index.md fence-blind while
  `knowledge_lint.parse_index` scans it fence-aware). Fixing what the new check catches is
  part of adding the check, not a separate unit — one guard plus one test module.
- [decided] approach: deny-by-default over the corpus (every `.splitlines()` in scripts/
  must reference the shared grammar) with a self-documenting `# not-markdown: <reason>`
  escape at the call site. Rejected a curated list of markdown-scanning modules: that is a
  hand-maintained enumeration, which this repo has just twice been bitten by, and it decays
  in the dangerous direction because an omitted module reads as checked.
- [decided] whole-proposal soundness: additive test plus a one-line guard in an existing
  scan. No public interface changes.
- [decided] completion verification (never elided): all 6 criteria met against the diff.
  Both fixtures verified to FAIL against origin/main, and the enforcing test itself flagged
  `knowledge_fix.py` when the fix was reverted — the gate catching the defect it was written
  for is the check that it is not vacuous.
- [decided] review triage (solo): two findings, both my own, both FIXED. (1) The gate is
  per-MODULE, not per-scan: a second fence-blind scan added to an already-aware module would
  pass. Per-scan needs real dataflow and a static approximation would fire on the fence
  helper's own splitlines. Kept module granularity — it is what both real violations needed —
  but documented rather than left to be discovered, since overclaiming a gate is the failure
  this unit is about. (2) `MODULES` filtered out `_`-prefixed files for no reason; a
  deny-by-default gate that silently skips a filename pattern is the gap it exists to close.
  Filter removed.
- [decided] promote partition (solo): PROMOTE one entry — a documented constraint with no
  enforcing test is aspirational, and the enforcement finds violations on its first run.
  MERGE: proposal Approach matches what shipped. DISCARD: routine decision lines.
