# promote — the two mode protocols (verbatim from SKILL.md, work unit 035)

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

