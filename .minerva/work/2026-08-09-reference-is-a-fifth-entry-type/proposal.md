# Proposal: reference-is-a-fifth-entry-type

**Date**: 2026-08-09
**Status**: Shipped (2026-08-09)
**Base**: `origin/main`

## Goal

Admit `reference` as a real knowledge-entry type, with its own `## References` index
section, so entries authors have already written that way are catalogued instead of
refused.

## Why

The wiki's type vocabulary is four values — `decision` / `bug` / `pattern` /
`constraint` — hardcoded in `SECTION_TO_TYPE` (lint) and `SECTION_ORDER` (fix), and
enumerated in four skill docs. Authors have written `reference` entries anyway: four of
them in the corpus this surfaced in, covering how the blue-green search-index migration
is actually run, what the repo-local eslint plugin is and why, a curated followups
backlog, and a known-noise wontfix list.

The tooling has nowhere to put them. `plan_index` cannot place a line whose declared
type has no section, so those entries are refused with `entry X is type 'reference'
but catalogued under a 'constraint' section` — the last errors left after unit 051.
The refusal is honest, but it is a standoff: the entries are useful, they are cited by
name in a consumer's `CLAUDE.md`, and nothing about them is going to change.

The alternative reading — that `reference` material belongs in `.minerva/reference/`,
minerva's documented home for present-tense operational docs — is real, and it is why
this was escalated rather than decided. **Owner decision (2026-08-09): add the fifth
section.** Four independent authorings are evidence of a gap in the vocabulary, not four
mistakes; and a `reference` *entry* differs from a `.minerva/reference/` *doc* in the
way every entry differs from a doc — it is atomic, numbered, cross-linked and
catalogued, not a maintained operational page.

## Approach

Add `reference` alongside the existing four, everywhere the four are enumerated:

- **`knowledge_lint.SECTION_TO_TYPE`** — `"## References": "reference"`.
- **`knowledge_fix.SECTION_ORDER`** — append `"## References"`. Last, not
  interleaved: the canonical skeleton order is stable and existing indexes already
  render four sections in that order, so appending is the only position that leaves
  every current index's line order unchanged.
- **The `minerva:init` index skeleton** — the fifth header.
- **The four docs that enumerate the type vocabulary** — `promote`'s `modes.md` (two
  sites) and `wiki-maintenance.md`, `debug`'s `workflow.md`, and `migrate`'s
  illustrative list.

An empty section renders as its header alone (the canonical-skeleton rule already in
`plan_index`), so a corpus with no `reference` entries gains one inert `## References`
line in `index.md` at its next reconciliation and nothing else.

## Success criteria

1. A `reference`-typed entry is catalogued under `## References`, and a line filed
   under the wrong section is relocated there.
2. The four existing types are unaffected — same sections, same order, same lines.
3. A corpus with no `reference` entries gains only the empty `## References` header.
4. `knowledge_lint` no longer reports `type 'reference' but catalogued under …`.
5. The index skeleton `minerva:init` writes, and every doc enumerating the vocabulary,
   name five types.
6. Existing tests pass; new tests cover criteria 1–3.

## Open questions

None. Two follow-ups from unit 051 are **not** in this unit:

- **The shared-NNN severity question re-scoped.** Investigating it found the real
  defect underneath: `knowledge_lint` still keys entries by NNN and explicitly
  quarantines duplicate ids from every per-entry check, so ~130 entries in the large
  corpus are invisible to the linter. That is the same defect unit 051's predecessor
  fixed in `knowledge_fix` and never fixed here. Downgrading the severity *first* would
  be backwards — while the quarantine exists, a shared NNN genuinely does degrade
  linting, which is what an error should say. Fix the identity model, then the severity
  follows. It is threaded through ~10 call sites plus `parse_index`'s NNN-keyed
  catalog, so it is its own unit.
- **Ten entries encoding their type only in a prose H1.** The filename fallback from
  unit 051 resolves them correctly and nothing is broken; adding a field by parsing a
  title is the guesswork that unit declined. Closed, no action.
