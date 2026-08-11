# Scratchpad: knowledge-lint-detector

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `minerva:promote`: significant items get promoted to
> `.minerva/knowledge/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.

## Panel decisions 2026-06-02

- [1/3 accept → revise/DECOMPOSE] scope check r1: original bundled a deterministic detector + an LLM-judged interactive skill. Skeptic+Arbiter: split per the 017/018 precedent (deterministic floor vs LLM-judged layer) + knowledge 013 (LLM-judged output provisional, must not co-gate). Re-cut to Unit 1 (detector) only; Unit 2 (minerva:lint skill) deferred.
- [3/3 accept] scope check r2: Unit 1 (deterministic detector + tests + evals.yml live-dir gate, no skill) is a single cohesive tooling unit; matches 018/020 tooling precedent; 010/012 don't fire (no skill).
- [3/3 accept] approach selection: X (scripts/knowledge_lint.py importable fns + CLI exit-nonzero, run in evals.yml) over Y (pure-pytest, can't be Bash-invoked by Unit 2) and Z (JSON lib, can't be a gate). Skeptic accepted with 6 parser conditions (all folded into the proposal).
- [1/3 accept → revise] whole-proposal r1: Skeptic+Arbiter found 6 corpus-verified spec-precision fixes (shared-constants module + import direction; banner anchored not substring; reciprocity presence-not-label; last-non-fenced block selection; inline-prose-not-edge; exclude index.md). 4 of them determine correctness on the live corpus.
- [3/3 accept] whole-proposal r2: all 6 fixes folded; both panelists re-verified against the live corpus (banner prose-mentions excluded, exactly-7 label-match FPs avoided, 015 fenced+real block disambiguated, bijection clean). LOW residual (helper fns stay in test, only constants move) resolved.

## Carried concerns (from panels)

- CI live-dir gate must pass on the current clean corpus (watermark 017, 17 entries, reciprocal, no broken links) — verified by panels.
- Banner detection: anchored regex + above-first-`##`, NEVER substring (015/016 mention the string in prose).
- Reciprocity: presence keyed on NNN, NEVER label-match (builds on↔see also → 7 FPs otherwise).
- Block: last non-fenced `## Related` → EOF (015 has a fenced example + the real block).
- Only span CONSTANTS move to scripts/knowledge_spans.py; add_related_link/add_supersede_banner/body_complement stay in test_promote_invariant.py.

## Implementation log 2026-06-02

- scripts/knowledge_spans.py: extracted shared constants (BANNER_MARKER_RE, BANNER_QUOTE_RE, RELATED_HEADER, SECTION_RE) + added FENCE_RE. test_promote_invariant.py rewritten to import them (dropped its now-unused `import re`); its 7 tests still pass (value-preserving extraction).
- scripts/knowledge_lint.py: deterministic read-only detector. parse_entry (fence-aware: banner markers above first `## `; ## Related = last non-fenced header → EOF; links by NNN), parse_index (watermark, catalog NNN→section/stem, index.md excluded from entry set), lint_knowledge → list[Finding(family,severity,message)], main() CLI exits 1 iff any error-severity finding. Checks: index drift (watermark/bijection/Type-section; slug mismatch = warning), broken `## Related` links, missing reciprocals (presence keyed on NNN, back-link in ## Related OR banner).
- tests/test_knowledge_lint.py: 16 tests — clean corpus; each defect family flagged; slug-mismatch-is-warning; one-way-reciprocal = pure missing-back-NNN; false-positive guards (builds-on/see-also pair, banner-only back-link, fenced `## Related` example, inline-prose link, prose-mention-of-banner-string); CLI exit codes; test_live_knowledge_clean.
- evals.yml: added test_knowledge_lint.py to the gated pytest list + a "Knowledge-wiki drift gate" step running the CLI on the live dir.
- Verified: full gated suite 112 passed; CLI exits 0 on live `.minerva/knowledge/`; run_skill_evals --dry-run still ok.
- No skill added → constraints 010/012 don't fire (no catalog rows, no contract.json). Gate is deterministic-only (honors 013).
- Banner-back-link path has no live coverage (no superseded entries exist yet) — exercised only by fixture, as expected.

## Panel decisions 2026-06-02 (continued)

- [3/3 accept] completion verification: all 7 success criteria met; panel ran the CLI (exit 0) + suite (112 passed) + live-mutation probes (bump watermark → exit 1; delete back-link → reciprocal error). Skeptic caught a vacuous fence test → FIXED (fenced example moved AFTER the real block; verified discriminating via fence-disable probe); re-verified 3/3.
- [skipped — small] review triage: 3 LOW findings, single file (knowledge_lint.py), additive/polish, no interface/constraint impact → triaged directly.

## Review finding 2026-06-02

Inline review (spec-fidelity + knowledge-compliance clean):
1. [low] dead/duplicate `or re.match(...)` fallback in parse_entry (unreachable; identical to CATALOG_LINE_RE) → FIXED.
2. [low] duplicate-NNN files would silently collapse (dict keyed by NNN, last-writer-wins) → FOLLOWUP (a new check; can't occur in a promote-managed corpus, NNN is auto-incremented).
3. [low] missing-watermark message was terse (`watermark None != ...`) → FIXED (special-cased: "index.md has no `index-watermark` comment").
