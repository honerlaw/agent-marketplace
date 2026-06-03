---
name: promote
description: Use when the user invokes `minerva:promote`, implementation on a work unit is done and they want to finalize the record, or a significant mid-work decision/bug/pattern should be captured immediately. Promotes durable knowledge to .minerva/knowledge/, rewrites proposal.md to match reality, and archives the scratchpad. Forward-looking TODOs aren't silently discarded — the user is offered to keep them as followups.md or seed a new proposal. Idempotent.
---

Promote durable items from `scratchpad.md` to `.minerva/knowledge/`, and (in the end-of-work pass) reshape the work unit's persistent record to match what shipped.

## The heuristic

> **Artifacts get promoted, not just accumulated.** Apply this to every scratchpad entry: *would a new engineer (or new agent) joining the project in a year benefit from reading this?* Only concrete, past-tense facts qualify — things that happened, were decided, were fixed, or were discovered. If yes, promote. If no, discard (with the TODO escape hatch in Mode A step 4). Scratchpads almost always fail; concrete past-tense facts almost always pass; proposals are between.

## Target resolution

Same pattern used by `minerva:work`, `minerva:replan`, `minerva:review`, `minerva:ship`, `minerva:cleanup`. **Keep all six blocks in sync if you edit one.**

1. **Explicit argument** — slug or path. Look in both `.minerva/work/<NNN-slug>/` and `.minerva/worktrees/<NNN-slug>/.minerva/work/<NNN-slug>/`.
2. **Current-session context** — explicit mention in this session.
3. **Most-recently-modified across both locations** — scan `.minerva/work/NNN-*/` AND `.minerva/worktrees/NNN-*/.minerva/work/NNN-*/` by directory mtime.
4. **Ambiguity** → list candidates, ask.
5. **None found** → report and stop.

`minerva:promote "exponential backoff for retries"` (Mode B) — when the first argument matches a scratchpad block, Mode B kicks in on the resolved unit.

## Worktree entry

After resolving the target and before reading or writing any files:

- If the resolved target's docs live at `.minerva/worktrees/<NNN-slug>/.minerva/work/<NNN-slug>/` and the current session is **not** already in that worktree, call `EnterWorktree` with `path: ".minerva/worktrees/<NNN-slug>"`.
- If the docs live only on the default branch (a shipped unit being promoted retrospectively), operate on the parent repo without entering a worktree.
- If the session is already in the matching worktree, do nothing.

Knowledge files written by promote (`.minerva/knowledge/NNN-<type>-<slug>.md`) land inside the worktree when one is active, so they're committed on the work-unit branch and merged into the default branch via the PR.

## Two modes

### Mode A — no argument (end-of-work full pass)

1. Read `proposal.md`, `scratchpad.md`, and `replan.md` (if present).
2. **Idempotency check:** if `scratchpad.md` is the one-line `Summarized at minerva:promote on YYYY-MM-DD — see archive/.` marker, report "already promoted" and stop.
3. Propose a three-way partition of the scratchpad entries:
   - **PROMOTE** → concrete, past-tense knowledge: architectural/design choices made, bugs fixed (if the fix is non-obvious or the root cause could recur), discovered failure patterns, surprising constraints, gotchas a future reader needs.
   - **MERGE INTO PROPOSAL** → places where the actual approach diverged from the original; the proposal's `## Approach` must end up describing what got built. Entries under a `## Review finding YYYY-MM-DD` header from `minerva:review` go through this lens by default — review findings are about the implementation, not durable knowledge, unless they reveal a pattern/constraint worth capturing.
   - **DISCARD** → dead ends, momentary confusion, debugging digressions, choices that don't matter.
   - **TODO** → forward-looking notes ("we should do X later", "investigate Y", "consider Z"). These are surfaced separately at step 5 so they don't vanish silently.
   Skip entries already marked `→ promoted to .minerva/knowledge/...` — they were promoted mid-work.
4. Present the partition as a numbered list with each entry's classification and a one-line justification. Wait for confirmation or edits.
5. **TODO disposition gate.** If any entries landed in the TODO bucket, surface them and ask:
   > "These forward-looking items don't belong in `.minerva/knowledge/` but I don't want to drop them silently. For each one: keep in `followups.md` for this work unit, seed a new `minerva:propose`, or discard?"

   - **Keep** → append to `.minerva/work/<target>/followups.md` (create the file if missing) under a `## YYYY-MM-DD` header, one bullet per item. `minerva:propose` scans this file as part of project context.
   - **Seed new proposal** → after Mode A finishes, offer to invoke `minerva:propose "<the todo>"` for each chosen item.
   - **Discard** → drop, no record.
6. **Hard gate:** do not write files until the user has confirmed the partition, the TODO dispositions, **and the wiki-maintenance edits** (the proposed `## Related` cross-links, supersession banners, and `index.md` lines from [Wiki maintenance](#wiki-maintenance-index--cross-references), shown as concrete diffs against each affected neighbor and the index).
7. On confirmation:
   - **For each PROMOTE item:** determine its type (`decision`, `bug`, `pattern`, or `constraint`) and write `.minerva/knowledge/NNN-<type>-<slug>.md` using the knowledge entry template below. Auto-increment NNN across the whole `.minerva/knowledge/` directory (3-digit pad). If `.minerva/knowledge/` doesn't exist, create it and start at `001`. Each entry must stand alone.
   - **Run [Wiki maintenance](#wiki-maintenance-index--cross-references) for each PROMOTE item:** apply the approved `## Related` cross-links (bidirectional), any supersession banners, and the `index.md` line(s) + watermark bump. Edit neighbor entries only within their `## Related` block / banner span (never their body).
   - **Rewrite `proposal.md`:** the `## Approach` section (and any other section that's out of date) describes reality, not the original plan. Don't preserve obsolete planning prose just because it was there. Update `## Status` to `Shipped (YYYY-MM-DD)`.
   - **Apply TODO dispositions** per step 5.
   - **Archive the scratchpad:** create `.minerva/work/<target>/archive/` if needed, move `scratchpad.md` to `archive/scratchpad.md`, then write a new `scratchpad.md` containing exactly:
     ```
     Summarized at minerva:promote on YYYY-MM-DD — see archive/.
     ```
8. Report: items promoted (with paths), proposal-update summary, TODOs handled, scratchpad disposition. If any TODOs were marked "seed new proposal," prompt the user to invoke `minerva:propose` now or later.

### Mode B — with argument (single-item mid-work promote)

`minerva:promote "empty queue causes null pointer in the retry handler"`

1. Read `scratchpad.md`.
2. Locate the block matching the argument (substring or fuzzy match on the entry text). If multiple candidates, list them and ask which.
3. **Idempotency check:** if the matched block already has a `→ promoted to .minerva/knowledge/...` trailing line, report the existing file path and stop.
4. Confirm with the user that you've identified the right block and show the proposed knowledge entry **plus the wiki-maintenance edits for this single entry** — its `## Related` cross-links (bidirectional), any supersession banner, and its `index.md` line + watermark bump, shown as concrete diffs (see [Wiki maintenance](#wiki-maintenance-index--cross-references)). Wait for approval.
5. On approval:
   - Determine the type (`decision`, `bug`, `pattern`, or `constraint`) and the next NNN under `.minerva/knowledge/` (max+1, 3-digit pad; start at `001` if dir is missing).
   - Write `.minerva/knowledge/NNN-<type>-<slug>.md` using the knowledge entry template.
   - **Run [Wiki maintenance](#wiki-maintenance-index--cross-references)** scoped to this single entry: apply the approved cross-links, banner, and index line + watermark bump. Edit neighbor entries only within their `## Related` block / banner span. (Idempotency makes a later Mode A full pass a no-op over this entry.)
   - In `scratchpad.md`, append `→ promoted to .minerva/knowledge/NNN-<type>-<slug>.md` to the matched block so the end-of-work pass won't re-promote it.
6. Report the knowledge file path.

## Idempotency summary

- Mode A re-run: scratchpad marker → stops early.
- Mode B re-run on a marked block: existing knowledge file → stops early.
- Knowledge files are **append-only in their body** — auto-incremented NNN guarantees each new entry is unique, and the body of an existing entry (its `# H1`/metadata block and the `## Context` / `## Finding` / `## Implications` sections) is **never rewritten**. The *only* machine-managed mutable surfaces are the delimited `## Related` block and the supersession-banner span — both edited idempotently by the [Wiki maintenance](#wiki-maintenance-index--cross-references) step. This narrowed invariant is what makes bidirectional cross-references safe: promoting a new entry can add a backlink to an older one without ever touching that older entry's recorded finding.

If a user manually edits the scratchpad to remove markers, re-running `minerva:promote` could duplicate entries. This is a known footgun; not defended against.

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
