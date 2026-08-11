# Fence-aware scans import the single-sourced fence grammar, whatever the corpus

**Date**: 2026-06-11
**Type**: constraint
**Context**: .minerva/work/2026-06-11-strengthen-pointer-guard

## Context
Work unit 036 added a fence-aware scanner over skill prose (`tests/test_skill_budget.py`) and hand-rolled its fence toggle. The hand-rolled grammar missed indented fences (caught by a completion panel) and tilde fences (caught when a partition panel spotted the re-derivation itself) — even though `scripts/knowledge_spans.py` already single-sources `FENCE_RE` (`^\s*(```|~~~)`), which handles both.

## Finding
Any fence-aware scan in this repo — over **any** corpus: wiki entries, skill prose, site files — uses the single-sourced fence grammar: import `FENCE_RE` from `scripts/knowledge_spans.py`, or a parser built on it (`_strip_fences` from the lint detector, as `synthesis_status.py` and `migration_status.py` do). Never re-derive the grammar.

[[2026-06-03-constraint-wiki-edge-derivation-fence-aware]]'s letter covers only wiki edge derivation and [[2026-06-02-constraint-knowledge-span-model-single-sourced]]'s letter only the wiki span model, so the author of the next scanner over a *new* corpus was routed nowhere — that routing gap is how 036 walked into the fence trap's fourth encounter (across three tool families and now two corpora; [[2026-06-03-bug-knowledge-edits-not-fence-aware]] records the third).

## Implications
- Writing any new scanner that must ignore fenced examples: import the grammar, per the same import-the-API pattern as [[2026-06-03-constraint-skill-wraps-script-via-importable-api]].
- The single known residual of `FENCE_RE` itself: 4-space indented literal blocks (zero live instances in the corpora scanned today; tracked in 036's followups.md).

## Related
- [[2026-06-02-constraint-knowledge-span-model-single-sourced]] — builds on
- [[2026-06-03-constraint-skill-wraps-script-via-importable-api]] — see also
- [[2026-06-03-constraint-wiki-edge-derivation-fence-aware]] — see also
- [[2026-06-03-bug-knowledge-edits-not-fence-aware]] — see also
- [[2026-07-27-constraint-agent-dispatch-pins-execution-mode]] — see also
- [[2026-08-11-pattern-a-comment-cannot-enforce-a-shared-invariant]] — see also
- [[2026-08-11-pattern-a-tolerant-reader-needs-a-boundary]] — see also
- [[2026-08-11-pattern-an-unenforced-constraint-is-aspirational]] — see also
