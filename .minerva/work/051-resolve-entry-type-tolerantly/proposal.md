# Proposal: resolve-entry-type-tolerantly

**Date**: 2026-08-09
**Status**: Shipped (2026-08-09)
**Base**: `origin/main`

## Goal

Resolve a knowledge entry's type from wherever the entry actually declares it, so an
entry written before the current template is catalogued and relocated like any other
instead of being permanently refused.

## Why

`parse_entry` reads the type from exactly one place — a body line matching
`^\*\*Type\*\*:\s*([a-z]+)`. Real corpora do not all look like that. Across the
629-entry corpus this was found in, **42 entries** have no type the parser can see,
and every one of them declares it somewhere:

| Where the type actually is | Entries |
|---|---|
| `Type: pattern` — plain, no bold | 16 |
| `**Type:** constraint` — colon inside the bold markers | 13 |
| only in the H1 (`# 426 — bug: …`) or nowhere in the body | 10 |
| only in YAML frontmatter (`metadata: type: bug`) | 3 |

The consequences are not cosmetic. `plan_index` buckets a catalog line under
`entries[stem]["parsed"]["declared_type"]`, so a `None` type means the line can never
be relocated to the right section, and an uncatalogued entry can never gain one at
all. `knowledge_lint` reports the same 42 as **25 hard errors** of the form
`entry X is type 'None' but catalogued under a 'constraint' section` — an error
naming a mismatch that the entry itself does not have.

This is the last big class of tooling-blocked entries after the stem-identity and
relation-label fixes. Those two took refusals from 838 to 66; 42 of the remaining 66
are this.

## Approach

Resolve `declared_type` from the first source that yields one, in descending order of
how deliberately the author stated it:

1. **A type field in the body**, matched tolerantly — `**Type**: x` (canonical),
   `**Type:** x` (colon inside the bold), and plain `Type: x`. All three are the
   author writing the field; only the punctuation drifted.
2. **YAML frontmatter `metadata.type`** — the template's machine-readable half, which
   3 entries carry without a body line.
3. **The filename's own type segment** — `ENTRY_RE` already captures it, so it costs
   nothing and it is the one source that ALWAYS exists.

The filename is last precisely because it is a fallback, but it is a trustworthy one:
across **642 entries in two corpora, filename type and declared type never once
disagree** (588 concordant + 0 divergent in the large corpus, 54 + 0 in this repo's
own). An entry whose body says one thing and whose name says another keeps the body's
answer, so the fallback can only ever fill a gap, never override an author.

### Rejected

- **Migrate the 42 entries.** Rewrites entries in a different repo to satisfy a
  parser that could simply read what they already say, and does nothing for the next
  corpus with legacy entries in it.
- **Only add the frontmatter fallback.** Covers 3 of 42 — I checked before assuming,
  which is how the plain-`Type:` and colon-inside variants surfaced.
- **Infer the type from the H1.** The 10 entries with no field encode it in prose
  (`# 426 — bug: …`). Parsing a title is guesswork where the filename is certain.

## Success criteria

1. All three body-field spellings resolve, and the canonical one is unchanged.
2. An entry with no body field but a frontmatter `metadata.type` resolves to it.
3. An entry with neither resolves to its filename's type segment.
4. A body field always wins over frontmatter and filename.
5. `parse_entry`'s return shape is unchanged — `declared_type` simply stops being
   `None` for entries that do declare a type.
6. Against the 629-entry corpus: entries with an unresolvable type go 42 → 0, and the
   25 `type 'None'` lint errors go to 0, with no new errors.
7. The existing suite still passes, plus new cases per criterion.

## Open questions

None. One adjacent question is deliberately **not** in this unit: `knowledge_lint`
still reports a shared NNN as a hard **error** (63 of them), which reads oddly now
that the fixer identifies entries by stem and handles collisions correctly. Whether
that should become a warning is a policy call about how much the convention still
matters, not a bug fix — recorded as a follow-up rather than decided here.
