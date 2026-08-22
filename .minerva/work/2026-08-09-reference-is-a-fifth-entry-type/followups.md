# Follow-ups: 052-reference-is-a-fifth-entry-type

## 1. `knowledge_lint` still keys entries by NNN, and quarantines duplicates

**The re-scoped version of unit 051's followup 1.** That followup asked whether a shared
NNN should stay a hard `error` now the fixer keys on stems. Investigating it found the
defect underneath the question:

`lint_knowledge` builds `entries = {nnn: (group[0], parse_entry(group[0]))}` — one
arbitrary member per NNN — and then explicitly **skips duplicate ids in every per-entry
check** (`if nnn in duplicate_nnns: continue`, three times). In the large corpus that is
63 shared NNNs covering ~130 entries, none of which are type-checked, slug-checked, or
link-checked at all. The linter reports them as errors and then looks away.

So the severity question cannot be answered first. While the quarantine stands, a shared
NNN genuinely does degrade linting, which is exactly what an `error` should say.
**Fix the identity model, then the severity follows** — at which point `warning` is
almost certainly right, since nothing else downstream breaks (verified: seekless does not
wire `knowledge_lint` into CI, and zero `supersedes` edges touch a shared NNN, so the one
remaining consequence — the banner refusal — is both hypothetical and already reported
precisely by `knowledge_fix`).

Not small: NNN keying is threaded through ~10 call sites plus `parse_index`, whose
`catalog` is itself `{nnn: …}` and is compared against `entry_nnns` on both sides. That
is a wider refactor than the fixer's was. **Recommend `minerva:propose-ship-balanced`** —
same shape as the fixer change it mirrors, and worth one independent reviewer because the
linter is the CI gate in this repo.

## 2. Ten entries encode their type only in a prose H1 — CLOSED

`# 426 — bug: dontAsk mode auto-denies …`. Unit 051's filename fallback resolves all ten
correctly, so nothing is broken and no tool is blocked. Writing a `**Type**` field by
parsing a title is the guesswork unit 051 deliberately declined, and doing it to ten
entries in a consumer repo buys nothing. Recorded as closed rather than left open so it
is not re-derived a third time.

## 3. Consumer indexes gain a `## References` header on next reconcile

Expected and inert, but worth knowing before someone sees the diff: every consumer repo's
`index.md` gains one empty `## References` line the first time reconciliation runs after
this ships. No existing line moves (the section is appended, never interleaved).

## Backfill disposition (2026-08-22)

Triaged by `minerva:backfill-followups`. Every item above is unchanged; this section records where each one landed.

- ## 1. `knowledge_lint` still keys entries by NNN, and quarantines duplicates → shipped — stem identity landed; `parse_index` is keyed on the full stem and duplicates are no longer excluded from per-entry checks
- ## 2. Ten entries encode their type only in a prose H1 — CLOSED → shipped — marked CLOSED by its own author
- ## 3. Consumer indexes gain a `## References` header on next reconcile → not-an-item — a heads-up about an expected, inert diff, not a task
