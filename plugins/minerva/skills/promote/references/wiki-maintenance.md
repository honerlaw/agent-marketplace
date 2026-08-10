# promote — knowledge-entry template + wiki maintenance

## Knowledge entry template

The `**Context**` field is a stable pointer that should remain meaningful even after the work-unit worktree is removed (`minerva:cleanup`). Use the canonical `.minerva/work/<date-slug>` path even if the actual files currently live in a worktree — after merge + cleanup, the docs are reconstructible from git history at that path on the merge commit.

The `**Summary**` field is **required**. It is the entry's own catalog line — the ≤15-word condensation of its Finding that `index.md` will carry. Because the entry states it, the main-side reconciliation can catalogue the entry mechanically instead of needing an LLM to re-read and re-condense the Finding. Write it in the same voice as a catalog line: declarative, specific, no leading article.

```markdown
# <Short, declarative title — what was decided, fixed, or discovered>

**Date**: YYYY-MM-DD
**Type**: decision | bug | pattern | constraint | reference
**Summary**: <≤15-word condensation of the Finding — becomes the index catalog line>
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

The `## Related` block is the canonical cross-reference surface. Omit it from a fresh
entry that has no neighbors. A superseded entry additionally carries a banner placed
between its metadata block and the first `## ` header — but promote **never writes
that banner itself** (see below); reconciliation derives it:

```markdown
<!-- superseded-by: <superseding-stem> -->
> **Superseded by [[YYYY-MM-DD-type-slug]]** (YYYY-MM-DD)
```

## Wiki maintenance (add-only)

**A promote run writes new entry files and nothing else.** No `index.md` catalog
line, no watermark bump, no edit to any neighbor entry, no supersession banner.

This is the invariant that makes concurrent work units safe. A work-unit branch's
entire `.minerva/` footprint becomes *newly-added files*, and new files merge cleanly
no matter how many PRs are in flight. Every shared surface — `index.md`,
`overview.md`, and the reverse direction of every cross-link — is written on the
default branch instead, by the reconciliation step in `minerva:cleanup`, where there
is exactly one writer at a time.

Do not "just add the index line while you're here." That single line is the file that
appeared in 78% of commits and conflicted on every concurrent pair.

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

1. **Neighbor discovery (recall-complete floor).** Read the titles + Findings of
   the existing `.minerva/knowledge/*.md` entries directly (a full corpus scan)
   and identify genuine relationships. You MAY read `index.md`'s one-line summaries
   first as a pre-filter, but **only** to narrow what you read — never as the sole
   source, since the index legitimately lags the corpus and a pending entry has no
   line at all. A stale or absent index never blocks discovery — fall back to the full
   scan. Dedup candidate hits by target **stem**: a date is shared by design, so
   deduping on the id alone would collapse distinct same-day entries into one.
2. **Write forward links only.** Record each relationship as a `## Related` line
   **in the new entry**: `- [[YYYY-MM-DD-type-slug]] — <relationship>`.

   The label is normally a short sentence saying what the edge *is* — that is what
   makes the wiki navigable, and it is what the corpora actually contain. Four labels
   are reserved and matched exactly, because their reciprocal is a claim rather than a
   pointer: `supersedes` / `superseded by` / `contradicts` / `builds on`. Any other
   label reciprocates as `see also`. A label that merely *mentions* superseding or
   contradicting without being the exact term is refused — write that reciprocal by
   hand rather than letting the fixer guess the direction of a retirement.

   Do **not** write the reciprocal line into the neighbor, and do **not** write a
   supersession banner. Both are derived on the default branch by
   `knowledge_fix.plan_reciprocals`, which already turns a `supersedes` forward edge
   into the neighbor's banner *and* its `superseded by` line. Editing the neighbor
   here is the second-most-common conflict source after the index, and it is
   redundant with a step that runs anyway.
3. **Gate.** Surface the new entry files as concrete diffs in the same confirmation
   gate that approves the promote (Mode A step 6 / Mode B step 4). There are no
   neighbor or index diffs to show — if you find yourself with one, something has
   gone wrong.

### What reconciliation does with this later

`minerva:cleanup` runs `knowledge_fix.py` on the default branch after the PR merges.
It adds each entry's catalog line from its `**Summary**`, bumps the watermark to the
new max, writes every missing reciprocal and banner, and opens a single PR. Until
then the entries sit above the watermark and `knowledge_lint` reports them as
`pending reconciliation` **warnings**, so the branch's CI drift gate stays green.

The canonical `index.md` skeleton lives with its sole creator, `minerva:init`.
Promote no longer creates `index.md` — if it is missing, that is an `minerva:init`
gap and both the linter and the fixer say so.

### Idempotency

Re-running promote is a byte-level no-op on an entry that already exists: the file
name is derived from the date and slug rather than allocated, and a `## Related` line
is added only if no existing line in that block references the target **stem**
(insert-iff-absent, set semantics keyed on the stem — keying on the id would treat two
same-day entries as one and silently drop the second relationship). Promote never edits an entry body outside the `## Related`
block of the entry it is currently writing.
