# Proposal: close-silent-reference-gaps

**Date**: 2026-08-11
**Status**: Draft
**Base**: `origin/main`

## Goal

Close six defects in which a knowledge tool's model of "a reference" is narrower — or
wider — than the reference forms real corpora contain, and make the load-bearing one
(the lint/fix edge-model divergence) impossible by construction rather than by
inspection.

## Why

All six were found by running `minerva:migrate-fix` against a real external 637-entry
corpus, and every one was re-verified against this repo's source before this proposal
was written. They share a single failure shape, which is what makes them one unit:
**the pattern is wrong, and being wrong is silent.** Nothing errors, nothing refuses,
so the project's own gate reads clean while real rot accumulates.

| # | Defect | Site | Observed |
|---|---|---|---|
| 1 | lint and fix disagree on what counts as an edge | `knowledge_lint.py` / `knowledge_fix.py` | 18 of 41 findings neither planned nor refused |
| 2 | `rewrite_links` ignores bare `.md` path references | `knowledge_rename.py` | 182 references broken, undetectable by lint |
| 3 | `CONTEXT_PATH_RE` captures trailing punctuation | `knowledge_rename.py:82` | 4 paths silently skipped |
| 4 | bare `[[NNN]]` shorthand silently degraded | `knowledge_rename.py` | 563 refs across 185 files |
| 5 | migrate-fix's verification grep false-positives | `skills/migrate-fix/SKILL.md:72` | 6,005 hits vs 26 real |
| 6 | lint's orphan query keys on the id prefix | `skills/lint/SKILL.md:72` | 0 orphans vs 14 pre-migration |

**Defect 1 is the worst and the least visible.** `RELATED_LINE_RE`'s own comment states
the invariant it violates: "Single-sourced so `knowledge_fix` cannot recognise a
narrower set of edges than this linter reports on — a line the linter counts as an edge
but the fixer skips is a permanent error nothing repairs and nothing refuses." The
comment is true about the regex and false about the code: `knowledge_fix` imports
`RELATED_LINE_RE`, but `knowledge_lint.parse_entry` derives its own edges with
`CATALOG_LINE_RE`, which is start-anchored only. Measured:

```
line                                                lint(CATALOG)  fix(RELATED)
- [[a]] — supersedes                                True           True
- [[a]] / [[b]] — both unchanged                    True           False
- [[a]] /                                           True           False
```

So a convergence loop stalls forever: lint reports a missing reciprocal, the fixer
prints "corpus clean", and no run in between ever refuses anything.

**Defect 2 is the one that destroys data.** `knowledge_rename` is a writer that moves
every entry in a corpus. It retargets wikilinks, `<!-- superseded-by: -->` markers and
`**Context**: .minerva/work/…` paths — but not `.minerva/knowledge/<stem>.md` written
in prose or backticks, and not markdown links `[text](<stem>.md)`. Because the gate
does not model that form either, all 182 broken references read clean before and after.

## Approach

### 1. Single-source the edge model (defect 1)

Extract one `related_edges(text) -> [(stem, label)]` in `knowledge_lint.py` that owns
the whole "read a `## Related` block" operation — fence-stripping, last-`## Related`-
header block selection, per-line parse. `parse_entry` and `knowledge_fix._forward_related`
both call it. There is then no second regex left to drift, which is the same rule
[[2026-06-02-constraint-knowledge-span-model-single-sourced]] already imposes on the
span model, applied to the edge model.

**The semantic it commits to:** every wikilink in the block is an edge; a label is
carried only when the line is unambiguously `- [[one-target]] — label`, otherwise the
label is `None`.

This direction is dominant, not a coin flip, and the deciding evidence is already in
the code. `plan_reciprocals` has a `label is None` branch that appends a **refusal**:
"forward `## Related` line has no relationship label; cannot derive the reciprocal."
So the fixer already knows how to handle an edge it cannot label — visibly, by
refusing. Widening the edge set therefore converts exactly the reported failure
(*neither planned nor refused — invisible*) into a refusal, with no new machinery. The
two alternatives both fail:

- **Narrow lint to `RELATED_LINE_RE`.** Silently drops broken-link and
  missing-reciprocal coverage on multi-target lines, and contradicts a pinned
  behaviour: `test_second_link_on_a_related_line_counts_as_a_back_link` already
  establishes that a second link on a Related line *is* a real edge inbound. Counting
  it inbound but not outbound makes an entry simultaneously linked and not-linked.
- **Widen fix to auto-write a reciprocal from a multi-target line.** It would have to
  invent a label out of a line tail like `both unchanged`, writing a wrong edge into a
  neighbouring entry. The refusal path exists precisely so it doesn't.

Measured on this repo's 62-entry corpus: **0 lines diverge**, so the widening is inert
here and cannot introduce a new finding on the CI gate. Coverage therefore comes from
fixtures, not from the live corpus.

### 2. Teach `rewrite_links` the two missing reference forms (defect 2)

Add `.minerva/knowledge/<stem>.md` (prose and backtick) and relative markdown links
`](<stem>.md)`. Both go through the same **map-lookup-only** discipline `rewrite_links`
already documents: a stem absent from the rename map is left byte-identical. That is
what bounds the blast radius — the function cannot invent a target, only retarget one
it is already renaming.

### 3. Exclude trailing punctuation from the path patterns (defect 3)

Add `,.;:` to the excluded character class in `CONTEXT_PATH_RE`, and use the same class
in the new knowledge-path pattern so the two cannot drift apart. Safe against the
naming convention: slugs are kebab-case and contain none of these.

### 4. Count bare `[[NNN]]` shorthand; never resolve it (defect 4)

`plan()` gains a read-only content scan and a `shorthand_refs` field, surfaced by the
CLI the way `undated` already is. This is a small **output-contract addition**, not a
pattern fix, and is called out as such: `plan()` today reads only filenames and `git
log` dates, so the file walk is factored so `plan()` and `apply()` share it.

Deliberately **not** auto-resolved. The reporting session tried: in ~6 of 23 cases
where a bare number named exactly one entry, the intended referent was something else —
often the same-numbered *work unit*, one of them literally annotated "(work unit)" in
the prose. Not rewriting is defensible; doing it silently is not.

### 5 & 6. Fix the two SKILL.md snippets — with executable coverage

- **migrate-fix's verification grep** matches `[0-9]{3,}`, which matches `2026`. Replace
  with a form that excludes date ids. Verified: on a fixture holding one migrated and
  one legacy link, the current grep returns both, the replacement returns only the
  legacy one.
- **lint's orphan query** keys `inbound` on `e['nnn']`, which under date ids is the
  *date*, collapsing the corpus into date buckets. Re-key on stems using the
  `related_out_stems` / `backlink_stems` twins `knowledge_lint` already exposes.

Both are snippets embedded in markdown, which today has no executable regression
coverage — `tests/test_skill_contracts.py` checks `anchors`, and those are
presence-only assertions, the exact shape
[[2026-08-10-pattern-presence-assertions-rot-into-green-lies]] warns rots into a green
lie. So rather than pinning prose, the tests **extract each snippet from its SKILL.md
and execute it** against a fixture: the grep must not match `[[2026-05-19-decision-foo]]`
and must match `[[015-decision-legacy]]`; the orphan one-liner must find a planted
orphan in a date-id corpus. A snippet that regresses then fails CI instead of passing a
substring check.

### Rejected

- **Fix each defect at its own site (no extraction).** Re-establishes agreement between
  two regexes that the next edit can silently break again — which is exactly how defect
  1 arose, since the comment claiming single-sourcing is already there.
- **Ship 1 and 2 now, defer 3–6.** Leaves four known-silent defects live in a
  corpus-mutating tool, and defects 3 and 4 live in the same function as 2, so it means
  touching `rewrite_links` twice.

## Success criteria

1. `knowledge_lint` and `knowledge_fix` derive `## Related` edges from one shared
   function; no second edge regex remains in either module.
2. A multi-target Related line (`- [[a]] / [[b]] — label`) yields edges to both targets
   in lint, and in fix produces a visible **refusal** rather than silence or a
   fabricated label.
3. `rewrite_links` retargets `.minerva/knowledge/<stem>.md` and `](<stem>.md)`, and
   leaves a stem absent from the map byte-identical.
4. A `**Context**` path with trailing `,` or `.` resolves through the map.
5. `plan()` reports a count of bare `[[NNN]]` shorthand references; no such reference is
   rewritten.
6. The migrate-fix verification grep matches legacy ids and not date ids; the lint
   orphan snippet finds a planted orphan in a date-id corpus. Both are asserted by
   tests that **execute the extracted snippet**, not by substring presence.
7. Regression fixtures exist for each of the six defects, and each fails before its fix.
8. The CI-enumerated suite passes (baseline: 437), `knowledge_lint .minerva/knowledge`
   stays clean, and any new test module is appended to the enumerated list in
   `.github/workflows/evals.yml` per
   [[2026-06-11-constraint-ci-test-enumeration-explicit]].

## Open questions

None blocking. One adjacent item is deliberately out of scope: the reporting session
noted that number-based resolution of bare `[[NNN]]` shorthand is wrong often enough to
refuse, but a *slug-first* resolver (resolve by slug, fall back to number, refuse the
rest) might be worth building later. That is a new capability with its own accuracy
question, not a defect fix — recorded as a follow-up rather than bundled here.
