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
