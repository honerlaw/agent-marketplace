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
- [3/3 accept] completion verification: all five criteria independently reproduced by each panelist (99/99 module, 279/279 suite, single-file commit, negative coverage genuine, CI-enumerated). Concerns carried to review: (1, med) fence tracker is column-0 only — indented fences in init/lint/replan treated as unfenced, latent; (2, med) Goal headline "close the prose-alias gap" overstates the delivered deterministic complement; (3, low) trailing-period token "references/foo.md." flagged malformed; (4, low) read-directive needle is raw substring.
- [2/3 quorum met, P+S both accept — Arbiter not dispatched, outcome mathematically fixed] review triage: FIX ×3 applied (lstrip fence toggle + indented-fence/nesting pin tests; Goal reworded to "deterministically checkable part"; rstrip('.') with ellipsis/foo. edge tests), IGNORE ×1 (substring needle — complementary check covers the contrived case). Residual logged for followups: tilde fences (~~~) and 4-space literal blocks unhandled, zero live instances.
