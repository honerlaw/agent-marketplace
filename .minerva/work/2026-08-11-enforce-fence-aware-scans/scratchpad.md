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
