# Replan log: related-backfill (027)

## 2026-06-03 — knowledge_edits.py is not fence-aware (panel: 2/2 divergence, 3/3 new-plan)

**Original plan.** Backfill `## Related` edges for the 9 inventoried entries (done,
committed, detector-clean) + promote (entry 027 with cross-refs incl. `see also [[015]]`)
+ post-promote synthesize. No code surfaces; criterion 6: `knowledge_lint.py` /
`knowledge_fix.py` / `knowledge_spans.py` untouched.

**What changed.** The fixer crashed (pre-write — its all-or-nothing validation left zero
damage) while adding 027's reciprocal INTO entry 015: `body_complement`,
`_related_has_target`, and `add_related_link`'s header check in
`scripts/knowledge_edits.py` scan raw splitlines — **not fence-aware**. Entry 015's
FENCED `## Related` convention example trips `body_complement`'s terminal-section assert
(crash), opens `_related_has_target` to a silent false-dedupe on prose `[[…]]` mentions
after the fenced header, and would make `add_related_link` append a malformed bare line
on a fenced-only-header entry. Third instance of the recurring trap
[[2026-06-03-constraint-wiki-edge-derivation-fence-aware]] records — and whose Implications
explicitly mandate fixing ("a tool that parses the `## Related` block itself … must be
fence-aware too"). Latent landmine: any future edge → 015 broke promote's own
maintenance path.

**New plan (additive; the completed backfill is unchanged).**
1. Make the editors fence-aware with **header-location-only** semantics: a shared
   `_fence_flags` helper (FENCE_RE imported from `knowledge_spans.py` per 019) decides
   which lines count as *structure* in `body_complement` (header location + terminal
   assert + banner marker), `_related_has_target`, and `add_related_link`'s header
   check. **Fenced lines are never dropped from the complement** — they are body content
   under the byte-identity guard (deliberately NOT a `_strip_fences` content filter).
2. Three regression tests in `tests/test_promote_invariant.py`: the 015-shaped crash
   case (complement preserves the fenced example), the prose-after-fence false-dedupe
   case, and the fenced-only-header real-block-creation case. The 7 existing property
   tests pass unchanged.
3. Resume the promote: fixer pass lands the three 027 reciprocals (015/016/026);
   detector clean.
4. Promote records an additional **bug** knowledge entry for the latent landmine (the
   instance), cross-referencing 023 (the standing constraint). `add_supersede_banner`'s
   analogous insert-position scan is recorded there in writing as the remaining dormant
   variant (no triggering entry shape exists in-corpus; deferred deliberately, not
   silently).

**Success-criteria change.** Criterion 8 added: "`body_complement`,
`_related_has_target`, and `add_related_link` are fence-aware (header-location-only, via
`_fence_flags`/FENCE_RE); the crash, false-dedupe, and fenced-only-header cases are
covered in `tests/test_promote_invariant.py` and green; the 7 existing property tests
pass unchanged." Criterion 6 unchanged (`knowledge_edits.py` was never in the untouched
list).
