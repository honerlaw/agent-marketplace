---
name: migrate-fix
description: Migrates a legacy knowledge corpus to the current shape — MUTATES `.minerva/knowledge/` and `.minerva/work/` behind confirmation gates. (1) Renames legacy `NNN`-prefixed entries and work units to date ids (`YYYY-MM-DD-type-slug`), dating each from its own git history and retargeting every wikilink, supersession marker and `**Context**` path via `scripts/knowledge_rename.py`; refuses the whole batch if two entries would land on one name. (2) Backfills the `**Theme**` / `**Summary**` lines the 3.0 catalog reads from a pre-3.0 corpus's legacy `index.md` / `overview.md`, then deletes both, via `scripts/knowledge_backfill.py`. Never renames git branches or edits entry bodies. Use when a corpus still carries `NNN-` filenames or legacy `index.md` / `overview.md`, when upgrading from minerva 2.x, or when the user invokes `minerva:migrate-fix`. The read-only companion is `minerva:migrate`.
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
---

## Runtime

Read `skills/using-minerva/references/runtime.md` before executing; follow its host adapter.

Move a legacy corpus into the current shape, behind confirmation gates.
`minerva:migrate-fix` is the **mutating** companion to the read-only `minerva:migrate`:
where `minerva:migrate` reports that a corpus is off-convention, this skill performs the
two migrations it can do deterministically:

- **Part A — rename** legacy `NNN`-prefixed entries and work units to date ids
  (`scripts/knowledge_rename.py`).
- **Part B — backfill** the `**Theme**` / `**Summary**` metadata a pre-3.0 corpus keeps in
  its legacy `index.md` / `overview.md`, then delete those files
  (`scripts/knowledge_backfill.py`).

**All mutation happens inside the unit-tested helpers** — this skill orchestrates and
gates; it does not edit files directly; always use the helper. Run only the parts
`minerva:migrate` reported a need for. **When both are needed, run Part A first:** the
backfill matches each entry to its legacy catalog line and overview link *by stem*, and
the rename retargets those legacy lines, so renaming first keeps every stem resolvable.
Backfilling first would leave the metadata in place but feed the rename files that no
longer exist.

> This skill **changes files**, including `git mv` of ~100 paths in a typical corpus. It
> is not read-only. Each part's full plan is shown and applied only after you confirm.

## Why the ids changed

`NNN` was scarce and globally ordered, so allocating it correctly was a distributed
problem — two branches picking the same number produced two *different* filenames, which
git merged cleanly, shipping a silent duplicate. A date is read off the clock, so nothing
is allocated and nothing coordinates. **Several entries sharing a date is normal**, because
identity is the whole `YYYY-MM-DD-<type>-<slug>` stem — and a duplicate stem is the same
path, which git refuses to merge rather than merging silently.

## Part A — Rename `NNN` ids to date ids

## Step 1 — Plan (read-only)

Run the planner and show the user what would move:

```bash
ROOT="$(git rev-parse --show-toplevel)"; PLUGIN_SCRIPTS="$(python3 "$MINERVA_PLUGIN_ROOT/scripts/minerva_runtime.py" resolve --skill-file "$MINERVA_SKILL_FILE")" || exit 1; [ -n "$PLUGIN_SCRIPTS" ] && { python3 "$PLUGIN_SCRIPTS/plugin_guard.py" || exit 1; }; python3 "$PLUGIN_SCRIPTS/knowledge_rename.py"
```

It prints every `old -> new` pair and exits without touching anything. Three outcomes
need your attention before you gate:

- **`COLLISION`** — two entries want one name, meaning they share a date, a type *and* a
  slug. They are the same entry: merge them by hand, then re-plan. Do **not** invent a
  disambiguating suffix; that manufactures two records where the corpus has one finding.
- **`UNDATED (skipped)`** — git could not date the path (uncommitted, or no history).
  These are skipped rather than guessed at, because inventing a date mints an id that
  corresponds to nothing. Commit the file first, then re-plan.
- **A date that surprises you** — the id is the *landing* date, not the authored date.
  **Read "What the date means" in `references/upgrading.md`** before trusting a derived date.

## Step 2 — Confirmation gate (REQUIRED)

Show the counts (`N entries, M work dirs`), the collision and undated lists if any, and
ask before proceeding. Never apply on the strength of a clean plan alone — the plan is
also what tells the user whether the dates look right, and only they can judge that.

**Surface the exception lines, not just the totals.** `plan` reports
`ALREADY MIGRATED (skipped) N path(s)`, `INVALID DATE ID (re-dated) <path>` for a
date-shaped id that is not a real date, and the `SHORTHAND` block. Put these in front of
the user at the gate rather than leaving them to be read out of a long plan: on one real
637-entry migration, three corrupted rows sat among 552 correct ones in the dry-run
output and were missed, because `2026-08-10-x -> 2026-08-10-08-10-x` reads as noise at
that length. A plan is a control only when its anomalies are separable at the size the
output actually reaches.

**Offer shorthand resolution here**, since a flag nobody knows about is not a feature.
If bare `[[NNN]]` references were counted, re-run the plan with `--resolve-shorthand` and
report how many are resolvable and how many are refused, with the refusal reasons, then
let the user choose. **Pair the refusals with the `UNDATED` list**: an entry git cannot
date has no target stem, so every `[[NNN]]` pointing at it refuses for that one reason, and
dating it converts a block of refusals into resolutions at once. Printed apart, they read as
two unrelated warnings. Resolution is opt-in and refuses anything not provably unambiguous, including
*everything* on a partially-migrated corpus, where the collision it guards against has
already become undetectable.

## Step 3 — Apply

```bash
python3 "$PLUGIN_SCRIPTS/knowledge_rename.py" --apply
```

Order matters and is handled inside the script: every reference is rewritten **before**
anything moves, so each path in the map still resolves while it is being consulted.

## Step 4 — Verify the rename

Confirm no live legacy link survived:

```bash
grep -rE '\[\[[0-9]{3,}-' --include='*.md' . \
  | grep -vE '\[\[[0-9]{4}-[0-9]{2}-[0-9]{2}-' | grep -v '.minerva/worktrees'
```

The second `grep -v` is what makes this check mean anything. A bare `[[0-9]{3,}-` also
matches the `2026` of every correctly-migrated `[[2026-05-19-…]]` link, so the pattern
that looks like it finds leftovers actually matches the whole corpus — 6,005 hits against
26 real ones, on the corpus where this was caught. Excluding the date shape is what
leaves only genuine legacy ids. The `{3,}` stays as it was: that is the legacy id's own
width (`ID_RE_SRC`), and loosening it to `+` would start reporting any bracketed number.

Remaining hits should only ever be inside fenced examples, or prose in an entry recounting
an old number. Both are correct: the migration is fence-aware by design.

## Part B — Backfill entry metadata from the legacy aggregates

A pre-3.0 corpus keeps its catalog in `index.md` and its theme grouping in `overview.md`.
Part B moves both onto the entries as `**Summary**` / `**Theme**` lines with
`scripts/knowledge_backfill.py` — dry run, confirmation gate, apply, verify — and deletes the
two files. Run Part A first when both are needed: the backfill matches entries by stem. The
full protocol (Steps 5–8) lives in `references/backfill.md`. **Read it before backfilling.**

## Out of scope

- **Git branches.** `minerva:cleanup` matches a branch by its literal name and a merged
  PR's head ref is immutable on the forge, so renaming breaks both for no gain — a branch
  name is not corpus content. Legacy branches keep their `NNN-slug` names forever; only new ones
  take the date form.
- **Entry bodies.** Only the `**Context**` path, wikilinks and supersession markers (Part A)
  and the inserted `**Theme**` / `**Summary**` lines (Part B) are touched. Findings, summaries and `**Date**` fields are left exactly as written.
- **Deciding whether a corpus needs migrating.** That is `minerva:migrate`, which is
  read-only and reports the shape. This skill assumes the decision is already made.
- **Re-running against a migrated corpus.** The backfill is a no-op without legacy files.
  Already-dated entries AND work directories
  are skipped, so a second run is a no-op rather than a double-rename. Work directories
  were the exception until this was fixed: their pattern matched a bare `NNN` only, so an
  already-migrated `2026-08-07-foo/` read as id `2026` plus slug `08-07-foo` and got
  re-dated to `2026-08-10-08-07-foo/`, with every `**Context**` path retargeted to the
  corrupted name.

## Related

- `minerva:migrate` — the read-only shape check; run it first.
- `minerva:lint` — the ongoing health check; run it after this to confirm the corpus is
  clean.
- `minerva:init` — refreshes a stale `## minerva` routing section after the backfill.
