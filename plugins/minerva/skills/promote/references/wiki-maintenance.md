# promote — knowledge-entry template + wiki maintenance

## Knowledge entry template

The `**Context**` field is a stable pointer that should remain meaningful even after the work-unit worktree is removed (`minerva:cleanup`). Use the canonical `.minerva/work/<date-slug>` path even if the actual files currently live in a worktree — after merge + cleanup, the docs are reconstructible from git history at that path on the merge commit.

The `**Theme**` and `**Summary**` fields are **required**. Together they are the entry's
catalog line: the knowledge catalog is never stored, it is derived on read by
`knowledge_catalog.py` (and the Routing section's one-liner), which groups entries by
`**Theme**` and prints each one's `**Summary**`. An entry missing either is invisible to
orientation, and `knowledge_lint` errors on it for any entry dated on or after 2026-10-01.

- **`**Summary**`** — the ≤15-word condensation of the Finding. Declarative, specific, no
  leading article.
- **`**Theme**`** — one lowercase kebab-case name (`knowledge-wiki`, `concurrency`).
  **Reuse an existing theme**; list them first:

  ```bash
  ROOT="$(git rev-parse --show-toplevel)"
  PLUGIN_SCRIPTS="$(python3 "$MINERVA_PLUGIN_ROOT/scripts/minerva_runtime.py" resolve --skill-file "$MINERVA_SKILL_FILE")" || exit 1
  [ -n "$PLUGIN_SCRIPTS" ] && { python3 "$PLUGIN_SCRIPTS/plugin_guard.py" || exit 1; }
  python3 "$PLUGIN_SCRIPTS/knowledge_catalog.py" "$ROOT/.minerva/knowledge" --themes
  ```

  Coin a new theme only when no existing one fits — a near-duplicate splits a group in
  the catalog, and lint warns about a theme only one entry uses.

```markdown
# <Short, declarative title — what was decided, fixed, or discovered>

**Date**: YYYY-MM-DD
**Type**: decision | bug | pattern | constraint | reference
**Theme**: <existing kebab-case theme — see `knowledge_catalog.py --themes`>
**Summary**: <≤15-word condensation of the Finding — the entry's catalog line>
**Context**: .minerva/work/<date-slug> (see git history if the worktree has been cleaned up)

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
only**: the reverse direction is derived (`knowledge_catalog.py --links-to <stem>`), so
promote never writes a back-link into another entry. To retire an older entry, the new
entry says so — `- [[<old-stem>]] — supersedes` — and the catalog marks the old one
superseded. Nothing is written into the old entry; a supersession banner is a legacy form
the catalog still reads but promote never writes.

## Wiki maintenance (add-only)

**A promote run writes new entry files and nothing else.** No catalog, no edit to any
existing entry, no supersession banner, no `index.md` or `overview.md` (neither exists).

This is the invariant that makes concurrent work units safe. A work-unit branch's
entire `.minerva/` footprint is *newly-added files*, and new files merge cleanly no
matter how many PRs are in flight. There is also nothing left to do after merge: the
catalog, backlinks and supersession are all computed from the entries when they are
read, so the knowledge update ships complete in the unit's own PR.

Do not edit an older entry "while you're here" to add a back-link or a banner. Every
shared or cross-entry write is a surface two concurrent PRs fight over.

### Entry naming

An entry's id is **today's date**, `YYYY-MM-DD`:

```bash
date +%F
```

There is nothing to allocate and nothing to scan. Dates are read off the clock, so two
units promoting concurrently never negotiate for an id, and **several entries sharing a
date is normal, not a collision** — identity is the whole `YYYY-MM-DD-<type>-<slug>`
stem.

This replaced a cross-branch allocator that existed because a *number* is scarce: two
units picking the same NNN produced two different filenames, so git merged both cleanly
and the duplicate shipped silently. Under stem identity that failure cannot happen — two
entries with the same stem are the same path, so git raises an add/add conflict and one
side must resolve it. The guard moved from a script into the filesystem.

Do not add a disambiguating suffix to "avoid" a shared date. If two entries on one day
really do share a type and slug, they are the same entry and want merging, not renaming.

### The maintenance step

For **each** newly-written knowledge entry, before the gate:

1. **Pick the theme.** Run `knowledge_catalog.py --themes` and reuse the theme whose
   existing entries this one belongs beside.
2. **Neighbor discovery (recall-complete floor).** List the catalog
   (`knowledge_catalog.py .minerva/knowledge`) to narrow candidates by theme and summary,
   then read the Findings of the plausible neighbours and identify genuine relationships.
   Dedup candidate hits by target **stem**: a date is shared by design, so deduping on the
   id alone would collapse distinct same-day entries into one.
3. **Write forward links only.** Record each relationship as a `## Related` line
   **in the new entry**: `- [[YYYY-MM-DD-type-slug]] — <relationship>`.

   The label is normally a short sentence saying what the edge *is* — that is what
   makes the wiki navigable. `supersedes` is matched as a term: a label that starts with
   it (optionally followed by `:` and an explanation) retires the target in the derived
   catalog. Use it only when the new entry genuinely replaces the old one.

   Do **not** write anything into the neighbor.
4. **Gate.** Surface the new entry files as concrete diffs in the same confirmation
   gate that approves the promote (Mode A step 6 / Mode B step 4). There are no
   neighbor or catalog diffs to show — if you find yourself with one, something has
   gone wrong.

### Idempotency

Re-running promote is a byte-level no-op on an entry that already exists: the file
name is derived from the date and slug rather than allocated, and a `## Related` line
is added only if no existing line in that block references the target **stem**
(insert-iff-absent, set semantics keyed on the stem — keying on the id would treat two
same-day entries as one and silently drop the second relationship). Promote never edits
any entry other than the one it is currently writing.
