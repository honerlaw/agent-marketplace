# Scratchpad: strengthen-pointer-guard

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `minerva:promote`: significant items get promoted to
> `.minerva/knowledge/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.

## Panel decisions 2026-06-11

- [skipped — small] scope check: single additive unit = 035 followup #1 only (evidence: scan shows test-file-only change — zero malformed pointers, zero skill-text edits needed; followup #2 deferred on its own recorded gate in 035/followups.md — token measurements, none exist in repo)
- [skipped — small] approach selection: extend test_skill_budget.py with malformed-pointer + per-file read-directive checks (rejected: B canonical-pointer-syntax rewrite — churns 9 skills for no extra guarantee given scan shows corpus already passes; C LLM-judged advisory lint — non-deterministic, doesn't strengthen the CI floor the followup names)
- [skipped — small] whole-proposal acceptance: single-surface (one test file), criteria objectively checkable, no skill-text changes (evidence: same scan; knowledge 035 satisfied — module already CI-enumerated)
