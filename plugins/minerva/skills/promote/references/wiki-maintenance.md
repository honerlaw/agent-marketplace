# promote — knowledge-entry template + wiki maintenance

## Knowledge entry template

The `**Context**` field is a stable pointer that should remain meaningful even after the work-unit worktree is removed (`minerva:cleanup`). Use the canonical `.minerva/work/NNN-<slug>` path even if the actual files currently live in a worktree — after merge + cleanup, the docs are reconstructible from git history at that path on the merge commit.

```markdown
# <Short, declarative title — what was decided, fixed, or discovered>

**Date**: YYYY-MM-DD
**Type**: decision | bug | pattern | constraint
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

The `## Related` block is the canonical, machine-managed cross-reference surface —
see [Wiki maintenance](#wiki-maintenance-index--cross-references) below. Omit it
from a fresh entry that has no neighbors; the wiki-maintenance step adds it when a
relationship is confirmed. A superseded entry additionally carries a banner placed
between its metadata block and the first `## ` header:

```markdown
<!-- superseded-by: NNN -->
> **Superseded by [[NNN-type-slug]]** (YYYY-MM-DD)
```

## Wiki maintenance (index + cross-references)

Every promote that writes a new knowledge entry also maintains the wiki's
navigability layer: the `.minerva/knowledge/index.md` catalog and the
cross-references between entries. This runs **inside promote's existing gate** — no
new gate is introduced — and writes to neighbors / index **only on approval**.

### The canonical `index.md` skeleton

`minerva:init` and `minerva:promote` are the two creators of `index.md`; both emit
this **exact** skeleton so they cannot diverge:

```markdown
# Knowledge index
<!-- index-watermark: NNN -->

## Decisions

## Bugs

## Patterns

## Constraints
```

- The watermark `NNN` is the highest entry number the index reflects (`000` when
  empty). It is a **content** freshness signal, used in preference to file mtime
  (mtime is unreliable across git checkouts and worktrees).
- Catalog lines go under the matching Type section, one per entry:
  `- [[NNN-type-slug]] — <≤15-word summary>` (title from the entry H1, summary
  condensed from its Finding). Sections are plural buckets; links use the singular
  filename stem.

### The maintenance step

For **each** newly-written knowledge entry, before the gate:

1. **Neighbor discovery (recall-complete floor).** Read the titles + Findings of
   the existing `.minerva/knowledge/NNN-*.md` entries directly (a full corpus scan —
   cheap at this scale) and identify genuine relationships. You MAY read
   `index.md`'s one-line summaries first as a pre-filter, but **only** when it is
   present AND fresh (its `index-watermark` ≥ the max NNN on disk). A stale or
   absent index never blocks discovery — fall back to the full scan and recompute.
   Dedup candidate hits by target NNN (an entry referenced both inline in prose and
   in a `## Related` block collapses to one).
2. **Propose the edits**, classifying each relationship with the closed vocabulary
   `builds on` / `supersedes` / `superseded by` / `contradicts` / `see also`:
   - a `## Related` line in the new entry: `- [[NNN-type-slug]] — <relationship>`;
   - the **reciprocal** line in the neighbor entry (e.g. new→`supersedes`old pairs
     with old→`superseded by`new);
   - a `<!-- superseded-by: NNN -->` banner in any entry the new one supersedes.
   Present each reciprocal pair as a **single coupled approval unit** — never let
   one direction be approved while its reciprocal is dropped.
3. **Propose the `index.md` line(s)**: the new entry's catalog line, the watermark
   bump, and any line edits for superseded entries. If `index.md` is absent, create
   it from the canonical skeleton with just the new entry (and point the user at
   `minerva:init`'s backfill for the rest).
4. **Gate.** Surface all proposed neighbor + index edits as **concrete diffs** in
   the same confirmation gate that approves the promote (Mode A step 6 / Mode B
   step 4). Use the `Edit` tool to apply them only after approval (Mode A step 7 /
   Mode B step 5).

### Idempotency of wiki edits

- A `## Related` line is added only if no existing line in that block references the
  target NNN (insert-iff-absent, set semantics keyed on NNN).
- A supersession banner is added only if no `<!-- superseded-by: NNN -->` marker for
  that superseding NNN is already present.
- An index line is added only if no line for that NNN exists; the watermark bumps
  **only** when an index line is actually added or changed.

Re-running promote in either mode is therefore a **byte-level no-op** on
already-present links, banners, and index lines — and never edits an entry body
outside the `## Related` block or the banner span.
