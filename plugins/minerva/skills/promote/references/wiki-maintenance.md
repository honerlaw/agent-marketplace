# promote — knowledge-entry template + wiki maintenance

## Knowledge entry template

The `**Context**` field is a stable pointer that should remain meaningful even after the work-unit worktree is removed (`minerva:cleanup`). Use the canonical `.minerva/work/NNN-<slug>` path even if the actual files currently live in a worktree — after merge + cleanup, the docs are reconstructible from git history at that path on the merge commit.

The `**Summary**` field is **required**. It is the entry's own catalog line — the ≤15-word condensation of its Finding that `index.md` will carry. Because the entry states it, the main-side reconciliation can catalogue the entry mechanically instead of needing an LLM to re-read and re-condense the Finding. Write it in the same voice as a catalog line: declarative, specific, no leading article.

```markdown
# <Short, declarative title — what was decided, fixed, or discovered>

**Date**: YYYY-MM-DD
**Type**: decision | bug | pattern | constraint | reference
**Summary**: <≤15-word condensation of the Finding — becomes the index catalog line>
**Context**: .minerva/work/NNN-<slug> (see git history if the worktree has been cleaned up)

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
- [[NNN-type-slug]] — <relationship>
```

The `## Related` block is the canonical cross-reference surface. Omit it from a fresh
entry that has no neighbors. A superseded entry additionally carries a banner placed
between its metadata block and the first `## ` header — but promote **never writes
that banner itself** (see below); reconciliation derives it:

```markdown
<!-- superseded-by: NNN -->
> **Superseded by [[NNN-type-slug]]** (YYYY-MM-DD)
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

### Entry numbering

Allocate NNN with the tested allocator, never by eyeballing the directory:

```bash
ROOT="$(git rev-parse --show-toplevel)"; PLUGIN_SCRIPTS=$(find -L "${HOME}/.claude/plugins/minerva" "${HOME}/.claude/plugins/cache/agent-marketplace/minerva" -maxdepth 2 -type d -name "scripts" 2>/dev/null | head -1); python3 "${PLUGIN_SCRIPTS:-$ROOT/scripts}/knowledge_next_nnn.py" "$ROOT/.minerva/knowledge" --fetch
```

A plain `max+1` over the local directory is **wrong** here: entries on other in-flight
branches are invisible to it, so two units allocate the same number, and since each
entry is a new file git merges both without a conflict. The allocator unions the
working tree with every entry ever added across all refs. `--fetch` refreshes remotes
first so a branch pushed from elsewhere is counted (best-effort — offline is fine).

### The maintenance step

For **each** newly-written knowledge entry, before the gate:

1. **Neighbor discovery (recall-complete floor).** Read the titles + Findings of
   the existing `.minerva/knowledge/NNN-*.md` entries directly (a full corpus scan)
   and identify genuine relationships. You MAY read `index.md`'s one-line summaries
   first as a pre-filter, but **only** when it is present AND its `index-watermark` ≥
   the max NNN among entries *this run did not write*. (The watermark legitimately
   lags the corpus now, so comparing it against the raw max would reject a perfectly
   usable index on every run.) A stale or absent index never blocks discovery — fall
   back to the full scan. Dedup candidate hits by target NNN.
2. **Write forward links only.** Record each relationship as a `## Related` line
   **in the new entry**: `- [[NNN-type-slug]] — <relationship>`.

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

Re-running promote is a byte-level no-op on an entry that already exists: the
allocator never reissues a number, and a `## Related` line is added only if no
existing line in that block references the target NNN (insert-iff-absent, set
semantics keyed on NNN). Promote never edits an entry body outside the `## Related`
block of the entry it is currently writing.
