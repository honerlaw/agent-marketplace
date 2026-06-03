# `minerva:promote` may edit an existing knowledge entry only within its `## Related` block and supersession-banner span — entry bodies are append-only

**Date**: 2026-06-02
**Type**: constraint
**Context**: .minerva/work/020-knowledge-wiki-navigability (see git history if the worktree has been cleaned up)

## Context
`minerva:promote` historically only ever appended *new* knowledge files; its documented invariant was "knowledge files are never overwritten." Work unit 020 made promote maintain **bidirectional** cross-references (see [[015-constraint-knowledge-cross-reference-convention]]), which requires editing *existing* neighbor entries to add reciprocal links and supersession banners. That collides with a literal never-overwrite reading, so the invariant had to be narrowed precisely rather than abandoned.

## Finding
The never-overwrite invariant is narrowed, not dropped:

- The **body** of an existing entry — its `# H1`/metadata block and the `## Context` / `## Finding` / `## Implications` sections — stays strictly **append-only** and is never rewritten by promote.
- The **only** machine-managed mutable surfaces are (1) the delimited trailing `## Related` block and (2) the supersession-banner span (the `<!-- superseded-by: NNN -->` marker + its `> **Superseded by …**` line, sitting between the metadata block and the first `## ` header).
- Edits are **idempotent**: a `## Related` line is added only if no line already references that target NNN; a banner only if no marker for that superseding NNN exists; an index line only if absent (watermark bumps only on an actual index change). Re-running promote (either mode) is a byte-level no-op on already-present links/banners/index lines, so a later Mode A full pass is a no-op over a Mode-B-touched entry.
- All neighbor + index edits are surfaced as concrete diffs in promote's **existing** confirmation gate (Mode A step 6 / Mode B step 4) and written only on approval (Mode A step 7 / Mode B step 5).

This invariant is **mechanically guarded** by `tests/test_promote_invariant.py` (in the `evals.yml` CI gate): it provides a reference implementation of the two allowed mutations and asserts the *complement* of the two spans is byte-identical before/after, plus idempotency and an already-linked-pair zero-diff case.

## Implications
- Any future change to promote (or any tool that edits knowledge files) must keep entry bodies append-only and confine edits to the `## Related`/banner spans, or the guard test fails. Update the test deliberately if the span model itself changes — don't weaken it to pass.
- The guard test embodies a reusable technique: a **behavioral invariant of a prose skill** (a `SKILL.md` executed by an LLM, with no callable function to unit-test) is enforced via a *reference implementation + property tests* registered in the deterministic eval gate — the behavioral-invariant complement to the structural-contract floor in [[012-constraint-skill-structural-contracts]].
- `## Related` must be the entry's terminal section and the banner the only pre-`## ` content, so the two mutable spans stay unambiguous (see [[015-constraint-knowledge-cross-reference-convention]]).

## Related
- [[015-constraint-knowledge-cross-reference-convention]] — see also
- [[017-decision-knowledge-wiki-navigability-layer]] — builds on
- [[012-constraint-skill-structural-contracts]] — builds on
