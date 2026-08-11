---
name: migrate-fix
description: Renames legacy `NNN`-prefixed knowledge entries and work units to date ids (`YYYY-MM-DD-type-slug`) — MUTATES `.minerva/knowledge/` and `.minerva/work/` behind a confirmation gate, deriving each date from the git history of the path itself and retargeting every wikilink, supersession marker and `**Context**` path via the tested `scripts/knowledge_rename.py`. Refuses the whole batch before moving anything if two entries would land on one name. Never renames git branches, and never edits an entry's body `**Date**` field. Use when a corpus still carries `NNN-` filenames and the user asks to migrate to date ids, or when they invoke `minerva:migrate-fix`. The read-only companion that tells you whether a corpus needs this is `minerva:migrate`.
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
---

Rename a legacy `NNN`-prefixed corpus to date ids, behind a confirmation gate.
`minerva:migrate-fix` is the **mutating** companion to the read-only `minerva:migrate`:
where `minerva:migrate` reports that a corpus is off-convention, this skill performs the
one rename it can do deterministically. **All mutation happens inside the unit-tested
`scripts/knowledge_rename.py`** — this skill orchestrates and gates; it does not edit
files itself (its `allowed-tools` omits `Edit`/`Write`).

> This skill **changes files**, including `git mv` of ~100 paths in a typical corpus. It
> is not read-only. The full plan is shown and applied only after you confirm.

## Why the ids changed

`NNN` was scarce and globally ordered, so allocating it correctly was a distributed
problem — two branches picking the same number produced two *different* filenames, which
git merged cleanly, shipping a silent duplicate. A date is read off the clock, so nothing
is allocated and nothing coordinates. **Several entries sharing a date is normal**, because
identity is the whole `YYYY-MM-DD-<type>-<slug>` stem — and a duplicate stem is the same
path, which git refuses to merge rather than merging silently.

## Step 1 — Plan (read-only)

Run the planner and show the user what would move:

```bash
ROOT="$(git rev-parse --show-toplevel)"; PLUGIN_SCRIPTS=$(find -L "${HOME}/.claude/plugins/minerva" "${HOME}/.claude/plugins/cache/agent-marketplace/minerva" -maxdepth 2 -type d -name "scripts" 2>/dev/null | head -1); python3 "${PLUGIN_SCRIPTS:-$ROOT/scripts}/knowledge_rename.py"
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
  See [What the date means](#what-the-date-means).

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
python3 "${PLUGIN_SCRIPTS:-$ROOT/scripts}/knowledge_rename.py" --apply
```

Order matters and is handled inside the script: every reference is rewritten **before**
anything moves, so each path in the map still resolves while it is being consulted.

## Step 4 — Verify

Run `minerva:lint`. A migrated corpus should report **zero errors**; pending-reconciliation
warnings are normal and are `minerva:cleanup`'s job. Then confirm no live legacy link
survived:

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

## After upgrading: expect the finding count to RISE

The first `minerva:lint` run after upgrading usually reports **more** findings on an
unchanged corpus, because the `## Related` edge model was unified and the old detector
could not see extra targets on a shared line. The delta is previously-unreportable
findings, not new damage — but any pending finding-count comparison must be re-baselined.
**Read `references/upgrading.md`** before comparing any finding count across the upgrade —
it covers why the old number was wrong rather than the new one, what to do on the first
run, and the post-merge surprise this cost a real team.

## What the date means

The id is the **landing** date — the oldest commit touching that path, following renames.
Under squash-merge that is the day the work shipped; if the repo merges or rebases
instead, it is the original commit date. The imprecision is deliberate and harmless: a
date carries no identity and no ordering weight beyond sort.

Two consequences worth stating so nobody later "fixes" them:

- **An entry's date may differ from its work unit's.** They are derived independently, and
  an entry promoted in a later PR than its proposal legitimately differs. `**Context**`
  paths are rewritten through a lookup map, never by assuming the two agree.
- **A filename date may differ from the entry's own `**Date**:` field.** The filename
  records when the entry *landed*; the body records when it was *authored*. This skill
  never rewrites the body field — doing so would overwrite authored metadata with a
  derived value.

## Out of scope

- **Git branches.** `minerva:cleanup` matches a branch by its literal name and a merged
  PR's head ref is immutable on the forge, so renaming breaks both for no gain — a branch
  name is not corpus content. Legacy branches keep their `NNN-slug` names forever; only new ones
  take the date form.
- **Entry bodies.** Only the `**Context**` path, wikilinks and supersession markers are
  touched. Findings, summaries and `**Date**` fields are left exactly as written.
- **Deciding whether a corpus needs migrating.** That is `minerva:migrate`, which is
  read-only and reports the shape. This skill assumes the decision is already made.
- **Re-running against a migrated corpus.** Already-dated entries AND work directories
  are skipped, so a second run is a no-op rather than a double-rename. Work directories
  were the exception until this was fixed: their pattern matched a bare `NNN` only, so an
  already-migrated `2026-08-07-foo/` read as id `2026` plus slug `08-07-foo` and got
  re-dated to `2026-08-10-08-07-foo/`, with every `**Context**` path retargeted to the
  corrupted name.

## Related

- `minerva:migrate` — the read-only shape check; run it first.
- `minerva:lint` / `minerva:lint-fix` — the ongoing health check and its repairer; run
  `minerva:lint` after this to confirm the corpus is clean.
