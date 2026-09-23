# Scratchpad: follow-ups-must-earn-filing

## Quick decisions 2026-09-23
- [decided] scope check: single unit, one PR — policy text in one reference file plus pointer/summary updates and one test file
- [decided] approach: extend the single-sourced bar with value + size conditions and a fix-now outlet; retire `medium` (rejected: hard numeric cap — drops real criticals; keep-but-forbid `medium` — dead vocabulary)
- [decided] whole-proposal soundness: user specified the rule directly in chat; no public interface beyond the skill prose itself
- [decided] completion verification: 5/5 criteria met — bar states 3 conditions + fix-now outlet + soft cap; priority table {critical, high}; review triage FIX no longer diff-bound; consumer pointer tests pass; pytest 1081 passed

## Work notes
- `test_no_skill_prose_uses_a_priority_level_the_table_does_not_define` caught a `priority: medium` sample in `status/references/tables.md` that no grep of the promote/review files would have found; changed the sample to critical/high.
- Existing open followups (#98, #113) stay `priority: medium` — the bar is not retroactive.

## Review triage 2026-09-23
- [FIXED] #1 med promote/SKILL.md description — still framed TODOs as filed-by-default; now names fix-now and the urgent+too-large filing condition
- [FIXED] #2 low-med orchestrator triage summaries had no branch for a too-large, non-urgent defect (fell through to IGNORE); now SUGGEST as a standing fact
- [FIXED] #3 high fix-now at promote would ship unreviewed code; promote now stops, fixes, and routes the commits back through review before re-running
- [FIXED] #4 med ordering of promote-time fix vs. scratchpad archive — resolved by #3 (fix happens before promote writes anything)
- [FIXED] #5 med absorbed out-of-diff fixes collided with review's scope-creep lens; `- Absorbed fix:` log line marks them in scope
- [FIXED] #6 low soft-cap justification location undefined outside orchestrators; now in the second issue's body + promote report
- [FIXED] #7 low (pre-existing) bar said "no fifth outlet" while promote offers seed-new-proposal; bar now names it
- [decided] triage: all seven have concrete failure scenarios and are absorbable — FIX (applying the new bar to itself)
- Review fix: promote/SKILL.md frontmatter — a `: ` inside the description broke YAML parsing; caught by test_skill_contracts
