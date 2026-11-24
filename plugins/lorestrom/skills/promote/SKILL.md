---
name: promote
description: Finalizes a work unit's record in a repository linked to Lorestrom — promotes durable knowledge to Lorestrom entries pending until the unit merges, rewrites the proposal to match reality, and archives the scratchpad; every forward-looking TODO gets an explicit disposition — a small defect is fixed in this unit, and only an urgent defect too large to absorb is filed as a GitHub issue (the unit's followups record when the repo cannot host issues). Also captures a significant mid-work decision/bug/pattern immediately. Use when implementation is done and the record needs finalizing, when a review has completed and the scratchpad holds unpromoted notes, or when the user invokes `lorestrom:promote`. Idempotent.
---

## Runtime

Read `skills/using-lorestrom/references/runtime.md` before executing; follow its host adapter.

Promote durable items from the scratchpad record to knowledge entries in Lorestrom, and (in the end-of-work pass) reshape the work unit's persistent record to match what shipped.

## The heuristic

> **Artifacts get promoted, not just accumulated.** Apply this to every scratchpad entry: *would a new engineer (or new agent) joining the project in a year benefit from reading this?* Only concrete, past-tense facts qualify — things that happened, were decided, were fixed, or were discovered. If yes, promote. If no, discard (with the TODO escape hatch in Mode A step 4). Scratchpads almost always fail; concrete past-tense facts almost always pass; proposals are between.

## Target resolution

Same pattern used by `lorestrom:work`, `lorestrom:replan`, `lorestrom:review`, `lorestrom:ship`, `lorestrom:cleanup`. **Keep all six blocks in sync if you edit one.**

1. **Explicit argument** — a unit id. Use it only when it equals an id `storage:unit.list` or the runtime's `units` printed (runtime contract, "Names are data"); otherwise stop on it.
2. **Current-session context** — a unit id or branch name mentioned in this session, checked the same way. A branch name may end `-phase-N` (a phased unit's later phases): drop that suffix, then check what remains.
3. **The only open unit** — if `storage:unit.list` shows exactly one of this project's units with an open gate, use it.
4. **Ambiguity** — list the candidates, ask the user.
5. **None found** — report "no work units found — run `lorestrom:propose` first" and stop.

A unit's records live in Lorestrom (`storage:unit.read`), never in files. With no link, no server or no project, a record write stops and names `lorestrom:init`.

`lorestrom:promote "exponential backoff for retries"` (Mode B) — when the first argument matches a scratchpad block, Mode B kicks in on the resolved unit.

## Worktree addressing

After resolving the target and before reading or writing any files:

- `<date-slug>` is a checked id (runtime contract, "Names are data").
- **Do not call `EnterWorktree`** — lorestrom worktrees live under `.lorestrom/worktrees/`, which that tool does not reliably enter; the session's working directory stays the parent repo.
- Code lives in the worktree: prefix every repository file path this skill reads or writes with `.lorestrom/worktrees/<date-slug>/`, and run every git command as `git -C .lorestrom/worktrees/<date-slug> …`. Relative paths resolve to the parent repo and silently misroute edits onto the wrong branch.
- The unit's records (proposal, scratchpad, replan, followups) are Lorestrom docs read and written through `storage:` operations, never files in either tree.

Promote writes no file: entries, the proposal rewrite and the scratchpad archive are Lorestrom writes under the unit's gate (`skills/using-lorestrom/references/storage.md`). Entries are pending lore until the unit's release at cleanup.

## Orchestrated mode (`--auto`)

**Mode argument**: `--auto`

`--auto=<orchestrator>` is an **observable** signal that an autonomous orchestrator has
substituted its own adjudication for this skill's user gates. Act on the argument — never on a
judgment about who is calling. Absent it, every gate behaves exactly as written. **Inert until 0.3.0:**
no lorestrom skill passes it until the orchestrators arrive (runtime contract, "Scope of this version").

It satisfies the Mode A and Mode B hard gates in `references/modes.md`.

## Two modes

The full mode protocols — **Mode A (end-of-work)**, the default full-scratchpad partition, and **Mode B (single-item)**, the mid-work immediate promotion — live verbatim in `references/modes.md`. **Read it before executing either mode.** The knowledge-entry template (including the required `**Theme**` and `**Summary**` fields), the add-only wiki-maintenance protocol, and entry naming live in `references/wiki-maintenance.md`. **Read it before writing any knowledge entry.** **What may be deferred at all — the three-condition bar, its outlets (fix now / tracker issue / `reference` knowledge entry / neither, for documentation), the one-issue-per-unit soft cap, and why the bar exists — lives in `references/deferral-bar.md`. Read it before disposing of any forward-looking item.** It is the single statement of that rule; `lorestrom:review` and the `propose-ship-*` orchestrators (0.3.0) point at the same file rather than restating it. The mechanics of the issue path — the capability probe, the `critical`/`high` priority vocabulary, the required `**Failure scenario**:` body line, label bootstrap, the duplicate check, and the per-item fail-soft to the followups record — live in `references/github-issues.md`. **Read it before filing anything.**

## Idempotency summary

- Mode A re-run: `minerva:promoted` on the unit (`unit-state`) → stops early.
- Mode B re-run on a marked block: existing entry → stops early.
- Promote is **add-only**: it writes new entries under the unit's gate and touches no existing entry's body — not a neighbor's `## Related` block, not a supersession banner. An edge onto an existing entry is a held write, applied only when the unit merges, so concurrent units never fight over a shared doc. The reverse direction of every cross-link, the catalog and supersession are derived from the edges on read. An entry's id is today's date (`date +%F`) — nothing is allocated, and a shared date is normal because identity is the full stem. A duplicate stem is the same key, which Lorestrom refuses rather than overwriting. See [Wiki maintenance](#wiki-maintenance-add-only).

If a user manually edits the scratchpad to remove markers, re-running `lorestrom:promote` could duplicate entries. This is a known footgun; not defended against.

