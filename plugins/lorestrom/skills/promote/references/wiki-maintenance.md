# promote — knowledge-entry template + wiki maintenance

## Knowledge entry template

The `**Context**` field is a stable pointer that stays meaningful after the work-unit worktree is removed (`lorestrom:cleanup`): name the unit, `lorestrom unit <date-slug>`. Its records stay in Lorestrom, and `storage:knowledge.write` also records the unit's key as the entry's `minerva:context`.

The `**Theme**` and `**Summary**` fields are **required**. Together they are the entry's
catalog line: the knowledge catalog is never stored, it is derived on read by
`storage:knowledge.list`, which groups entries by `minerva:theme` and prints each one's
`minerva:summary` — both read from these lines. An entry missing either is invisible to
orientation, and the helper's `entry-payload` refuses it for any entry dated on or after
2026-10-01.

- **`**Summary**`** — the ≤15-word condensation of the Finding. Declarative, specific, no
  leading article.
- **`**Theme**`** — one lowercase kebab-case name (`knowledge-wiki`, `concurrency`).
  **Reuse an existing theme**; list them first from `storage:knowledge.list` (the distinct
  themes of this project's entries).

  Coin a new theme only when no existing one fits — a near-duplicate splits a group in
  the catalog, and lint warns about a theme only one entry uses.

```markdown
# <Short, declarative title — what was decided, fixed, or discovered>

**Date**: YYYY-MM-DD
**Type**: decision | bug | pattern | constraint | reference
**Theme**: <existing kebab-case theme — see `storage:knowledge.list`>
**Summary**: <≤15-word condensation of the Finding — the entry's catalog line>
**Context**: lorestrom unit <date-slug>

## Context
The situation that led to this entry. Constraints, prior state, or the
problem that was hit. Enough that a reader cold to the project understands
why this matters.

## Finding
What was decided, fixed, learned, or observed — stated as a declarative.
For bugs: what the root cause was and how it was fixed. For patterns: what
the recurring behavior is and when it appears. For decisions: what was
chosen. For constraints: what the limit is and where it comes from.

## Implications
What this means going forward — invariants other code now relies on,
things future work has to honor, gotchas to watch for, tradeoffs accepted.

## Related
- [[YYYY-MM-DD-type-slug]] — <relationship>
```

The `## Related` block is the canonical cross-reference surface. It holds **forward links
only**: `storage:knowledge.write` turns each line into a Lorestrom relation, and the reverse
direction is read from the relations (`get_relations` gives both), so promote never writes a
back-link into another entry. To retire an older entry, the new entry says so —
`- [[<old-stem>]] — supersedes` — and the relation marks the old one superseded once the
unit merges. Nothing is written into the old entry's body; a supersession banner is a legacy
form promote never writes.

## Wiki maintenance (add-only)

**A promote run writes new entries and their edges, and nothing else.** No catalog, no edit
to any existing entry's body, no supersession banner.

This is the invariant that makes concurrent work units safe. Each unit's writes are new docs
under its own gate, and an edge that touches an existing entry is held on that gate, so it
takes effect only when the unit merges and is discarded if it is abandoned. The catalog,
backlinks and supersession are computed from the entries and edges when they are read.

Do not edit an older entry "while you're here" to add a back-link or a banner. Every
shared or cross-entry write is a surface two concurrent units fight over.

### Entry naming

An entry's id is **today's date**, `YYYY-MM-DD`:

```bash
date +%F
```

There is nothing to allocate and nothing to scan. Dates are read off the clock, so two
units promoting concurrently never negotiate for an id, and **several entries sharing a
date is normal, not a collision** — identity is the whole `YYYY-MM-DD-<type>-<slug>`
stem.

Under stem identity a duplicate cannot ship silently: two entries with the same stem have
the same Lorestrom key, and a key another doc holds is refused rather than overwritten
(`storage:knowledge.write`).

Do not add a disambiguating suffix to "avoid" a shared date. If two entries on one day
really do share a type and slug, they are the same entry and want merging, not renaming.

### The maintenance step

For **each** newly-written knowledge entry, before the gate:

1. **Pick the theme.** List the themes (`storage:knowledge.list`) and reuse the theme whose
   existing entries this one belongs beside.
2. **Neighbor discovery (recall-complete floor).** List the catalog
   (`storage:knowledge.list`) to narrow candidates by theme and summary,
   then read the Findings of the plausible neighbours and identify genuine relationships.
   Dedup candidate hits by target **stem**: a date is shared by design, so deduping on the
   id alone would collapse distinct same-day entries into one.
3. **Write forward links only.** Record each relationship as a `## Related` line
   **in the new entry**: `- [[YYYY-MM-DD-type-slug]] — <relationship>`.

   The label is normally a short sentence saying what the edge *is* — that is what
   makes the wiki navigable. `supersedes` is matched as a term: a label that starts with
   it (optionally followed by `:` and an explanation) retires the target in the derived
   catalog. Use it only when the new entry genuinely replaces the old one.

   Do **not** write anything into the neighbor's body.
4. **Gate.** Surface the new entries' text, and every edge onto an existing entry, in the
   same confirmation gate that approves the promote (Mode A step 6 / Mode B step 4). There
   are no neighbor body or catalog changes to show — if you find yourself with one,
   something has gone wrong.

### Idempotency

Re-running promote is a no-op on an entry that already exists: its key is derived from
the date and slug rather than allocated, a retry finishes its own entry under the unit's
gate (`storage:knowledge.write`), and a `## Related` line
is added only if no existing line in that block references the target **stem**
(insert-iff-absent, set semantics keyed on the stem — keying on the id would treat two
same-day entries as one and silently drop the second relationship). Promote never edits
any entry other than the one it is currently writing.
