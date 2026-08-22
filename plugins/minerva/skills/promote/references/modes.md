# promote — the two mode protocols

## Two modes

### Mode A — no argument (end-of-work full pass)

1. Read `proposal.md`, `scratchpad.md`, and `replan.md` (if present).
2. **Idempotency check:** decide via the importable predicate, never by matching the marker string:

   ```bash
   python3 -c "import sys; sys.path.insert(0, '<scripts>'); from work_status import unit_state; print(unit_state('.minerva/work/<date-slug>')['promoted'])"
   ```

   If it prints `True`, report "already promoted" and stop. **Do not** re-implement this as a string comparison against the marker below. That is what the check used to do, and the marker has eight spellings across one corpus (`/promote` before the skill rename, `promoted <date> — durable knowledge in …`, a bare `<!-- post-promote -->`, an appended `## Promote` section, a `> **PROMOTED …**` blockquote). Matching one spelling made the check fail **open** on 16 of 51 units — promote would re-run a mutating pass and can duplicate `.minerva/knowledge/` entries. Reported as a bug in May 2026 and left unapplied while the affected set grew from 3 units to 16.
3. Propose a three-way partition of the scratchpad entries:
   - **PROMOTE** → concrete, past-tense knowledge: architectural/design choices made, bugs fixed (if the fix is non-obvious or the root cause could recur), discovered failure patterns, surprising constraints, gotchas a future reader needs.
   - **MERGE INTO PROPOSAL** → places where the actual approach diverged from the original; the proposal's `## Approach` must end up describing what got built. Entries under a `## Review finding YYYY-MM-DD` header from `minerva:review` go through this lens by default — review findings are about the implementation, not durable knowledge, unless they reveal a pattern/constraint worth capturing.
   - **DISCARD** → dead ends, momentary confusion, debugging digressions, choices that don't matter.
   - **TODO** → forward-looking notes ("we should do X later", "investigate Y", "consider Z"). These are surfaced separately at step 5 so they don't vanish silently.
   Skip entries already marked `→ promoted to .minerva/knowledge/...` — they were promoted mid-work.
4. Present the partition as a numbered list with each entry's classification and a one-line justification. Wait for confirmation or edits.
5. **TODO disposition gate.** If any entries landed in the TODO bucket, run the capability probe in [references/github-issues.md](github-issues.md) step 1 — **read that file now if any item may be kept** — then surface the items and ask:
   > "These forward-looking items don't belong in `.minerva/knowledge/` but I don't want to drop them silently. For each one: keep it (I'll file it as a GitHub issue on `<nameWithOwner>` at the priority shown / I'll add it to `followups.md`), seed a new `minerva:propose`, or discard?"

   - **Keep** → **issue path** when the probe says the repo has issues we can create: one issue per item, carrying a proposed priority (`critical` / `high` / `medium` / `low`), the `minerva:followup` marker label, and a back-link to this unit. **File path** otherwise — no `gh`, not authenticated, no GitHub remote, issues disabled, or creation fails for that item: append to `.minerva/work/<target>/followups.md` (create the file if missing) under a `## YYYY-MM-DD` header, one bullet per item. Both paths are specified in full in [references/github-issues.md](github-issues.md); the priority is a **proposal** that this gate and step 6 exist to correct.
   - **Seed new proposal** → after Mode A finishes, offer to invoke `minerva:propose "<the todo>"` for each chosen item. These never become issues — a proposal is the richer record.
   - **Discard** → drop, no record.

   Deferred work stays discoverable through whichever path it took: `minerva:review` and the `propose-ship-*` orchestrators read `followups.md` **and** open `minerva:followup` issues. Plain `minerva:propose` reads neither — do not claim otherwise.
6. **Hard gate:** do not write files until the user — or, when invoked by an autonomous orchestrator, its adjudication mechanism — has confirmed the partition, the TODO dispositions, **and the new entry files** (each shown as a concrete diff, including its `**Summary**` and its forward `## Related` lines). There are no neighbor or `index.md` diffs to confirm — promote is add-only (see [Wiki maintenance](#wiki-maintenance-add-only)).
7. On confirmation:
   - **For each PROMOTE item:** determine its type (`decision`, `bug`, `pattern`, `constraint`, or `reference`) and write `.minerva/knowledge/<YYYY-MM-DD>-<type>-<slug>.md` using the knowledge entry template below, where the date is today (`date +%F`) — see [Entry naming](#entry-naming). If `.minerva/knowledge/` doesn't exist, create it. Each entry must stand alone.
   - **Run [Wiki maintenance](#wiki-maintenance-add-only) for each PROMOTE item:** write the forward `## Related` lines **into the new entry only**. Do not touch `index.md`, the watermark, any neighbor entry, or any supersession banner — the main-side reconciliation in `minerva:cleanup` derives all of those.
   - **Rewrite `proposal.md`:** the `## Approach` section (and any other section that's out of date) describes reality, not the original plan. Don't preserve obsolete planning prose just because it was there. Update the `**Status**:` field to `Shipped (YYYY-MM-DD)` — that inline field, not a `## Status` heading; 52 of 53 units use it and it is what this skill's own output produces.
   - **Author the `**Closes**` field** if this unit's diff resolves any open issues — `**Closes**: #12, #34`, directly under `**Status**:`. `minerva:ship` reads it when composing the PR body and emits one `Closes #N` line per entry, so GitHub closes them on merge; nothing else closes a `minerva:followup` issue. List only what the diff genuinely resolves: this is the one place the linkage is decided, it is authored rather than inferred, and a wrong auto-close destroys a real record where a stale-open issue merely lingers. Omit the field when nothing is closed.
   - **Apply TODO dispositions** per step 5. On the issue path, run [references/github-issues.md](github-issues.md) steps 3-6: ensure labels, skip items already filed, create one issue per kept item, drop any failed item to `followups.md`, and record the created issues in `proposal.md` under `## Deferred work`. Creating an issue is the only externally-visible side effect promote has — the duplicate check is what keeps a re-run after a partial failure from filing the same item twice.
   - **Archive the scratchpad:** create `.minerva/work/<target>/archive/` if needed, move `scratchpad.md` to `archive/scratchpad.md`, then write a new `scratchpad.md` containing exactly:
     ```
     Summarized at minerva:promote on YYYY-MM-DD — see archive/.
     ```
8. Report: items promoted (with paths), proposal-update summary, TODOs handled, scratchpad disposition. For each kept TODO name where it landed — the issue URL, `already filed as #N`, or `fell back to followups.md` with the reason (including a label that could not be created). A report that omits a skipped item lies by omission. If any TODOs were marked "seed new proposal," prompt the user to invoke `minerva:propose` now or later.

### Mode B — with argument (single-item mid-work promote)

`minerva:promote "empty queue causes null pointer in the retry handler"`

1. Read `scratchpad.md`.
2. Locate the block matching the argument (substring or fuzzy match on the entry text). If multiple candidates, list them and ask which.
3. **Idempotency check:** if the matched block already has a `→ promoted to .minerva/knowledge/...` trailing line, report the existing file path and stop.
4. Confirm with the user that you've identified the right block and show the proposed knowledge entry as a concrete diff — including its `**Summary**` and its forward `## Related` lines. As in Mode A there are no neighbor or `index.md` diffs: promote is add-only (see [Wiki maintenance](#wiki-maintenance-add-only)). Wait for approval.
5. On approval:
   - Determine the type (`decision`, `bug`, `pattern`, `constraint`, or `reference`) and name the file `<YYYY-MM-DD>-<type>-<slug>.md` with today's date — see [Entry naming](#entry-naming). Nothing is allocated; a shared date is normal, and a duplicate stem conflicts in git rather than merging silently.
   - Write `.minerva/knowledge/<YYYY-MM-DD>-<type>-<slug>.md` using the knowledge entry template.
   - **Run [Wiki maintenance](#wiki-maintenance-add-only)** scoped to this single entry: forward `## Related` lines in the new entry only. No index line, no watermark bump, no neighbor edit, no banner. (Idempotency makes a later Mode A full pass a no-op over this entry.)
   - In `scratchpad.md`, append `→ promoted to .minerva/knowledge/<YYYY-MM-DD>-<type>-<slug>.md` to the matched block so the end-of-work pass won't re-promote it.
6. Report the knowledge file path.

