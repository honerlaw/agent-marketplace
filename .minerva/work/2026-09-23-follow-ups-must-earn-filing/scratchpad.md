# Scratchpad: follow-ups-must-earn-filing

## Quick decisions 2026-09-23
- [decided] scope check: single unit, one PR — policy text in one reference file plus pointer/summary updates and one test file
- [decided] approach: extend the single-sourced bar with value + size conditions and a fix-now outlet; retire `medium` (rejected: hard numeric cap — drops real criticals; keep-but-forbid `medium` — dead vocabulary)
- [decided] whole-proposal soundness: user specified the rule directly in chat; no public interface beyond the skill prose itself
- [decided] completion verification: 5/5 criteria met — bar states 3 conditions + fix-now outlet + soft cap; priority table {critical, high}; review triage FIX no longer diff-bound; consumer pointer tests pass; pytest 1081 passed

## Work notes
- `test_no_skill_prose_uses_a_priority_level_the_table_does_not_define` caught a `priority: medium` sample in `status/references/tables.md` that no grep of the promote/review files would have found; changed the sample to critical/high.
- Existing open followups (#98, #113) stay `priority: medium` — the bar is not retroactive.
